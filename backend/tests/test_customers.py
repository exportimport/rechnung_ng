from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.yaml_store import YamlStore
from app.main import app

SAMPLE = {
    "vorname": "Max",
    "nachname": "Mustermann",
    "adresse": "Musterstraße 1\n04103 Leipzig",
    "iban": "DE89370400440532013000",
    "email": "max@example.com",
}


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    import app.routers.customers as customers_router
    import app.db.yaml_store as yaml_store_module

    tmp_store = YamlStore(tmp_path)
    yaml_store_module.store = tmp_store
    customers_router.store = tmp_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    from app.db.yaml_store import _default_data_dir
    yaml_store_module.store = YamlStore(_default_data_dir)
    customers_router.store = yaml_store_module.store


async def test_list_empty(client: AsyncClient):
    res = await client.get("/api/v1/customers")
    assert res.status_code == 200
    assert res.json() == []


async def test_create_and_get(client: AsyncClient):
    res = await client.post("/api/v1/customers", json=SAMPLE)
    assert res.status_code == 201
    data = res.json()
    assert data["vorname"] == "Max"
    assert data["id"] == 1

    res2 = await client.get(f"/api/v1/customers/{data['id']}")
    assert res2.status_code == 200


async def test_search(client: AsyncClient):
    await client.post("/api/v1/customers", json=SAMPLE)
    await client.post(
        "/api/v1/customers",
        json={**SAMPLE, "vorname": "Erika", "nachname": "Musterfrau", "email": "erika@example.com"},
    )
    res = await client.get("/api/v1/customers?q=erika")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["vorname"] == "Erika"


async def test_update(client: AsyncClient):
    create_res = await client.post("/api/v1/customers", json=SAMPLE)
    cid = create_res.json()["id"]
    res = await client.put(f"/api/v1/customers/{cid}", json={**SAMPLE, "vorname": "Heinrich"})
    assert res.status_code == 200
    assert res.json()["vorname"] == "Heinrich"


async def test_delete(client: AsyncClient):
    create_res = await client.post("/api/v1/customers", json=SAMPLE)
    cid = create_res.json()["id"]
    res = await client.delete(f"/api/v1/customers/{cid}")
    assert res.status_code == 204
    assert (await client.get(f"/api/v1/customers/{cid}")).status_code == 404


async def test_delete_with_contract_blocked(client: AsyncClient, tmp_path: Path):
    import app.db.yaml_store as m
    create_res = await client.post("/api/v1/customers", json=SAMPLE)
    cid = create_res.json()["id"]
    m.store.create("contracts", {"customer_id": cid, "plan_id": 1})
    res = await client.delete(f"/api/v1/customers/{cid}")
    assert res.status_code == 409


async def test_get_nonexistent(client: AsyncClient):
    res = await client.get("/api/v1/customers/999")
    assert res.status_code == 404
