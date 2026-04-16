"""Tests for CAMT.053 reconciliation models — spec §2."""
from datetime import date, datetime

import pytest

from app.models.camt import (
    CamtTransaction,
    ImportSummary,
    MatchConfidence,
    MatchResult,
    MatchStatus,
)
from app.models.invoice import Invoice, InvoiceStatus


# ---------------------------------------------------------------------------
# InvoiceStatus
# ---------------------------------------------------------------------------


def test_invoice_status_has_paid():
    assert InvoiceStatus.paid == "paid"


def test_invoice_status_draft_and_sent_unchanged():
    assert InvoiceStatus.draft == "draft"
    assert InvoiceStatus.sent == "sent"


# ---------------------------------------------------------------------------
# Invoice new fields
# ---------------------------------------------------------------------------


def _base_invoice(**kwargs) -> Invoice:
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


def test_invoice_paid_at_defaults_to_none():
    inv = _base_invoice()
    assert inv.paid_at is None


def test_invoice_payment_transaction_id_defaults_to_none():
    inv = _base_invoice()
    assert inv.payment_transaction_id is None


def test_invoice_accepts_paid_at():
    inv = _base_invoice(paid_at=date(2025, 3, 15))
    assert inv.paid_at == date(2025, 3, 15)


def test_invoice_accepts_payment_transaction_id():
    inv = _base_invoice(payment_transaction_id="TXN-ABC-123")
    assert inv.payment_transaction_id == "TXN-ABC-123"


def test_invoice_status_paid_persists():
    inv = _base_invoice(status=InvoiceStatus.paid)
    assert inv.status == InvoiceStatus.paid


# ---------------------------------------------------------------------------
# MatchStatus
# ---------------------------------------------------------------------------


def test_match_status_values():
    assert MatchStatus.unmatched == "unmatched"
    assert MatchStatus.auto_matched == "auto_matched"
    assert MatchStatus.manually_matched == "manually_matched"
    assert MatchStatus.ignored == "ignored"


# ---------------------------------------------------------------------------
# MatchConfidence
# ---------------------------------------------------------------------------


def test_match_confidence_values():
    assert MatchConfidence.high == "high"
    assert MatchConfidence.medium == "medium"
    assert MatchConfidence.low == "low"


# ---------------------------------------------------------------------------
# CamtTransaction
# ---------------------------------------------------------------------------


def _base_tx(**kwargs) -> CamtTransaction:
    defaults = dict(
        transaction_id="ACCTSVR-001",
        booking_date=date(2025, 3, 15),
        value_date=date(2025, 3, 15),
        amount=119.00,
        currency="EUR",
        credit_debit="CRDT",
        debtor_name="Max Mustermann",
        debtor_iban="DE89370400440532013000",
        remittance_info="RE 2025-03-0001",
        imported_at=datetime(2025, 4, 1, 12, 0),
        source_file="kontoauszug_2025_03.xml",
    )
    defaults.update(kwargs)
    return CamtTransaction(**defaults)


def test_camt_transaction_defaults():
    tx = _base_tx()
    assert tx.match_status == MatchStatus.unmatched
    assert tx.matched_invoice_id is None
    assert tx.matched_at is None
    assert tx.match_confidence is None


def test_camt_transaction_credit_debit_crdt():
    tx = _base_tx(credit_debit="CRDT")
    assert tx.credit_debit == "CRDT"


def test_camt_transaction_rejects_invalid_credit_debit():
    with pytest.raises(Exception):
        _base_tx(credit_debit="INVALID")


def test_camt_transaction_optional_fields_none():
    tx = _base_tx(debtor_name=None, debtor_iban=None, remittance_info=None)
    assert tx.debtor_name is None
    assert tx.debtor_iban is None
    assert tx.remittance_info is None


def test_camt_transaction_matched_state():
    tx = _base_tx(
        match_status=MatchStatus.auto_matched,
        matched_invoice_id=42,
        match_confidence=MatchConfidence.high,
        matched_at=datetime(2025, 4, 1, 12, 0),
    )
    assert tx.match_status == MatchStatus.auto_matched
    assert tx.matched_invoice_id == 42
    assert tx.match_confidence == MatchConfidence.high


# ---------------------------------------------------------------------------
# MatchResult
# ---------------------------------------------------------------------------


def test_match_result_no_match():
    result = MatchResult(confidence=None, invoice_id=None, reason="no match found")
    assert result.confidence is None
    assert result.invoice_id is None


def test_match_result_high_confidence():
    result = MatchResult(confidence=MatchConfidence.high, invoice_id=1, reason="invoice number found in Verwendungszweck")
    assert result.confidence == MatchConfidence.high
    assert result.invoice_id == 1


# ---------------------------------------------------------------------------
# ImportSummary
# ---------------------------------------------------------------------------


def test_import_summary_fields():
    summary = ImportSummary(
        total_parsed=10,
        imported=8,
        skipped_duplicates=2,
        auto_matched=5,
        queued_for_review=2,
        unmatched=1,
    )
    assert summary.total_parsed == 10
    assert summary.skipped_duplicates == 2
    assert summary.imported + summary.skipped_duplicates == summary.total_parsed
