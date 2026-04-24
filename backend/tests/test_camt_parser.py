"""Tests for CAMT.053 v8 parser — spec §3."""
from datetime import date
from pathlib import Path

import pytest

from app.services.camt_parser import UnsupportedNamespaceError, parse_camt053

FIXTURES = Path(__file__).parent / "fixtures"


def _load(filename: str) -> bytes:
    return (FIXTURES / filename).read_bytes()


def test_rejects_unsupported_namespace():
    xml = _load("camt053_wrong_namespace.xml")
    with pytest.raises(UnsupportedNamespaceError):
        parse_camt053(xml, source_file="wrong.xml")


def test_accepts_v8_namespace():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    assert isinstance(result, list)


def test_dbit_entries_excluded():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    assert all(tx.credit_debit == "CRDT" for tx in result)


def test_crdt_count():
    """Sample has 4 CRDT entries and 1 DBIT — expect 4."""
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    assert len(result) == 5


def _first(xml: bytes):
    return parse_camt053(xml, source_file="sample.xml")[0]


def test_transaction_id_from_acct_svr_ref():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.transaction_id == "ACCTSVR-001"


def test_booking_date():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.booking_date == date(2025, 3, 15)


def test_value_date():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.value_date == date(2025, 3, 15)


def test_amount():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.amount == 119.00


def test_currency():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.currency == "EUR"


def test_debtor_name():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.debtor_name == "Max Mustermann"


def test_debtor_iban():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.debtor_iban == "DE89370400440532013000"


def test_remittance_info():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.remittance_info == "RE 2025-03-0001"


def test_source_file():
    tx = _first(_load("camt053_v8_sample.xml"))
    assert tx.source_file == "sample.xml"


def test_imported_at_is_set():
    from datetime import datetime
    tx = _first(_load("camt053_v8_sample.xml"))
    assert isinstance(tx.imported_at, datetime)


def test_transaction_id_falls_back_to_end_to_end_id():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    # Second CRDT entry has no AcctSvcrRef, uses EndToEndId
    tx = result[1]
    assert tx.transaction_id == "E2E-002"


def test_transaction_id_deterministic_fallback():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    # Fourth CRDT entry (index 3) has no refs at all — gets a hash-based ID
    tx = result[3]
    assert tx.transaction_id.startswith("FALLBACK-")
    # Parsing same file twice must produce identical ID
    result2 = parse_camt053(xml, source_file="sample.xml")
    assert result[3].transaction_id == result2[3].transaction_id


def test_missing_debtor_iban_is_none():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    # Third CRDT entry (index 2) has no DbtrAcct
    assert result[2].debtor_iban is None


def test_missing_remittance_info_is_none():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    # Third CRDT entry (index 2) has no RmtInf
    assert result[2].remittance_info is None


def test_value_date_differs_from_booking_date():
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    # Third CRDT entry: BookgDt=2025-03-25, ValDt=2025-03-26
    tx = result[2]
    assert tx.booking_date == date(2025, 3, 25)
    assert tx.value_date == date(2025, 3, 26)


def test_parsed_transactions_start_unmatched():
    from app.models.camt import MatchStatus
    xml = _load("camt053_v8_sample.xml")
    result = parse_camt053(xml, source_file="sample.xml")
    assert all(tx.match_status == MatchStatus.unmatched for tx in result)
