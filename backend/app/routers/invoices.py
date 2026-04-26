import smtplib
import socket
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse

from app.db.yaml_store import store
from app.models.invoice import Invoice, InvoiceStatus
from app.services.invoice_generator import generate_invoices

router = APIRouter(prefix="/invoices")


def _enrich_invoice(inv: Invoice) -> dict:
    customers = {c["id"]: c for c in store.load("customers")}
    contracts = {c["id"]: c for c in store.load("contracts")}
    plans = {p["id"]: p for p in store.load("plans")}

    customer_d = customers.get(inv.customer_id)
    contract_d = contracts.get(inv.contract_id)
    plan_name = ""
    if contract_d:
        plan_d = plans.get(contract_d["plan_id"])
        plan_name = plan_d["name"] if plan_d else ""

    data = inv.model_dump(mode="json")
    data["customer_name"] = (
        f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt"
    )
    data["plan_name"] = plan_name
    return data


def _load_invoices(year=None, month=None, status=None):
    invoices = [Invoice(**d) for d in store.load("invoices")]
    if year is not None:
        invoices = [i for i in invoices if i.year == year]
    if month is not None:
        invoices = [i for i in invoices if i.month == month]
    if status is not None:
        invoices = [i for i in invoices if i.status == status]

    customers = {c["id"]: c for c in store.load("customers")}
    contracts = {c["id"]: c for c in store.load("contracts")}
    plans = {p["id"]: p for p in store.load("plans")}

    enriched = []
    for inv in invoices:
        customer_d = customers.get(inv.customer_id)
        contract_d = contracts.get(inv.contract_id)
        plan_name = ""
        if contract_d:
            plan_d = plans.get(contract_d["plan_id"])
            plan_name = plan_d["name"] if plan_d else ""
        data = inv.model_dump(mode="json")
        data["customer_name"] = (
            f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt"
        )
        data["plan_name"] = plan_name
        enriched.append(data)
    return enriched


@router.get("")
def list_invoices(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    status: str | None = None,
):
    from app.main import render

    today = date.today()
    year = year or today.year
    month = month or today.month
    status_enum = InvoiceStatus(status) if status else None

    enriched = _load_invoices(year, month, status_enum)
    ctx = {
        "active_page": "invoices",
        "invoices": enriched,
        "filter_year": year,
        "filter_month": month,
        "filter_status": status_enum.value if status_enum else "",
    }
    return render(request, "base.html.j2", "fragments/invoice_table.html.j2", ctx)


@router.post("/generate")
async def generate(request: Request):
    import json as _json

    form = await request.form()
    year = int(form.get("year", 0))
    month = int(form.get("month", 0))

    if not year or not month:
        raise HTTPException(status_code=422, detail="Jahr und Monat erforderlich")

    results = []
    for event in generate_invoices(year, month, store):
        if event[0] == "done":
            _, results = event

    count = len(results)
    html = f'<div class="text-success">Fertig — {count} Rechnung(en) generiert.</div>'
    _r = HTMLResponse(html, status_code=200)
    _r.headers["HX-Trigger"] = _json.dumps(
        {"showToast": {"message": f"{count} Rechnung(en) generiert.", "ok": True}}
    )
    _r.headers["HX-Redirect"] = f"/invoices?year={year}&month={month}"
    return _r


@router.get("/{invoice_id}/pdf")
def download_pdf(invoice_id: int):
    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)
    if not invoice.pdf_path or not Path(invoice.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF nicht vorhanden")
    return FileResponse(
        invoice.pdf_path,
        media_type="application/pdf",
        filename=f"{invoice.invoice_number}.pdf",
    )


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, response: Response):
    from app.main import set_toast

    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)
    if invoice.status != InvoiceStatus.draft:
        raise HTTPException(status_code=409, detail="Nur Entwürfe können gelöscht werden")
    if invoice.pdf_path and Path(invoice.pdf_path).exists():
        Path(invoice.pdf_path).unlink()
    store.delete("invoices", invoice_id)
    _r = HTMLResponse("", status_code=200)
    set_toast(_r, "Rechnung gelöscht.")
    return _r


