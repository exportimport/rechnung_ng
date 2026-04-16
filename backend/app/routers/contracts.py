from datetime import date
from pathlib import Path

import magic
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.db.yaml_store import store
from app.models.contract import Contract, ContractStatus, compute_status
from app.models.plan import Plan, current_price

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads" / "contracts"

router = APIRouter(prefix="/contracts")


def _load_lookups():
    customers = {c["id"]: c for c in store.load("customers")}
    plans = {p["id"]: p for p in store.load("plans")}
    return customers, plans


def _enrich(contract: Contract, customers: dict, plans: dict) -> dict:
    today = date.today()
    status = compute_status(contract.start_date, contract.end_date, today)
    customer_d = customers.get(contract.customer_id)
    customer_name = (
        f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt"
    )
    plan_d = plans.get(contract.plan_id)
    plan_name = plan_d["name"] if plan_d else "Unbekannt"
    price = None
    if plan_d:
        p = current_price(Plan(**plan_d), today)
        price = float(p) if p is not None else None
    data = contract.model_dump(mode="json")
    data["status"] = status.value
    data["customer_name"] = customer_name
    data["plan_name"] = plan_name
    data["current_price"] = price
    return data


@router.get("")
def list_contracts(request: Request, status: ContractStatus | None = None):
    from app.main import render

    contracts = [Contract(**d) for d in store.load("contracts")]
    customers, plans = _load_lookups()
    enriched = [_enrich(c, customers, plans) for c in contracts]
    if status:
        enriched = [c for c in enriched if c["status"] == status.value]

    ctx = {
        "active_page": "contracts",
        "contracts": enriched,
        "status_filter": status.value if status else "",
    }
    return render(request, "base.html.j2", "fragments/contract_table.html.j2", ctx)


@router.get("/new")
def new_contract_form(request: Request):
    from app.main import render

    customers, plans = _load_lookups()
    ctx = {
        "active_page": "contracts",
        "contract": None,
        "customers": list(customers.values()),
        "plans": list(plans.values()),
        "errors": {},
    }
    return render(request, "base.html.j2", "pages/contract_form.html.j2", ctx)


@router.get("/{contract_id}")
def edit_contract_form(request: Request, contract_id: int):
    from app.main import render

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    customers, plans = _load_lookups()
    ctx = {
        "active_page": "contracts",
        "contract": _enrich(Contract(**d), customers, plans),
        "customers": list(customers.values()),
        "plans": list(plans.values()),
        "errors": {},
    }
    return render(request, "base.html.j2", "pages/contract_form.html.j2", ctx)


@router.post("")
async def create_contract(request: Request, response: Response):
    from app.main import set_toast
    from app.main import templates as jinja_env

    form = await request.form()
    data = dict(form)
    errors = _validate_contract(data)
    if errors:
        customers, plans = _load_lookups()
        html = jinja_env.get_template("pages/contract_form.html.j2").render(
            request=request, active_page="contracts", contract=None,
            customers=list(customers.values()), plans=list(plans.values()),
            form_data=data, errors=errors,
        )
        return HTMLResponse(html, status_code=422)

    # Check FK constraints
    customer_id = int(data["customer_id"])
    plan_id = int(data["plan_id"])
    if not store.get_by_id("customers", customer_id):
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    plan_d = store.get_by_id("plans", plan_id)
    if not plan_d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    start = date.fromisoformat(data["start_date"])
    if current_price(Plan(**plan_d), start) is None:
        raise HTTPException(
            status_code=422,
            detail=f"Tarif hat am {start} keinen gültigen Preis.",
        )

    store.create("contracts", {
        "customer_id": customer_id,
        "plan_id": plan_id,
        "start_date": data["start_date"],
        "end_date": data.get("end_date") or None,
        "billing_cycle": data.get("billing_cycle", "monthly"),
        "reference": data.get("reference") or None,
        "comment": data.get("comment") or None,
    })
    _r = HTMLResponse("", status_code=200)
    set_toast(_r, "Vertrag erstellt.")
    _r.headers["HX-Redirect"] = "/contracts"
    return _r


