from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class InvoiceStatus(StrEnum):
    draft = "draft"
    sent = "sent"
    paid = "paid"


class Invoice(BaseModel):
    id: int
    contract_id: int
    customer_id: int
    invoice_number: str
    year: int
    month: int
    amount: float
    period_start: date
    period_end: date
    status: InvoiceStatus = InvoiceStatus.draft
    pdf_path: str | None = None
    mail_template: str | None = None
    created_at: datetime
    sent_at: datetime | None = None
    paid_at: date | None = None
    payment_transaction_id: str | None = None
    dunning_level: int = 0
    last_reminded_at: date | None = None


class GenerateRequest(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)


class SendRequest(BaseModel):
    template_id: str


class BulkDeleteRequest(BaseModel):
    ids: list[int]
