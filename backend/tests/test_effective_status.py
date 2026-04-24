"""Tests for effective_status() — spec §7."""
from datetime import date, datetime, timedelta

import pytest

from app.services.reconciliation import effective_status
from app.models.invoice import Invoice, InvoiceStatus


def _invoice(**kwargs) -> Invoice:
    defaults = dict(
        id=1,
        contract_id=1,
        customer_id=1,
        invoice_number="2025-03-0001",
        year=2025,
        month=3,
        amount=119.00,
        period_start=date(2025, 3, 1),
        period_end=date(2025, 3, 31),
        status=InvoiceStatus.sent,
        created_at=datetime(2025, 3, 1, 10, 0),
        sent_at=datetime(2025, 3, 1, 10, 0),
    )
    defaults.update(kwargs)
    return Invoice(**defaults)


TODAY = date(2025, 4, 22)
PAYMENT_TERMS = 14


def test_paid_invoice_returns_paid():
    inv = _invoice(status=InvoiceStatus.paid, paid_at=date(2025, 3, 15))
    assert effective_status(inv, TODAY, PAYMENT_TERMS) == "paid"


def test_sent_within_due_date_returns_sent():
    # sent today, due date is 14 days from now — not yet overdue
    sent = datetime.combine(TODAY, datetime.min.time())
    inv = _invoice(status=InvoiceStatus.sent, sent_at=sent)
    assert effective_status(inv, TODAY, PAYMENT_TERMS) == "sent"


def test_sent_past_due_date_returns_overdue():
    # sent 20 days ago, due after 14 — overdue
    sent_date = TODAY - timedelta(days=20)
    sent = datetime.combine(sent_date, datetime.min.time())
    inv = _invoice(status=InvoiceStatus.sent, sent_at=sent)
    assert effective_status(inv, TODAY, PAYMENT_TERMS) == "overdue"


def test_sent_exactly_on_due_date_is_not_overdue():
    # sent 14 days ago — due today, not yet overdue (strictly greater)
    sent_date = TODAY - timedelta(days=PAYMENT_TERMS)
    sent = datetime.combine(sent_date, datetime.min.time())
    inv = _invoice(status=InvoiceStatus.sent, sent_at=sent)
    assert effective_status(inv, TODAY, PAYMENT_TERMS) == "sent"


def test_draft_invoice_returns_draft():
    inv = _invoice(status=InvoiceStatus.draft, sent_at=None)
    assert effective_status(inv, TODAY, PAYMENT_TERMS) == "draft"