@router.put("/{contract_id}")
async def update_contract(request: Request, response: Response, contract_id: int):
    from app.main import set_toast
    from app.main import templates as jinja_env

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")

    form = await request.form()
    data = dict(form)
    errors = _validate_contract(data)
    if errors:
        customers, plans = _load_lookups()
        html = jinja_env.get_template("pages/contract_form.html.j2").render(
            request=request, active_page="contracts",
            contract=_enrich(Contract(**d), customers, plans),
            customers=list(customers.values()), plans=list(plans.values()),
            form_data=data, errors=errors,
        )
        return HTMLResponse(html, status_code=422)

    store.update("contracts", contract_id, {
        "customer_id": int(data["customer_id"]),
        "plan_id": int(data["plan_id"]),
        "start_date": data["start_date"],
        "end_date": data.get("end_date") or None,
        "billing_cycle": data.get("billing_cycle", "monthly"),
        "reference": data.get("reference") or None,
        "comment": data.get("comment") or None,
    })
    _r = HTMLResponse("", status_code=200)
    set_toast(_r, "Vertrag aktualisiert.")
    _r.headers["HX-Redirect"] = "/contracts"
    return _r


@router.delete("/{contract_id}")
def delete_contract(contract_id: int, response: Response):
    from app.main import set_toast

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    invoices = store.load("invoices")
    if any(inv.get("contract_id") == contract_id for inv in invoices):
        raise HTTPException(status_code=409, detail="Vertrag hat noch Rechnungen")
    store.delete("contracts", contract_id)
    _r = HTMLResponse("", status_code=200)
    set_toast(_r, "Vertrag gelöscht.")
    return _r


@router.post("/{contract_id}/cancel")
async def cancel_contract(request: Request, response: Response, contract_id: int):
    from app.main import set_toast
    from app.services.cancellation import generate_cancellation

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")

    form = await request.form()
    end_date_str = form.get("end_date", "")
    if not end_date_str:
        raise HTTPException(status_code=422, detail="Kündigungsdatum fehlt")
    end_date = date.fromisoformat(end_date_str)

    store.update("contracts", contract_id, {"end_date": end_date.isoformat()})
    try:
        pdf_path = generate_cancellation(contract_id, end_date, store)
        store.update("contracts", contract_id, {"cancellation_pdf": str(pdf_path)})
    except Exception:
        pass

    _r = HTMLResponse("", status_code=200)
    set_toast(_r, "Vertrag gekündigt.")
    _r.headers["HX-Redirect"] = f"/contracts/{contract_id}"
    return _r


@router.post("/{contract_id}/scan")
async def upload_scan(contract_id: int, file: UploadFile):
    from app.main import set_toast

    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")

    content = await file.read()
    # Validate via magic bytes (not just Content-Type header)
    mime = magic.from_buffer(content, mime=True)
    if mime != "application/pdf":
        raise HTTPException(status_code=422, detail="Nur PDF-Dateien erlaubt")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{contract_id}.pdf"
    dest.write_bytes(content)
    store.update("contracts", contract_id, {"scan_file": str(dest)})
    _r = HTMLResponse(
        f'<span class="text-success">Scan vorhanden</span> '
        f'<a href="/contracts/{contract_id}/scan" class="btn btn--sm btn--secondary">Download</a>',
        status_code=200,
    )
    set_toast(_r, "Scan hochgeladen.")
    return _r


@router.get("/{contract_id}/scan")
def download_scan(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    contract = Contract(**d)
    if not contract.scan_file or not Path(contract.scan_file).exists():
        raise HTTPException(status_code=404, detail="Kein Scan vorhanden")
    return FileResponse(contract.scan_file, media_type="application/pdf",
                        filename=f"vertrag-{contract_id}.pdf")


@router.get("/{contract_id}/cancellation-pdf")
def download_cancellation_pdf(contract_id: int):
    d = store.get_by_id("contracts", contract_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vertrag nicht gefunden")
    contract = Contract(**d)
    if not contract.cancellation_pdf or not Path(contract.cancellation_pdf).exists():
        raise HTTPException(status_code=404, detail="Kein Kündigungsdokument vorhanden")
    return FileResponse(contract.cancellation_pdf, media_type="application/pdf",
                        filename=f"kuendigung-{contract_id}.pdf")


def _validate_contract(data: dict) -> dict:
    errors = {}
    if not data.get("customer_id"):
        errors["customer_id"] = "Pflichtfeld"
    if not data.get("plan_id"):
        errors["plan_id"] = "Pflichtfeld"
    if not data.get("start_date"):
        errors["start_date"] = "Pflichtfeld"
    if not data.get("billing_cycle"):
        errors["billing_cycle"] = "Pflichtfeld"
    return errors
