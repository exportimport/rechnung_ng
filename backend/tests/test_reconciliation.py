"""Tests for /reconciliation/* router — spec §8."""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_monthly_view_returns_200(client):
    r = await client.get("/reconciliation")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_monthly_view_uses_base_layout(client):
    r = await client.get("/reconciliation")
    assert "<nav" in r.text  # full page layout, not bare stub


@pytest.mark.asyncio
async def test_monthly_view_has_year_month_dropdowns(client):
    r = await client.get("/reconciliation?year=2025&month=3")
    assert '<select' in r.text
    assert 'name="year"' in r.text
    assert 'name="month"' in r.text
    assert '<option' in r.text


@pytest.mark.asyncio
async def test_monthly_view_has_month_navigation(client):
    r = await client.get("/reconciliation?year=2026&month=3")
    assert "2026" in r.text
    # prev month link
    assert "month=2" in r.text
    # next month link
    assert "month=4" in r.text


@pytest.mark.asyncio
async def test_monthly_view_shows_sent_invoices(client, csrf):
    import app.db.yaml_store as ys
    # Seed customer and sent invoice directly
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    })
    r = await client.get("/reconciliation?year=2025&month=3")
    assert "Mustermann" in r.text


@pytest.mark.asyncio
async def test_monthly_view_shows_bezahlt_for_paid_invoice(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "paid", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00", "paid_at": "2025-03-20",
    })
    r = await client.get("/reconciliation?year=2025&month=3")
    assert "Bezahlt" in r.text


@pytest.mark.asyncio
async def test_monthly_view_shows_ueberfaellig_for_overdue_invoice(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    # sent 2 years ago — definitely overdue
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2024-01-0001", "year": 2024, "month": 1,
        "amount": 119.00, "period_start": "2024-01-01", "period_end": "2024-01-31",
        "status": "sent", "created_at": "2024-01-01T10:00:00",
        "sent_at": "2024-01-01T10:00:00",
    })
    r = await client.get("/reconciliation?year=2024&month=1")
    assert "Überfällig" in r.text


@pytest.mark.asyncio
async def test_customer_view_shows_matched_transaction_debtor_name(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "paid", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00", "paid_at": "2025-03-15",
        "payment_transaction_id": "ACCTSVR-001",
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "ACCTSVR-001",
        "booking_date": "2025-03-15", "value_date": "2025-03-15",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "M. Mustermann GmbH", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "RE 2025-03-0001", "imported_at": "2025-03-15T10:00:00",
        "source_file": "bank.xml", "match_status": "auto_matched",
        "matched_invoice_id": 1, "matched_at": "2025-03-15T10:00:00",
        "match_confidence": "high",
    })
    r = await client.get("/reconciliation/customers/1")
    assert "M. Mustermann GmbH" in r.text


@pytest.mark.asyncio
async def test_monthly_view_shows_matched_transaction_debtor_name(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "paid", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00", "paid_at": "2025-03-15",
        "payment_transaction_id": "ACCTSVR-001",
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "ACCTSVR-001",
        "booking_date": "2025-03-15", "value_date": "2025-03-15",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "M. Mustermann GmbH", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "RE 2025-03-0001", "imported_at": "2025-03-15T10:00:00",
        "source_file": "bank.xml", "match_status": "auto_matched",
        "matched_invoice_id": 1, "matched_at": "2025-03-15T10:00:00",
        "match_confidence": "high",
    })
    r = await client.get("/reconciliation?year=2025&month=3")
    assert "M. Mustermann GmbH" in r.text


@pytest.mark.asyncio
async def test_monthly_view_customer_name_links_to_customer_view(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    })
    r = await client.get("/reconciliation?year=2025&month=3")
    assert "/reconciliation/customers/1" in r.text


@pytest.mark.asyncio
async def test_import_get_returns_200(client):
    r = await client.get("/reconciliation/import")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_import_form_has_file_input(client):
    r = await client.get("/reconciliation/import")
    assert 'type="file"' in r.text


