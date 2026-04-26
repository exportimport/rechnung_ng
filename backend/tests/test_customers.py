"""Customer CRUD tests."""
import pytest

CUSTOMER_DATA = {
    "vorname": "Max",
    "nachname": "Mustermann",
    "street": "Musterstraße",
    "house_number": "1",
    "postcode": "12345",
    "city": "Musterstadt",
    "iban": "DE89370400440532013000",
    "email": "max@example.com",
}


@pytest.mark.asyncio
async def test_create_customer(client, csrf):
    r = await client.post(
        "/customers",
        data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/customers"


@pytest.mark.asyncio
async def test_customer_appears_in_list(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/customers")
    assert "Max" in r.text
    assert "Mustermann" in r.text


@pytest.mark.asyncio
async def test_customer_search(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/customers?q=muster")
    assert "Mustermann" in r.text

    r2 = await client.get("/customers?q=zzznomatch")
    assert "Mustermann" not in r2.text


@pytest.mark.asyncio
async def test_create_customer_validation_error(client, csrf):
    r = await client.post(
        "/customers",
        data={"vorname": "", "nachname": "Test"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    assert "Pflichtfeld" in r.text


@pytest.mark.asyncio
async def test_edit_customer_form(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/customers/1")
    assert r.status_code == 200
    assert "Speichern" in r.text
    assert "Max" in r.text


@pytest.mark.asyncio
async def test_update_customer(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    updated = {**CUSTOMER_DATA, "vorname": "Hans"}
    r = await client.put(
        "/customers/1", data=updated,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/customers")
    assert "Hans" in r2.text


@pytest.mark.asyncio
async def test_delete_customer(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.delete(
        "/customers/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/customers")
    assert "Mustermann" not in r2.text


@pytest.mark.asyncio
async def test_customer_not_found(client):
    r = await client.get("/customers/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_customer_list_has_zahlungsdaten_link(client, csrf):
    await client.post(
        "/customers", data=CUSTOMER_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/customers")
    assert "/reconciliation/customers/1" in r.text


@pytest.mark.asyncio
async def test_statement_returns_200(client, csrf):
    """GET /customers/{id}/statement returns a page."""
    await client.post("/customers", data=CUSTOMER_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/customers/1/statement")
    assert r.status_code == 200
    assert "Mustermann" in r.text


@pytest.mark.asyncio
async def test_statement_shows_invoice_and_balance(client, csrf):
    """Statement lists invoices and shows a running balance."""
    import app.db.yaml_store as ys

    await client.post("/customers", data=CUSTOMER_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    ys.store.create("invoices", {
        "id": 10, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-03-0001", "year": 2024, "month": 3,
        "amount": 49.99, "period_start": "2024-03-01", "period_end": "2024-03-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-03-01T10:00:00", "sent_at": "2024-03-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.get("/customers/1/statement")
    assert r.status_code == 200
    assert "1-1-2024-03-0001" in r.text
    assert "49" in r.text


@pytest.mark.asyncio
async def test_statement_link_shown_in_customer_list(client, csrf):
    """Customer list row must include a link to the statement page."""
    await client.post("/customers", data=CUSTOMER_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/customers")
    assert "/customers/1/statement" in r.text
