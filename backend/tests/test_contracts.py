"""Contract CRUD tests."""
import pytest

CUSTOMER_DATA = {
    "vorname": "Max", "nachname": "Mustermann", "street": "Str.", "house_number": "1",
    "postcode": "12345", "city": "Stadt", "iban": "DE89370400440532013000",
    "email": "max@example.com",
}
PLAN_DATA = {"name": "Basis", "initial_price": "29.99", "valid_from": "2024-01-01"}
CONTRACT_DATA = {
    "customer_id": "1", "plan_id": "1",
    "start_date": "2024-01-01", "billing_cycle": "monthly",
}


async def _setup(client, csrf):
    await client.post("/customers", data=CUSTOMER_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    await client.post("/plans", data=PLAN_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})


@pytest.mark.asyncio
async def test_create_contract(client, csrf):
    await _setup(client, csrf)
    r = await client.post(
        "/contracts", data=CONTRACT_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/contracts"


@pytest.mark.asyncio
async def test_contract_appears_in_list(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/contracts")
    assert "Mustermann" in r.text
    assert "Basis" in r.text


@pytest.mark.asyncio
async def test_contract_filter_by_status(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/contracts?status=active")
    assert "Mustermann" in r.text

    r2 = await client.get("/contracts?status=cancelled")
    assert "Mustermann" not in r2.text


@pytest.mark.asyncio
async def test_contract_validation_missing_billing_cycle(client, csrf):
    await _setup(client, csrf)
    bad = {**CONTRACT_DATA}
    del bad["billing_cycle"]
    r = await client.post(
        "/contracts", data=bad,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    assert "Pflichtfeld" in r.text


@pytest.mark.asyncio
async def test_delete_contract(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.delete(
        "/contracts/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/contracts")
    assert "Mustermann" not in r2.text


@pytest.mark.asyncio
async def test_new_contract_form(client):
    r = await client.get("/contracts/new")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_edit_contract_form(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/contracts/1")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_edit_contract_form_not_found(client):
    r = await client.get("/contracts/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_contract(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.put(
        "/contracts/1", data=CONTRACT_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/contracts"


@pytest.mark.asyncio
async def test_update_contract_validation_error(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.put(
        "/contracts/1",
        data={"customer_id": "1", "plan_id": "1", "start_date": "", "billing_cycle": "monthly"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    assert "Pflichtfeld" in r.text


@pytest.mark.asyncio
async def test_update_contract_not_found(client, csrf):
    r = await client.put(
        "/contracts/999", data=CONTRACT_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_contract_not_found(client, csrf):
    r = await client.delete(
        "/contracts/999",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_contract_with_invoices_returns_409(client, csrf):
    import app.db.yaml_store as ys
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-01-0001", "year": 2024, "month": 1,
        "amount": 29.99, "period_start": "2024-01-01", "period_end": "2024-01-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-01-01T10:00:00", "sent_at": None,
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.delete(
        "/contracts/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_cancel_contract(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.post(
        "/contracts/1/cancel",
        data={"end_date": "2024-06-30"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_cancel_contract_missing_date(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.post(
        "/contracts/1/cancel", data={},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_download_scan_not_found(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/contracts/1/scan")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_download_cancellation_pdf_not_found(client, csrf):
    await _setup(client, csrf)
    await client.post("/contracts", data=CONTRACT_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/contracts/1/cancellation-pdf")
    assert r.status_code == 404
