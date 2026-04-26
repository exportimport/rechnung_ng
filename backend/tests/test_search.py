"""Tests for GET /search?q= global search."""
import pytest

CUSTOMER = {
    "vorname": "Hans", "nachname": "Meier",
    "street": "Hauptstr.", "house_number": "1",
    "postcode": "10115", "city": "Berlin",
    "iban": "DE89370400440532013000", "email": "hans@example.com",
}


@pytest.mark.asyncio
async def test_search_empty_query_returns_200(client):
    r = await client.get("/search?q=")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_search_finds_customer_by_name(client, csrf):
    await client.post("/customers", data=CUSTOMER,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/search?q=Meier")
    assert r.status_code == 200
    assert "Meier" in r.text


@pytest.mark.asyncio
async def test_search_finds_invoice_by_number(client, csrf):
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-03-0001", "year": 2024, "month": 3,
        "amount": 49.99, "period_start": "2024-03-01", "period_end": "2024-03-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-03-01T10:00:00", "sent_at": "2024-03-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.get("/search?q=1-1-2024")
    assert r.status_code == 200
    assert "1-1-2024-03-0001" in r.text


@pytest.mark.asyncio
async def test_search_finds_transaction_by_debtor(client, csrf):
    import app.db.yaml_store as ys

    ys.store.create("camt_transactions", {
        "transaction_id": "TX-001", "booking_date": "2024-03-15",
        "value_date": "2024-03-15", "amount": 49.99, "currency": "EUR",
        "credit_debit": "CRDT", "debtor_name": "Erika Mustermann",
        "debtor_iban": None, "remittance_info": None,
        "imported_at": "2024-03-15T10:00:00", "source_file": "bank.xml",
        "match_status": "unmatched", "matched_invoice_id": None,
        "matched_at": None, "match_confidence": None,
    })
    r = await client.get("/search?q=Erika")
    assert r.status_code == 200
    assert "Erika" in r.text


@pytest.mark.asyncio
async def test_search_results_grouped_by_entity(client, csrf):
    """Results are grouped — customer hits appear under a 'Kunden' heading."""
    await client.post("/customers", data=CUSTOMER,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/search?q=Meier")
    assert r.status_code == 200
    assert "Kunden" in r.text
    assert "Meier" in r.text
