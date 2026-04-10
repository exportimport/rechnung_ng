from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.yaml_store import YamlStore
from app.main import app

CUSTOMER = {
    "vorname": "Max",
    "nachname": "Mustermann",
    "adresse": "Straße 1\n04103 Leipzig",
    "iban": "DE89370400440532013000",
    "email": "max@example.com",
}
PLAN_DATA = {"name": "Basic", "initial_price": "19.99", "valid_from": "2026-01-01"}


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    import app.routers.contracts as contracts_router
    import app.routers.customers as customers_router
    import app.routers.plans as plans_router
    import app.db.yaml_store as m

    tmp_store = YamlStore(tmp_path)
    m.store = tmp_store
    contracts_router.store = tmp_store
    customers_router.store = tmp_store
    plans_router.store = tmp_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    from app.db.yaml_store import _default_data_dir
    restored = YamlStore(_default_data_dir)
    m.store = restored
    contracts_router.store = restored
    customers_router.store = restored
    plans_router.store = restored


async def _seed(client: AsyncClient):
    c = await client.post("/api/v1/customers", json=CUSTOMER)
    p = await client.post("/api/v1/plans", json=PLAN_DATA)
    return c.json()["id"], p.json()["id"]


async def test_create_contract(client: AsyncClient):
    cid, pid = await _seed(client)
    res = await client.post(
        "/api/v1/contracts",
        json={"customer_id": cid, "plan_id": pid, "start_date": "2026-01-01", "billing_cycle": "monthly"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "active"
    assert data["customer_name"] == "Max Mustermann"
    assert data["plan_name"] == "Basic"


async def test_contract_status_not_yet_active(client: AsyncClient):
    cid, pid = await _seed(client)
    res = await client.post(
        "/api/v1/contracts",
        json={"customer_id": cid, "plan_id": pid, "start_date": "2099-01-01", "billing_cycle": "monthly"},
    )
    assert res.json()["status"] == "not_yet_active"


async def test_contract_status_cancelled(client: AsyncClient):
    cid, pid = await _seed(client)
    res = await client.post(
        "/api/v1/contracts",
        json={
            "customer_id": cid,
            "plan_id": pid,
            "start_date": "2020-01-01",
            "end_date": "2021-01-01",
            "billing_cycle": "monthly",
        },
    )
    assert res.json()["status"] == "cancelled"


async def test_cancel_contract(client: AsyncClient):
    cid, pid = await _seed(client)
    create_res = await client.post(
        "/api/v1/contracts",
        json={"customer_id": cid, "plan_id": pid, "start_date": "2026-01-01", "billing_cycle": "monthly"},
    )
    contract_id = create_res.json()["id"]
    res = await client.post(
        f"/api/v1/contracts/{contract_id}/cancel", json={"end_date": "2020-01-01"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


async def test_filter_by_status(client: AsyncClient):
    cid, pid = await _seed(client)
    await client.post(
        "/api/v1/contracts",
        json={"customer_id": cid, "plan_id": pid, "start_date": "2026-01-01", "billing_cycle": "monthly"},
    )
    await client.post(
        "/api/v1/contracts",
        json={"customer_id": cid, "plan_id": pid, "start_date": "2099-01-01", "billing_cycle": "monthly"},
    )
    res = await client.get("/api/v1/contracts?status=active")
    assert all(c["status"] == "active" for c in res.json())


async def test_create_contract_invalid_customer(client: AsyncClient):
    _, pid = await _seed(client)
    res = await client.post(
        "/api/v1/contracts",
        json={"customer_id": 999, "plan_id": pid, "start_date": "2026-01-01", "billing_cycle": "monthly"},
    )
    assert res.status_code == 404
