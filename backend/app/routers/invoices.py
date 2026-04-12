import json
import smtplib
import socket
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.db.yaml_store import store
from app.models.invoice import BulkDeleteRequest, GenerateRequest, Invoice, InvoiceStatus, SendRequest
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


@router.post("/generate")
def generate(body: GenerateRequest):
    def event_stream():
        for event in generate_invoices(body.year, body.month, store):
            if event[0] == "progress":
                _, current, total = event
                yield f"data: {json.dumps({'current': current, 'total': total})}\n\n"
            elif event[0] == "done":
                _, results = event
                yield f"data: {json.dumps({'done': True, 'count': len(results)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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


@router.post("/bulk-delete", status_code=204)
def bulk_delete_invoices(body: BulkDeleteRequest):
    id_set = set(body.ids)
    all_records = store.load("invoices")
    to_delete = [Invoice(**d) for d in all_records if d.get("id") in id_set]

    non_drafts = [i for i in to_delete if i.status != InvoiceStatus.draft]
    if non_drafts:
        raise HTTPException(status_code=409, detail="Nur Entwürfe können gelöscht werden")

    for invoice in to_delete:
        if invoice.pdf_path and Path(invoice.pdf_path).exists():
            Path(invoice.pdf_path).unlink()

    remaining = [d for d in all_records if d.get("id") not in id_set]
    store.save("invoices", remaining)


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
