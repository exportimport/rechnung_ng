"""Invoice tests — uses made-up but realistic data."""
import pytest

# Shared setup data
CUSTOMER = {
    "vorname": "Anna", "nachname": "Schmidt",
    "street": "Berliner Str.", "house_number": "12",
    "postcode": "10115", "city": "Berlin",
    "iban": "DE89370400440532013000", "email": "anna@example.com",
}
PLAN = {"name": "Internet 100", "initial_price": "49.99", "valid_from": "2024-01-01"}
CONTRACT = {
    "customer_id": "1", "plan_id": "1", "start_date": "2024-01-01", "billing_cycle": "monthly"
}


async def _seed(client, csrf):
    await client.post("/customers", data=CUSTOMER,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    await client.post("/plans", data=PLAN,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    await client.post("/contracts", data=CONTRACT,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})


@pytest.mark.asyncio
async def test_invoices_page_empty(client):
    r = await client.get("/invoices")
    assert r.status_code == 200
    assert "Rechnungen" in r.text


@pytest.mark.asyncio
async def test_invoices_filter_year_month(client, csrf):
    await _seed(client, csrf)
    r = await client.get("/invoices?year=2024&month=1")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_generate_invoices_sse(client, csrf):
    await _seed(client, csrf)
    r = await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "3"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    body = r.text
    assert "event: done" in body or "event: progress" in body or "Fertig" in body


@pytest.mark.asyncio
async def test_generate_then_list(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "3"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/invoices?year=2024&month=3")
    assert r.status_code == 200
    assert "Schmidt" in r.text
    assert "Internet 100" in r.text


@pytest.mark.asyncio
async def test_generate_missing_params(client, csrf):
    r = await client.post(
        "/invoices/generate",
        data={"year": "0", "month": "0"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_draft_invoice(client, csrf):
    await _seed(client, csrf)
    # Generate first
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "4"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    # Delete invoice id=1
    r = await client.delete(
        "/invoices/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200

    r2 = await client.get("/invoices?year=2024&month=4")
    assert "Schmidt" not in r2.text


@pytest.mark.asyncio
async def test_bulk_delete(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "5"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.post(
        "/invoices/bulk-delete",
        data={"ids": "1"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/invoices"


@pytest.mark.asyncio
async def test_pdf_download(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "6"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/invoices/1/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_invoice_not_found(client):
    r = await client.get("/invoices/999/pdf")
    assert r.status_code == 404
