import smtplib
import socket
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.db.yaml_store import store
from app.models.invoice import GenerateRequest, Invoice, InvoiceStatus, SendRequest
from app.services.invoice_generator import generate_invoices

router = APIRouter()


def _serialize(inv: Invoice) -> dict:
    return inv.model_dump(mode="json")


@router.get("")
def list_invoices(
    year: int | None = None,
    month: int | None = None,
    status: InvoiceStatus | None = None,
):
    invoices = [Invoice(**d) for d in store.load("invoices")]
    if year is not None:
        invoices = [i for i in invoices if i.year == year]
    if month is not None:
        invoices = [i for i in invoices if i.month == month]
    if status is not None:
        invoices = [i for i in invoices if i.status == status]
    return [_serialize(i) for i in invoices]


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int):
    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    return _serialize(Invoice(**d))


@router.post("/generate", status_code=201)
def generate(body: GenerateRequest):
    created = generate_invoices(body.year, body.month, store)
    return [_serialize(i) for i in created]


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


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int):
    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)
    if invoice.status != InvoiceStatus.draft:
        raise HTTPException(status_code=409, detail="Nur Entwürfe können gelöscht werden")
    if invoice.pdf_path and Path(invoice.pdf_path).exists():
        Path(invoice.pdf_path).unlink()
    store.delete("invoices", invoice_id)


@router.post("/{invoice_id}/send")
def send_invoice(invoice_id: int, body: SendRequest):
    from app.services.mail_service import send_invoice as do_send

    d = store.get_by_id("invoices", invoice_id)
    if not d:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    invoice = Invoice(**d)
    from app.services.mail_service import select_template
    template_id = body.template_id if body.template_id != "auto" else select_template(invoice, store)
    try:
        do_send(invoice, template_id, store)
    except (smtplib.SMTPException, socket.gaierror, OSError) as e:
        raise HTTPException(status_code=502, detail=f"SMTP-Fehler: {e}")
    updated = store.get_by_id("invoices", invoice_id)
    return _serialize(Invoice(**updated))


@router.post("/send-batch")
def send_batch(body: GenerateRequest):
    from app.services.mail_service import send_invoice as do_send, select_template

    invoices = [
        Invoice(**d)
        for d in store.load("invoices")
        if d.get("year") == body.year
        and d.get("month") == body.month
        and d.get("status") == InvoiceStatus.draft
    ]
    results = []
    for invoice in invoices:
        template_id = select_template(invoice, store)
        do_send(invoice, template_id, store)
        updated = store.get_by_id("invoices", invoice.id)
        results.append(_serialize(Invoice(**updated)))
    return results
