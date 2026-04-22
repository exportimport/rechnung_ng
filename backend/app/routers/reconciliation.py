from datetime import date

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.db.yaml_store import store
from app.services.camt_import import import_camt_file

router = APIRouter(prefix="/reconciliation")


@router.get("")
def monthly_view(request: Request, year: int | None = None, month: int | None = None):
    from app.config import get_config
    from app.main import render
    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.reconciliation import effective_status

    today = date.today()
    year = year or today.year
    month = month or today.month
    cfg = get_config()
    payment_terms = cfg.invoice.payment_terms_days

    customers = {c["id"]: c for c in store.load("customers")}
    all_invoices = [Invoice(**d) for d in store.load("invoices")]
    month_invoices = [
        inv for inv in all_invoices
        if inv.year == year and inv.month == month
        and inv.status != InvoiceStatus.draft
    ]

    rows = []
    for inv in month_invoices:
        customer = customers.get(inv.customer_id)
        data = inv.model_dump(mode="json")
        data["customer_name"] = (
            f"{customer['vorname']} {customer['nachname']}" if customer else "Unbekannt"
        )
        data["effective_status"] = effective_status(inv, today, payment_terms)
        rows.append(data)

    ctx = {"active_page": "reconciliation", "year": year, "month": month, "invoices": rows}
    return render(request, "base.html.j2", "fragments/reconciliation_monthly.html.j2", ctx)


@router.get("/customers/{customer_id}")
def customer_view(customer_id: int):
    return HTMLResponse(f"<p>Kunde {customer_id}</p>")


@router.get("/unmatched")
def unmatched_list(request: Request):
    from app.main import render
    from app.models.camt import CamtTransaction, MatchStatus

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    unmatched = [tx for tx in all_tx if tx.match_status == MatchStatus.unmatched]
    return render(request, "base.html.j2", "fragments/reconciliation_unmatched.html.j2",
                  {"active_page": "reconciliation", "transactions": [tx.model_dump(mode="json") for tx in unmatched]})


@router.get("/review")
def review_queue():
    return HTMLResponse("<p>Prüfwarteschlange</p>")


@router.get("/import")
def import_form(request: Request):
    from app.main import render

    return render(request, "base.html.j2", "fragments/reconciliation_import.html.j2",
                  {"active_page": "reconciliation"})


@router.post("/import")
async def import_post(file: UploadFile):
    xml_bytes = await file.read()
    summary = import_camt_file(xml_bytes, file.filename or "upload.xml", store)
    return HTMLResponse(
        f"<p>Importiert: {summary.imported}, Übersprungen: {summary.skipped_duplicates}</p>"
    )
