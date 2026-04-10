from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.db.yaml_store import store
from app.models.contract import (
    CancelRequest,
    Contract,
    ContractCreate,
    ContractRead,
    ContractStatus,
    ContractUpdate,
    compute_status,
)
from app.models.customer import Customer
from app.models.plan import Plan, current_price

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads" / "contracts"

router = APIRouter()


def _enrich(contract: Contract) -> dict:
    today = date.today()
    status = compute_status(contract.start_date, contract.end_date, today)

    customer_d = store.get_by_id("customers", contract.customer_id)
    customer_name = (
        f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt"
    )

    plan_d = store.get_by_id("plans", contract.plan_id)
    plan_name = plan_d["name"] if plan_d else "Unbekannt"
    price: float | None = None
    if plan_d:
        plan = Plan(**plan_d)
        p = current_price(plan, today)
        price = float(p) if p is not None else None

    data = contract.model_dump(mode="json")
    data["status"] = status.value
    data["customer_name"] = customer_name
    data["plan_name"] = plan_name
    data["current_price"] = price
    return data


@router.get("")
def list_contracts(status: ContractStatus | None = None):
    contracts = [Contract(**d) for d in store.load("contracts")]
    enriched = [_enrich(c) for c in contracts]
    if status:
        enriched = [c for c in enriched if c["status"] == status.value]
    return enriched


@router.get("/{contract_id}")
def get_contract(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    return _enrich(Contract(**d))


@router.post("", status_code=201)
def create_contract(body: ContractCreate):
    if not store.get_by_id("customers", body.customer_id):
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    if not store.get_by_id("plans", body.plan_id):
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    data = body.model_dump(mode="json")
    record = store.create("contracts", data)
    return _enrich(Contract(**record))


@router.put("/{contract_id}")
def update_contract(contract_id: int, body: ContractUpdate):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    if not store.get_by_id("customers", body.customer_id):
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    if not store.get_by_id("plans", body.plan_id):
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    updated = store.update("contracts", contract_id, body.model_dump(mode="json"))
    return _enrich(Contract(**updated))


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    invoices = store.load("invoices")
    if any(inv.get("contract_id") == contract_id for inv in invoices):
        raise HTTPException(status_code=409, detail="Vertrag hat noch Rechnungen")
    store.delete("contracts", contract_id)


@router.post("/{contract_id}/scan")
async def upload_scan(contract_id: int, file: UploadFile):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Nur PDF-Dateien erlaubt")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{contract_id}.pdf"
    content = await file.read()
    dest.write_bytes(content)
    updated = store.update("contracts", contract_id, {"scan_file": str(dest)})
    return _enrich(Contract(**updated))


@router.get("/{contract_id}/cancellation-pdf")
def download_cancellation_pdf(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    contract = Contract(**d)
    if not contract.cancellation_pdf or not Path(contract.cancellation_pdf).exists():
        raise HTTPException(status_code=404, detail="Kein Kündigungsdokument vorhanden")
    return FileResponse(
        contract.cancellation_pdf,
        media_type="application/pdf",
        filename=f"kuendigung-{contract_id}.pdf",
    )


@router.get("/{contract_id}/scan")
def download_scan(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    contract = Contract(**d)
    if not contract.scan_file or not Path(contract.scan_file).exists():
        raise HTTPException(status_code=404, detail="Kein Scan vorhanden")
    return FileResponse(
        contract.scan_file,
        media_type="application/pdf",
        filename=f"vertrag-{contract_id}.pdf",
    )


@router.post("/{contract_id}/cancel")
def cancel_contract(contract_id: int, body: CancelRequest):
    from app.services.cancellation import generate_cancellation

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    updated = store.update("contracts", contract_id, {"end_date": body.end_date.isoformat()})
    try:
        pdf_path = generate_cancellation(contract_id, body.end_date, store)
        updated = store.update("contracts", contract_id, {"cancellation_pdf": str(pdf_path)})
    except Exception:
        pass  # PDF generation failure should not block the cancellation
    return _enrich(Contract(**updated))
