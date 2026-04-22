"""Tests for /reconciliation/* router — spec §8."""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_monthly_view_returns_200(client):
    r = await client.get("/reconciliation")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_import_get_returns_200(client):
    r = await client.get("/reconciliation/import")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_unmatched_returns_200(client):
    r = await client.get("/reconciliation/unmatched")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_review_returns_200(client):
    r = await client.get("/reconciliation/review")
    assert r.status_code == 200


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
async def test_import_post_returns_summary(client, csrf):
    xml = (FIXTURES / "camt053_v8_sample.xml").read_bytes()
    r = await client.post(
        "/reconciliation/import",
        files={"file": ("sample.xml", xml, "application/xml")},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "4" in r.text  # 4 CRDT entries imported