@pytest.mark.asyncio
async def test_reconciliation_pages_have_subnav(client):
    r = await client.get("/reconciliation/import")
    assert "/reconciliation/unmatched" in r.text
    assert "/reconciliation/review" in r.text


@pytest.mark.asyncio
async def test_import_nav_link_is_active_on_import_page(client):
    r = await client.get("/reconciliation/import")
    assert "subnav__link--active" in r.text


@pytest.mark.asyncio
async def test_unmatched_returns_200(client):
    r = await client.get("/reconciliation/unmatched")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_unmatched_shows_transactions(client, csrf):
    # Import some transactions first
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    r = await client.get("/reconciliation/unmatched")
    assert "119" in r.text  # first CRDT entry amount


@pytest.mark.asyncio
async def test_review_returns_200(client):
    r = await client.get("/reconciliation/review")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_review_uses_base_layout(client):
    r = await client.get("/reconciliation/review")
    assert "<nav" in r.text


@pytest.mark.asyncio
async def test_review_shows_medium_confidence_transactions(client, csrf):
    import app.db.yaml_store as ys
    from datetime import datetime
    # Seed a medium-confidence transaction (match_confidence set, match_status unmatched)
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-REVIEW-001",
        "booking_date": "2026-04-05",
        "value_date": "2026-04-05",
        "amount": 119.00,
        "currency": "EUR",
        "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann",
        "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag",
        "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml",
        "match_status": "unmatched",
        "matched_invoice_id": None,
        "matched_at": None,
        "match_confidence": "medium",
    })
    r = await client.get("/reconciliation/review")
    assert "TX-REVIEW-001" in r.text


@pytest.mark.asyncio
async def test_review_has_confirm_button(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-CONFIRM-001",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag", "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": 1, "matched_at": None, "match_confidence": "medium",
    })
    r = await client.get("/reconciliation/review")
    assert "Bestätigen" in r.text


@pytest.mark.asyncio
async def test_review_confirm_post_marks_matched(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-CONFIRM-002",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag", "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": 1, "matched_at": None, "match_confidence": "medium",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2026-04-0001", "year": 2026, "month": 4,
        "amount": 119.00, "period_start": "2026-04-01", "period_end": "2026-04-30",
        "status": "sent", "created_at": "2026-04-01T10:00:00",
        "sent_at": "2026-04-01T10:00:00",
    })
    r = await client.post(
        "/reconciliation/review/TX-CONFIRM-002/confirm",
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    txs = ys.store.load("camt_transactions")
    tx = next(t for t in txs if t["transaction_id"] == "TX-CONFIRM-002")
    assert tx["match_status"] == "manually_matched"


@pytest.mark.asyncio
async def test_review_confirm_marks_invoice_paid(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-CONFIRM-003",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag", "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": 1, "matched_at": None, "match_confidence": "medium",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2026-04-0001", "year": 2026, "month": 4,
        "amount": 119.00, "period_start": "2026-04-01", "period_end": "2026-04-30",
        "status": "sent", "created_at": "2026-04-01T10:00:00",
        "sent_at": "2026-04-01T10:00:00",
    })
    await client.post(
        "/reconciliation/review/TX-CONFIRM-003/confirm",
        headers={"X-CSRF-Token": csrf},
    )
    invoices = ys.store.load("invoices")
    inv = next(i for i in invoices if i["id"] == 1)
    assert inv["status"] == "paid"


