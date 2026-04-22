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
async def test_import_get_returns_200(client):
    r = await client.get("/reconciliation/import")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_import_form_has_file_input(client):
    r = await client.get("/reconciliation/import")
    assert 'type="file"' in r.text


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
async def test_import_post_shows_imported_count(client, csrf):
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    r = await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "Importiert: 4" in r.text
