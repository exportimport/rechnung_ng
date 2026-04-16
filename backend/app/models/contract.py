from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class BillingCycle(StrEnum):
    monthly = "monthly"
    quarterly = "quarterly"


class ContractStatus(StrEnum):
    not_yet_active = "not_yet_active"
    active = "active"
    cancelled = "cancelled"


def compute_status(start_date: date, end_date: date | None, today: date) -> ContractStatus:
    if start_date > today:
        return ContractStatus.not_yet_active
    if end_date is None or end_date > today:
        return ContractStatus.active
    return ContractStatus.cancelled


class Contract(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    start_date: date
    end_date: date | None = None
    reference: str | None = None
    billing_cycle: BillingCycle
    scan_file: str | None = None
    cancellation_pdf: str | None = None
    comment: str | None = None


class ContractRead(Contract):
    status: ContractStatus
    customer_name: str
    plan_name: str
    current_price: float | None


class ContractCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_date: date
    end_date: date | None = None
    reference: str | None = None
    billing_cycle: BillingCycle
    comment: str | None = None


ContractUpdate = ContractCreate


class CancelRequest(BaseModel):
    end_date: date