@pytest.mark.asyncio
async def test_unmatched_has_ignore_button(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-IGNORE-001",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 55.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Unknown", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/reconciliation/unmatched")
    assert "Ignorieren" in r.text


@pytest.mark.asyncio
async def test_ignore_post_marks_transaction_ignored(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-IGNORE-002",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 55.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Unknown", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.post(
        "/reconciliation/unmatched/TX-IGNORE-002/ignore",
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    txs = ys.store.load("camt_transactions")
    tx = next(t for t in txs if t["transaction_id"] == "TX-IGNORE-002")
    assert tx["match_status"] == "ignored"


@pytest.mark.asyncio
async def test_review_has_reject_button(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-REJECT-001",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag", "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": 1, "matched_at": None, "match_confidence": "medium",
    })
    r = await client.get("/reconciliation/review")
    assert "Ablehnen" in r.text


@pytest.mark.asyncio
async def test_review_reject_clears_suggestion(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-REJECT-002",
        "booking_date": "2026-04-05", "value_date": "2026-04-05",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": "DE89370400440532013000",
        "remittance_info": "Monatsbeitrag", "imported_at": "2026-04-22T08:00:00",
        "source_file": "test.xml", "match_status": "unmatched",
        "matched_invoice_id": 1, "matched_at": None, "match_confidence": "medium",
    })
    r = await client.post(
        "/reconciliation/review/TX-REJECT-002/reject",
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    txs = ys.store.load("camt_transactions")
    tx = next(t for t in txs if t["transaction_id"] == "TX-REJECT-002")
    assert tx["match_confidence"] is None
    assert tx["matched_invoice_id"] is None
    assert tx["match_status"] == "unmatched"


@pytest.mark.asyncio
async def test_customer_view_shows_unmatched_transactions_panel(client):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-UNMATCHED-CUST",
        "booking_date": "2026-04-10", "value_date": "2026-04-10",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Unbekannt", "debtor_iban": None,
        "remittance_info": "Überweisung", "imported_at": "2026-04-10T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/reconciliation/customers/1")
    assert "TX-UNMATCHED-CUST" in r.text


@pytest.mark.asyncio
async def test_customer_view_unmatched_panel_has_assign_form(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2026-04-0001", "year": 2026, "month": 4,
        "amount": 119.00, "period_start": "2026-04-01", "period_end": "2026-04-30",
        "status": "sent", "created_at": "2026-04-01T10:00:00",
        "sent_at": "2026-04-01T10:00:00",
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-ASSIGN-001",
        "booking_date": "2026-04-10", "value_date": "2026-04-10",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-10T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/reconciliation/customers/1")
    assert "Zuweisen" in r.text
    assert "2026-04-0001" in r.text  # open invoice appears in dropdown


@pytest.mark.asyncio
async def test_customer_match_post_marks_transaction_and_invoice(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2026-04-0001", "year": 2026, "month": 4,
        "amount": 119.00, "period_start": "2026-04-01", "period_end": "2026-04-30",
        "status": "sent", "created_at": "2026-04-01T10:00:00",
        "sent_at": "2026-04-01T10:00:00",
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-ASSIGN-002",
        "booking_date": "2026-04-10", "value_date": "2026-04-10",
        "amount": 119.00, "currency": "EUR", "credit_debit": "CRDT",
        "debtor_name": "Max Mustermann", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-10T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.post(
        "/reconciliation/customers/1/match",
        data={"transaction_id": "TX-ASSIGN-002", "invoice_id": 1},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    txs = ys.store.load("camt_transactions")
    tx = next(t for t in txs if t["transaction_id"] == "TX-ASSIGN-002")
    assert tx["match_status"] == "manually_matched"
    assert tx["matched_invoice_id"] == 1
    invs = ys.store.load("invoices")
    inv = next(i for i in invs if i["id"] == 1)
    assert inv["status"] == "paid"


@pytest.mark.asyncio
async def test_customer_view_unmatched_filter_by_month(client):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-APRIL", "booking_date": "2026-04-10",
        "value_date": "2026-04-10", "amount": 119.00, "currency": "EUR",
        "credit_debit": "CRDT", "debtor_name": "A", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-10T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-MARCH", "booking_date": "2026-03-05",
        "value_date": "2026-03-05", "amount": 55.00, "currency": "EUR",
        "credit_debit": "CRDT", "debtor_name": "B", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-03-05T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/reconciliation/customers/1?tx_year=2026&tx_month=4")
    assert "TX-APRIL" in r.text
    assert "TX-MARCH" not in r.text


@pytest.mark.asyncio
async def test_customer_view_has_tx_filter_dropdowns(client):
    r = await client.get("/reconciliation/customers/1")
    assert 'name="tx_year"' in r.text
    assert 'name="tx_month"' in r.text


@pytest.mark.asyncio
async def test_customer_view_shows_paid_at(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "paid", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00", "paid_at": "2025-03-20",
        "payment_transaction_id": None,
    })
    r = await client.get("/reconciliation/customers/1")
    assert "20.03.2025" in r.text


@pytest.mark.asyncio
async def test_customer_view_unmatched_search_filters_results(client):
    import app.db.yaml_store as ys
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-MUELLER", "booking_date": "2026-04-01",
        "value_date": "2026-04-01", "amount": 100.00, "currency": "EUR",
        "credit_debit": "CRDT", "debtor_name": "Hans Müller", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-01T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    ys.store.create("camt_transactions", {
        "transaction_id": "TX-SCHMIDT", "booking_date": "2026-04-02",
        "value_date": "2026-04-02", "amount": 200.00, "currency": "EUR",
        "credit_debit": "CRDT", "debtor_name": "Anna Schmidt", "debtor_iban": None,
        "remittance_info": None, "imported_at": "2026-04-02T10:00:00",
        "source_file": "bank.xml", "match_status": "unmatched",
        "matched_invoice_id": None, "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/reconciliation/customers/1?tx_search=müller&tx_cols=debtor_name")
    assert "TX-MUELLER" in r.text
    assert "TX-SCHMIDT" not in r.text


@pytest.mark.asyncio
async def test_customer_view_has_search_field(client):
    r = await client.get("/reconciliation/customers/1")
    assert 'name="tx_search"' in r.text


@pytest.mark.asyncio
async def test_customer_view_has_column_checkboxes(client):
    r = await client.get("/reconciliation/customers/1")
    assert 'name="tx_cols"' in r.text
    assert 'value="debtor_name"' in r.text
    assert 'value="debtor_iban"' in r.text
    assert 'value="remittance_info"' in r.text
    assert 'value="transaction_id"' in r.text


@pytest.mark.asyncio
async def test_customer_view_returns_200(client, csrf):
    await client.post("/customers", data={
        "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1",
        "postcode": "12345", "city": "Berlin",
        "iban": "DE89370400440532013000", "email": "max@example.com",
    }, headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/reconciliation/customers/1")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_customer_view_uses_base_layout(client):
    r = await client.get("/reconciliation/customers/1")
    assert "<nav" in r.text


@pytest.mark.asyncio
async def test_customer_view_shows_invoices(client):
    import app.db.yaml_store as ys
    ys.store.create("customers", {
        "id": 1, "vorname": "Max", "nachname": "Mustermann",
        "street": "Musterstr", "house_number": "1", "postcode": "12345",
        "city": "Berlin", "iban": "DE89370400440532013000", "email": "max@example.com",
    })
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    })
    r = await client.get("/reconciliation/customers/1")
    assert "2025-03-0001" in r.text


@pytest.mark.asyncio
async def test_import_post_shows_imported_count(client, csrf):
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    r = await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "Importiert: 5" in r.text


@pytest.mark.asyncio
async def test_import_post_shows_auto_matched_count(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2025-03-0001", "year": 2025, "month": 3,
        "amount": 119.00, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "status": "sent", "created_at": "2025-03-01T10:00:00",
        "sent_at": "2025-03-01T10:00:00",
    })
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    r = await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "Auto-Match: 1" in r.text


@pytest.mark.asyncio
async def test_import_post_shows_skipped_count(client, csrf):
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    # Import twice — second run should show skipped
    await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    r = await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    assert "Übersprungen: 5" in r.text
