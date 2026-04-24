"""Tests for import_camt_file() — spec §6."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services.camt_import import import_camt_file

FIXTURES = Path(__file__).parent / "fixtures"


def _load(filename: str) -> bytes:
    return (FIXTURES / filename).read_bytes()


def _mock_store(existing_transactions=None, invoices=None, customers=None):
    store = MagicMock()
    store.load.side_effect = lambda entity: {
        "camt_transactions": existing_transactions or [],
        "invoices": invoices or [],
        "customers": customers or [],
    }.get(entity, [])
    store.create = MagicMock(side_effect=lambda entity, data: data)
    store.update = MagicMock(side_effect=lambda entity, id, data: data)
    return store


def test_returns_import_summary():
    from app.models.camt import ImportSummary
    store = _mock_store()
    result = import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    assert isinstance(result, ImportSummary)


def test_total_parsed_counts_crdt_entries():
    store = _mock_store()
    result = import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    assert result.total_parsed == 5


def test_new_transactions_are_stored():
    store = _mock_store()
    result = import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    assert result.imported == 5


def test_duplicate_transactions_are_skipped():
    existing = [{"transaction_id": "ACCTSVR-001"}]
    store = _mock_store(existing_transactions=existing)
    result = import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    assert result.skipped_duplicates == 1
    assert result.imported == 4


def test_tier1_match_is_auto_matched():
    invoices = [{
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    }]
    store = _mock_store(invoices=invoices)
    result = import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    assert result.auto_matched == 1


def test_tier2_match_stores_confidence_for_review():
    # Tier 2: amount + IBAN match, no invoice number in remittance
    invoices = [{
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    }]
    customers = [{"id": 1, "vorname": "Max", "nachname": "Mustermann",
                  "street": "Musterstr", "house_number": "1", "postcode": "12345",
                  "city": "Berlin", "iban": "DE89370400440532013000", "email": "m@x.de"}]
    store = _mock_store(invoices=invoices, customers=customers)
    # ACCTSVR-003 in the fixture: amount=119, IBAN=DE89..., no invoice number
    import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    # Find the stored transaction for ACCTSVR-003
    calls = {c[0][1]["transaction_id"]: c[0][1] for c in store.create.call_args_list}
    tx = calls.get("ACCTSVR-003")
    assert tx is not None
    assert tx["match_confidence"] == "medium"
    assert tx["matched_invoice_id"] == 1
    assert tx["match_status"] == "unmatched"  # not auto-matched, awaits review


def test_tier1_match_stores_transaction_as_auto_matched():
    invoices = [{
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    }]
    store = _mock_store(invoices=invoices)
    import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    stored = store.create.call_args_list[0][0][1]  # first created transaction
    assert stored["match_status"] == "auto_matched"
    assert stored["matched_invoice_id"] == 1
    assert stored["match_confidence"] == "high"
    assert stored["matched_at"] is not None


def test_tier1_match_marks_invoice_paid():
    invoices = [{
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    }]
    store = _mock_store(invoices=invoices)
    import_camt_file(_load("camt053_v8_sample.xml"), "sample.xml", store)
    # store.update should have been called to mark invoice as paid
    store.update.assert_called_once()
    call_args = store.update.call_args
    assert call_args[0][0] == "invoices"
    assert call_args[0][1] == 1
    assert call_args[0][2]["status"] == "paid"
