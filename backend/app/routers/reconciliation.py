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

    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)

    ctx = {"active_page": "reconciliation", "recon_page": "monthly",
           "year": year, "month": month, "invoices": rows,
           "prev_year": prev_year, "prev_month": prev_month,
           "next_year": next_year, "next_month": next_month}
    return render(request, "base.html.j2", "fragments/reconciliation_monthly.html.j2", ctx)


@router.get("/customers/{customer_id}")
def customer_view(request: Request, customer_id: int):
    from app.config import get_config
    from app.main import render
    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.reconciliation import effective_status

    today = date.today()
    cfg = get_config()
    payment_terms = cfg.invoice.payment_terms_days

    customers = {c["id"]: c for c in store.load("customers")}
    customer = customers.get(customer_id)
    all_invoices = [Invoice(**d) for d in store.load("invoices")]
    cust_invoices = [inv for inv in all_invoices
                     if inv.customer_id == customer_id and inv.status != InvoiceStatus.draft]

    rows = []
    for inv in sorted(cust_invoices, key=lambda i: (i.year, i.month), reverse=True):
        data = inv.model_dump(mode="json")
        data["effective_status"] = effective_status(inv, today, payment_terms)
        rows.append(data)

    return render(request, "base.html.j2", "fragments/reconciliation_customer.html.j2",
                  {"active_page": "reconciliation", "recon_page": "customer",
                   "customer_id": customer_id, "customer": customer, "invoices": rows})


@router.get("/unmatched")
def unmatched_list(request: Request):
    from app.main import render
    from app.models.camt import CamtTransaction, MatchStatus

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    unmatched = [tx for tx in all_tx if tx.match_status == MatchStatus.unmatched]
    return render(request, "base.html.j2", "fragments/reconciliation_unmatched.html.j2",
                  {"active_page": "reconciliation", "recon_page": "unmatched",
                   "transactions": [tx.model_dump(mode="json") for tx in unmatched]})


@router.get("/review")
def review_queue(request: Request):
    from app.main import render
    from app.models.camt import CamtTransaction, MatchStatus

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    review = [tx for tx in all_tx
              if tx.match_status == MatchStatus.unmatched and tx.match_confidence is not None]
    return render(request, "base.html.j2", "fragments/reconciliation_review.html.j2",
                  {"active_page": "reconciliation", "recon_page": "review",
                   "transactions": [tx.model_dump(mode="json") for tx in review]})


@router.get("/import")
def import_form(request: Request):
    from app.main import render

    return render(request, "base.html.j2", "fragments/reconciliation_import.html.j2",
                  {"active_page": "reconciliation", "recon_page": "import"})


@router.post("/import")
async def import_post(file: UploadFile):
    xml_bytes = await file.read()
    summary = import_camt_file(xml_bytes, file.filename or "upload.xml", store)
    return HTMLResponse(
        f"<div class='import-result'>"
        f"<p>Importiert: {summary.imported}, "
        f"Übersprungen: {summary.skipped_duplicates}, "
        f"Auto-Match: {summary.auto_matched}</p>"
        f"</div>"
    )
