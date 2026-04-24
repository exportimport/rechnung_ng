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

    tx_by_id = {t["transaction_id"]: t for t in store.load("camt_transactions")}

    rows = []
    for inv in month_invoices:
        customer = customers.get(inv.customer_id)
        data = inv.model_dump(mode="json")
        data["customer_name"] = (
            f"{customer['vorname']} {customer['nachname']}" if customer else "Unbekannt"
        )
        data["effective_status"] = effective_status(inv, today, payment_terms)
        data["matched_tx"] = tx_by_id.get(inv.payment_transaction_id) if inv.payment_transaction_id else None
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

    tx_by_id = {t["transaction_id"]: t for t in store.load("camt_transactions")}

    rows = []
    for inv in sorted(cust_invoices, key=lambda i: (i.year, i.month), reverse=True):
        data = inv.model_dump(mode="json")
        data["effective_status"] = effective_status(inv, today, payment_terms)
        data["matched_tx"] = tx_by_id.get(inv.payment_transaction_id) if inv.payment_transaction_id else None
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


@router.post("/review/{transaction_id}/confirm")
def confirm_match(transaction_id: str):
    from datetime import datetime
    from app.models.camt import CamtTransaction, MatchStatus
    from app.models.invoice import Invoice

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    tx = next((t for t in all_tx if t.transaction_id == transaction_id), None)
    if tx is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)

    tx.match_status = MatchStatus.manually_matched
    tx.matched_at = datetime.now()
    all_records = store.load("camt_transactions")
    for i, r in enumerate(all_records):
        if r["transaction_id"] == transaction_id:
            all_records[i] = tx.model_dump(mode="json")
            break
    store.save("camt_transactions", all_records)

    if tx.matched_invoice_id is not None:
        all_invoices = [Invoice(**d) for d in store.load("invoices")]
        inv = next((i for i in all_invoices if i.id == tx.matched_invoice_id), None)
        if inv is not None:
            store.update("invoices", inv.id, {
                **inv.model_dump(mode="json"),
                "status": "paid",
                "paid_at": tx.booking_date.isoformat(),
                "payment_transaction_id": tx.transaction_id,
            })

    return HTMLResponse("<tr><td colspan='7'>Abgeglichen</td></tr>")


@router.post("/review/{transaction_id}/reject")
def reject_suggestion(transaction_id: str):
    from app.models.camt import CamtTransaction

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    tx = next((t for t in all_tx if t.transaction_id == transaction_id), None)
    if tx is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)

    tx.match_confidence = None
    tx.matched_invoice_id = None
    all_records = store.load("camt_transactions")
    for i, r in enumerate(all_records):
        if r["transaction_id"] == transaction_id:
            all_records[i] = tx.model_dump(mode="json")
            break
    store.save("camt_transactions", all_records)

    return HTMLResponse("<tr><td colspan='7'>Vorschlag abgelehnt</td></tr>")


@router.post("/unmatched/{transaction_id}/ignore")
def ignore_transaction(transaction_id: str):
    from app.models.camt import CamtTransaction, MatchStatus

    all_tx = [CamtTransaction(**d) for d in store.load("camt_transactions")]
    tx = next((t for t in all_tx if t.transaction_id == transaction_id), None)
    if tx is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)

    tx.match_status = MatchStatus.ignored
    all_records = store.load("camt_transactions")
    for i, r in enumerate(all_records):
        if r["transaction_id"] == transaction_id:
            all_records[i] = tx.model_dump(mode="json")
            break
    store.save("camt_transactions", all_records)

    return HTMLResponse("<tr><td colspan='6'>Ignoriert</td></tr>")


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
