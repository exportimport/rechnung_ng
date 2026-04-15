"""Smoke tests: all pages return 200 with correct HTML."""
import pytest


@pytest.mark.asyncio
async def test_dashboard(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "Dashboard" in r.text
    assert "<!DOCTYPE html>" in r.text


@pytest.mark.asyncio
async def test_dashboard_htmx_fragment(client):
    r = await client.get("/", headers={"HX-Request": "true", "X-CSRF-Token": "x"})
    assert r.status_code == 200
    assert "<!DOCTYPE html>" not in r.text
    assert "page-title" in r.text


@pytest.mark.asyncio
async def test_customers_page(client):
    r = await client.get("/customers")
    assert r.status_code == 200
    assert "Kunden" in r.text


@pytest.mark.asyncio
async def test_customers_new_form(client):
    r = await client.get("/customers/new")
    assert r.status_code == 200
    assert "Neuer Kunde" in r.text


@pytest.mark.asyncio
async def test_plans_page(client):
    r = await client.get("/plans")
    assert r.status_code == 200
    assert "Tarife" in r.text


@pytest.mark.asyncio
async def test_plans_new_form(client):
    r = await client.get("/plans/new")
    assert r.status_code == 200
    assert "Neuer Tarif" in r.text


@pytest.mark.asyncio
async def test_contracts_page(client):
    r = await client.get("/contracts")
    assert r.status_code == 200
    assert "Vertr" in r.text  # Verträge


@pytest.mark.asyncio
async def test_invoices_page(client):
    r = await client.get("/invoices")
    assert r.status_code == 200
    assert "Rechnungen" in r.text


@pytest.mark.asyncio
async def test_settings_page(client):
    r = await client.get("/settings")
    assert r.status_code == 200
    assert "Einstellungen" in r.text


@pytest.mark.asyncio
async def test_mail_templates_page(client):
    r = await client.get("/mail-templates")
    assert r.status_code == 200
    assert "Mail-Vorlagen" in r.text


@pytest.mark.asyncio
async def test_csrf_rejects_post_without_token(client):
    r = await client.post("/customers", data={"vorname": "Max"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_static_htmx_js(client):
    r = await client.get("/static/js/htmx.min.js")
    assert r.status_code == 200
    assert len(r.content) > 10_000


@pytest.mark.asyncio
async def test_static_css(client):
    r = await client.get("/static/css/style.css")
    assert r.status_code == 200
