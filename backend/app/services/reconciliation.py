from datetime import date, timedelta

from app.models.invoice import Invoice, InvoiceStatus


def effective_status(invoice: Invoice, today: date, payment_terms_days: int) -> str:
    if invoice.status == InvoiceStatus.paid:
        return "paid"
    if invoice.status == InvoiceStatus.sent and invoice.sent_at is not None:
        due_date = invoice.sent_at.date() + timedelta(days=payment_terms_days)
        if today > due_date:
            return "overdue"
    return invoice.status
