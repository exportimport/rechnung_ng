"""Tests for match_transaction() — spec §4 + fixture table §5."""
from datetime import date, datetime

import pytest

from app.models.camt import CamtTransaction, MatchConfidence, MatchStatus
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.services.reconciliation import match_transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tx(**kwargs) -> CamtTransaction:
    defaults = dict(
        transaction_id="TX-001",
        booking_date=date(2025, 4, 10),
        value_date=date(2025, 4, 10),
        amount=119.00,
        currency="EUR",
        credit_debit="CRDT",
        debtor_name="Max Mustermann",
        debtor_iban="DE89370400440532013000",
        remittance_info="RE 2025-03-0001",
        imported_at=datetime(2025, 4, 10, 12, 0),
        source_file="test.xml",
    )
    defaults.update(kwargs)
    return CamtTransaction(**defaults)


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


def _customer(**kwargs) -> Customer:
    defaults = dict(
        id=1,
        vorname="Max",
        nachname="Mustermann",
        street="Musterstr",
        house_number="1",
        postcode="12345",
        city="Berlin",
        iban="DE89370400440532013000",
        email="max@example.com",
    )
    defaults.update(kwargs)
    return Customer(**defaults)


# ---------------------------------------------------------------------------
# T01 — exact invoice number in Verwendungszweck → high confidence
# ---------------------------------------------------------------------------


def test_t01_exact_invoice_number_matches_high_confidence():
    tx = _tx(remittance_info="RE 2025-03-0001")
    invoices = [_invoice(invoice_number="2025-03-0001")]
    customers = [_customer()]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence == MatchConfidence.high
    assert result.invoice_id == 1


def test_t02_invoice_number_embedded_in_text():
    tx = _tx(remittance_info="Rechnung 2025-03-0001 danke")
    invoices = [_invoice(invoice_number="2025-03-0001")]
    customers = [_customer()]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence == MatchConfidence.high
    assert result.invoice_id == 1


def test_t03_multiple_invoice_numbers_no_auto_match():
    tx = _tx(remittance_info="2025-03-0001 und 2025-04-0001", amount=238.00)
    invoices = [
        _invoice(id=1, invoice_number="2025-03-0001"),
        _invoice(id=2, invoice_number="2025-04-0001", month=4),
    ]
    customers = [_customer()]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence is None
    assert result.invoice_id is None


def test_t04_amount_and_iban_match_medium_confidence():
    tx = _tx(remittance_info="Monatsbeitrag März", amount=119.00, debtor_iban="DE89370400440532013000")
    invoices = [_invoice(id=1, amount=119.00, customer_id=1)]
    customers = [_customer(id=1, iban="DE89370400440532013000")]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence == MatchConfidence.medium
    assert result.invoice_id == 1


def test_t05_ambiguous_tier2_no_match():
    # Same customer, two open invoices of same amount → ambiguous, no auto-match
    tx = _tx(remittance_info="Monatsbeitrag", amount=119.00, debtor_iban="DE89370400440532013000")
    invoices = [
        _invoice(id=1, amount=119.00, customer_id=1, month=3),
        _invoice(id=2, amount=119.00, customer_id=1, month=4),
    ]
    customers = [_customer(id=1, iban="DE89370400440532013000")]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence is None
    assert result.invoice_id is None


def test_t06_fuzzy_name_match_low_confidence():
    # Unknown IBAN, but debtor name fuzzy-matches the customer
    tx = _tx(
        remittance_info="zahlung",
        amount=119.00,
        debtor_iban="DE99999999999999999999",
        debtor_name="max mustermann",
    )
    invoices = [_invoice(id=1, amount=119.00, customer_id=1)]
    customers = [_customer(id=1, vorname="Max", nachname="Mustermann", iban="DE89370400440532013000")]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence == MatchConfidence.low
    assert result.invoice_id == 1


def test_t07_no_match():
    tx = _tx(remittance_info="Pizza", amount=12.50, debtor_iban="DE00000000000000000000", debtor_name="Unbekannt")
    invoices = [_invoice(id=1, amount=119.00, customer_id=1)]
    customers = [_customer(id=1)]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence is None
    assert result.invoice_id is None


def test_t09_amount_mismatch_despite_invoice_number_no_match():
    # Invoice number found but amount differs → flag, no auto-match
    tx = _tx(remittance_info="RE 2025-03-0001", amount=50.00)
    invoices = [_invoice(id=1, invoice_number="2025-03-0001", amount=119.00)]
    customers = [_customer()]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence is None
    assert result.invoice_id is None


def test_t10_already_paid_invoice_not_rematched():
    # Invoice is already paid — must not be matched again
    tx = _tx(remittance_info="RE 2025-03-0001", amount=119.00)
    invoices = [_invoice(id=1, invoice_number="2025-03-0001", amount=119.00, status=InvoiceStatus.paid)]
    customers = [_customer()]
    result = match_transaction(tx, invoices, customers)
    assert result.confidence is None
    assert result.invoice_id is None
