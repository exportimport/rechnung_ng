from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.yaml_store import YamlStore
from app.main import app
from app.models.contract import BillingCycle
from app.models.plan import Plan, current_price
from app.services.invoice_generator import _next_seq, _period_end_quarterly, generate_invoices

CUSTOMER = {
    "vorname": "Max",
    "nachname": "Mustermann",
    "street": "Straße",
    "house_number": "1",
    "postcode": "04103",
    "city": "Leipzig",
    "iban": "DE89370400440532013000",
    "email": "max@example.com",
}


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    import app.routers.contracts as cr
    import app.routers.customers as cust_r
    import app.routers.plans as pr
    import app.routers.invoices as inv_r
    import app.db.yaml_store as m
    import app.services.invoice_generator as gen_mod

    tmp_store = YamlStore(tmp_path)
    m.store = cr.store = cust_r.store = pr.store = inv_r.store = tmp_store
    gen_mod.OUTPUT_DIR = tmp_path / "output"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    from app.db.yaml_store import _default_data_dir
    import app.services.invoice_generator as gm
    restored = YamlStore(_default_data_dir)
    m.store = cr.store = cust_r.store = pr.store = inv_r.store = restored
    gm.OUTPUT_DIR = Path(__file__).parent.parent / "output"


async def _seed(client: AsyncClient, start="2026-01-01"):
    c = await client.post("/api/v1/customers", json=CUSTOMER)
    p = await client.post(
        "/api/v1/plans",
        json={"name": "Basic", "initial_price": "19.99", "valid_from": "2026-01-01"},
    )
    ct = await client.post(
        "/api/v1/contracts",
        json={
            "customer_id": c.json()["id"],
            "plan_id": p.json()["id"],
            "start_date": start,
            "billing_cycle": "monthly",
        },
    )
    return c.json(), p.json(), ct.json()


def test_quarterly_period_end():
    assert _period_end_quarterly(2026, 1) == date(2026, 3, 31)
    assert _period_end_quarterly(2026, 10) == date(2026, 12, 31)
    assert _period_end_quarterly(2026, 7) == date(2026, 9, 30)


def test_next_seq_empty():
    assert _next_seq([], 2026, 4) == 1


def test_next_seq_existing():
    inv = [
        {"year": 2026, "month": 4, "invoice_number": "1-1-2026-04-0001"},
        {"year": 2026, "month": 4, "invoice_number": "2-2-2026-04-0002"},
    ]
    assert _next_seq(inv, 2026, 4) == 3
    assert _next_seq(inv, 2026, 5) == 1


def test_current_price_selection():
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


@patch("app.services.invoice_generator.render_invoice_pdf")
async def test_generate_basic(mock_render: MagicMock, client: AsyncClient, tmp_path: Path):
    mock_render.return_value = tmp_path / "output" / "invoices" / "test.pdf"
    await _seed(client)

    res = await client.post("/api/v1/invoices/generate", json={"year": 2026, "month": 4})
    assert res.status_code == 201
    data = res.json()
    assert len(data) == 1
    assert data[0]["invoice_number"].startswith("1-1-2026-04-")
    assert data[0]["status"] == "draft"
    assert data[0]["amount"] == pytest.approx(19.99, rel=1e-3)


@patch("app.services.invoice_generator.render_invoice_pdf")
async def test_generate_skips_existing(mock_render: MagicMock, client: AsyncClient, tmp_path: Path):
    mock_render.return_value = tmp_path / "output" / "invoices" / "test.pdf"
    await _seed(client)

    await client.post("/api/v1/invoices/generate", json={"year": 2026, "month": 4})
    res2 = await client.post("/api/v1/invoices/generate", json={"year": 2026, "month": 4})
    assert len(res2.json()) == 0


@patch("app.services.invoice_generator.render_invoice_pdf")
async def test_quarterly_only_in_quarter_start(mock_render: MagicMock, client: AsyncClient, tmp_path: Path):
    mock_render.return_value = tmp_path / "output" / "invoices" / "test.pdf"
    c = await client.post("/api/v1/customers", json=CUSTOMER)
    p = await client.post(
        "/api/v1/plans",
        json={"name": "Q", "initial_price": "50.00", "valid_from": "2026-01-01"},
    )
    await client.post(
        "/api/v1/contracts",
        json={
            "customer_id": c.json()["id"],
            "plan_id": p.json()["id"],
            "start_date": "2026-01-01",
            "billing_cycle": "quarterly",
        },
    )
    # February — should produce nothing
    res_feb = await client.post("/api/v1/invoices/generate", json={"year": 2026, "month": 2})
    assert len(res_feb.json()) == 0

    # April — quarter start — should generate with amount × 3
    res_apr = await client.post("/api/v1/invoices/generate", json={"year": 2026, "month": 4})
    assert len(res_apr.json()) == 1
    assert res_apr.json()[0]["amount"] == pytest.approx(150.0, rel=1e-3)
