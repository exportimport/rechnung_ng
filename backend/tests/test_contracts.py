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
