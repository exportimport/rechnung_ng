from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.yaml_store import YamlStore
from app.main import app


@pytest.fixture
def tmp_store(tmp_path: Path):
    s = YamlStore(tmp_path)
    return s


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    import app.routers.plans as plans_router
    import app.db.yaml_store as yaml_store_module

    tmp_store = YamlStore(tmp_path)
    original = yaml_store_module.store
    yaml_store_module.store = tmp_store
    plans_router.store = tmp_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    yaml_store_module.store = original
    plans_router.store = original


async def test_list_plans_empty(client: AsyncClient):
    res = await client.get("/api/v1/plans")
    assert res.status_code == 200
    assert res.json() == []


async def test_create_and_get_plan(client: AsyncClient):
    res = await client.post(
        "/api/v1/plans",
        json={"name": "Basic", "initial_price": "19.99", "valid_from": "2026-01-01"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Basic"
    assert len(data["price_history"]) == 1

    res2 = await client.get(f"/api/v1/plans/{data['id']}")
    assert res2.status_code == 200
    assert res2.json()["name"] == "Basic"


async def test_update_plan_name(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/plans",
        json={"name": "Old Name", "initial_price": "10.00", "valid_from": "2026-01-01"},
    )
    plan_id = create_res.json()["id"]
    res = await client.put(f"/api/v1/plans/{plan_id}", json={"name": "New Name"})
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


async def test_add_price(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/plans",
        json={"name": "Growing", "initial_price": "10.00", "valid_from": "2026-01-01"},
    )
    plan_id = create_res.json()["id"]
    res = await client.post(
        f"/api/v1/plans/{plan_id}/price",
        json={"amount": "12.00", "valid_from": "2026-07-01"},
    )
    assert res.status_code == 200
    history = res.json()["price_history"]
    assert len(history) == 2
    assert history[1]["amount"] == "12.00"


async def test_delete_plan(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/plans",
        json={"name": "ToDelete", "initial_price": "5.00", "valid_from": "2026-01-01"},
    )
    plan_id = create_res.json()["id"]
    res = await client.delete(f"/api/v1/plans/{plan_id}")
    assert res.status_code == 204
    assert (await client.get(f"/api/v1/plans/{plan_id}")).status_code == 404


async def test_get_nonexistent_plan(client: AsyncClient):
    res = await client.get("/api/v1/plans/999")
    assert res.status_code == 404


async def test_current_price_computed():
    from app.models.plan import Plan, current_price

    plan = Plan(
        id=1,
        name="Test",
        price_history=[
            {"amount": "10.00", "valid_from": date(2026, 1, 1)},
            {"amount": "12.00", "valid_from": date(2026, 7, 1)},
        ],
    )
    assert current_price(plan, date(2026, 6, 30)) == 10
    assert current_price(plan, date(2026, 7, 1)) == 12
    assert current_price(plan, date(2025, 12, 31)) is None