@router.post("/delete-all-drafts")
async def delete_all_drafts(request: Request):
    import json as _json

    form = await request.form()
    year = int(form.get("year", 0))
    month = int(form.get("month", 0))
    if not year or not month:
        raise HTTPException(status_code=422, detail="Jahr und Monat erforderlich")

    all_records = store.load("invoices")
    to_delete = [
        Invoice(**d)
        for d in all_records
        if d.get("year") == year
        and d.get("month") == month
        and d.get("status") == InvoiceStatus.draft
    ]
    for inv in to_delete:
        if inv.pdf_path and Path(inv.pdf_path).exists():
            Path(inv.pdf_path).unlink()

    ids = {i.id for i in to_delete}
    store.save("invoices", [d for d in all_records if d.get("id") not in ids])

    _r = HTMLResponse("", status_code=200)
    _r.headers["HX-Trigger"] = _json.dumps(
        {"showToast": {"message": f"{len(to_delete)} Entwurf/Entwürfe gelöscht.", "ok": True}}
    )
    _r.headers["HX-Redirect"] = f"/invoices?year={year}&month={month}"
    return _r


@router.post("/bulk-delete")
async def bulk_delete(request: Request, response: Response):
    from app.main import set_toast

    form = await request.form()
    ids = {int(v) for v in form.getlist("ids")}
    all_records = store.load("invoices")
    to_delete = [Invoice(**d) for d in all_records if d.get("id") in ids]

    non_drafts = [i for i in to_delete if i.status != InvoiceStatus.draft]
    if non_drafts:
        raise HTTPException(status_code=409, detail="Nur Entwürfe können gelöscht werden")

    for invoice in to_delete:
        if invoice.pdf_path and Path(invoice.pdf_path).exists():
            Path(invoice.pdf_path).unlink()

    remaining = [d for d in all_records if d.get("id") not in ids]
    store.save("invoices", remaining)
    _r = HTMLResponse("", status_code=200)
    set_toast(_r, f"{len(to_delete)} Rechnung(en) gelöscht.")
    _r.headers["HX-Redirect"] = "/invoices"
    return _r


@router.post("/{invoice_id}/send")
async def send_invoice(request: Request, response: Response, invoice_id: int):
    from app.main import set_toast
    from app.services.mail_service import select_template
    from app.services.mail_service import send_invoice as do_send

    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)

    form = await request.form()
    template_id = form.get("template_id", "auto")
    if template_id == "auto":
        template_id = select_template(invoice, store)

    try:
        do_send(invoice, template_id, store)
    except (smtplib.SMTPException, socket.gaierror, OSError) as e:
        raise HTTPException(status_code=502, detail=f"SMTP-Fehler: {e}")

    updated = store.get_by_id("invoices", invoice_id)
    from app.main import templates as jinja_env

    html = jinja_env.get_template("fragments/invoice_row.html.j2").render(
        request=request, invoice=_enrich_invoice(Invoice(**updated))
    )
    _r = HTMLResponse(html, status_code=200)
    set_toast(_r, f"Rechnung {invoice.invoice_number} versendet.")
    return _r


@router.post("/{invoice_id}/mark-paid")
def mark_paid(invoice_id: int, request: Request):
    from app.main import set_toast

    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)
    if invoice.status not in (InvoiceStatus.sent,):
        raise HTTPException(status_code=409, detail="Nur versendete Rechnungen können als bezahlt markiert werden")
    updated = store.update("invoices", invoice_id, {"status": InvoiceStatus.paid, "paid_at": date.today().isoformat()})
    from app.main import templates as jinja_env

    html = jinja_env.get_template("fragments/invoice_row.html.j2").render(
        request=request, invoice=_enrich_invoice(Invoice(**updated))
    )
    _r = HTMLResponse(html, status_code=200)
    set_toast(_r, "Rechnung als bezahlt markiert.")
    return _r


@router.post("/send-batch")
async def send_batch(request: Request):
    from app.main import set_toast
    from app.services.mail_service import select_template
    from app.services.mail_service import send_invoice as do_send

    form = await request.form()
    year = int(form.get("year", 0))
    month = int(form.get("month", 0))

    invoices = [
        Invoice(**d)
        for d in store.load("invoices")
        if d.get("year") == year
        and d.get("month") == month
        and d.get("status") == InvoiceStatus.draft
    ]
    for invoice in invoices:
        template_id = select_template(invoice, store)
        do_send(invoice, template_id, store)

    _r = HTMLResponse("", status_code=200)
    set_toast(_r, f"{len(invoices)} Rechnung(en) versendet.")
    _r.headers["HX-Redirect"] = "/invoices"
    return _r
