"""Plan CRUD tests."""
import pytest

PLAN_DATA = {
    "name": "Basis",
    "initial_price": "29.99",
    "valid_from": "2024-01-01",
}


@pytest.mark.asyncio
async def test_create_plan(client, csrf):
    r = await client.post(
        "/plans", data=PLAN_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/plans"


@pytest.mark.asyncio
async def test_plan_appears_in_list(client, csrf):
    await client.post(
        "/plans", data=PLAN_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/plans")
    assert "Basis" in r.text


@pytest.mark.asyncio
async def test_plan_validation_error(client, csrf):
    r = await client.post(
        "/plans", data={"name": "", "initial_price": "10", "valid_from": "2024-01-01"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    assert "Pflichtfeld" in r.text


@pytest.mark.asyncio
async def test_update_plan(client, csrf):
    await client.post(
        "/plans", data=PLAN_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.put(
        "/plans/1", data={"name": "Premium"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/plans")
    assert "Premium" in r2.text


@pytest.mark.asyncio
async def test_add_price_to_plan(client, csrf):
    await client.post(
        "/plans", data=PLAN_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.post(
        "/plans/1/price",
        data={"amount": "39.99", "valid_from": "2025-01-01"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "39" in r.text


@pytest.mark.asyncio
async def test_edit_plan_form(client, csrf):
    await client.post("/plans", data=PLAN_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/plans/1")
    assert r.status_code == 200
    assert "Basis" in r.text


@pytest.mark.asyncio
async def test_edit_plan_form_not_found(client):
    r = await client.get("/plans/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_plan_invalid_price(client, csrf):
    r = await client.post(
        "/plans", data={"name": "X", "initial_price": "abc", "valid_from": "2024-01-01"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_plan_not_found(client, csrf):
    r = await client.put(
        "/plans/999", data={"name": "X"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_price_validation_error(client, csrf):
    await client.post("/plans", data=PLAN_DATA,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.post(
        "/plans/1/price", data={"amount": "", "valid_from": ""},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_plan_not_found(client, csrf):
    r = await client.delete(
        "/plans/999",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_plan(client, csrf):
    await client.post(
        "/plans", data=PLAN_DATA,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.delete(
        "/plans/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/plans")
    assert "Basis" not in r2.text
