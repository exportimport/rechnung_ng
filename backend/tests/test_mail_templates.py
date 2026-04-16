"""Mail template tests."""

import pytest
import yaml


@pytest.fixture(autouse=True)
def seed_mail_templates():
    """Seed mail_templates.yaml before each test in this module."""
    from app.db.yaml_store import store
    data = [
        {
            "id": "default",
            "name": "Standard",
            "subject": "Rechnung {{ invoice.invoice_number }}",
            "body": "Hallo {{ customer.vorname }}, anbei Ihre Rechnung.",
        },
        {
            "id": "new_customer",
            "name": "Neukunde",
            "subject": "Willkommen – {{ invoice.invoice_number }}",
            "body": "Willkommen {{ customer.vorname }}!",
        },
    ]
    p = store.data_dir / "mail_templates.yaml"
    p.write_text(yaml.dump(data, allow_unicode=True))


@pytest.mark.asyncio
async def test_mail_templates_page(client):
    r = await client.get("/mail-templates")
    assert r.status_code == 200
    assert "Mail-Vorlagen" in r.text
    assert "Standard" in r.text
    assert "Neukunde" in r.text


@pytest.mark.asyncio
async def test_update_template(client, csrf):
    r = await client.put(
        "/mail-templates/default",
        data={
            "subject": "Ihre Rechnung Nr. {{ invoice.invoice_number }}",
            "body": (
                "Sehr geehrte/r {{ customer.vorname }} {{ customer.nachname }},"
                "\nanbei Ihre Rechnung."
            ),
        },
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "HX-Trigger" in r.headers
    assert "Ihre Rechnung" in r.text


@pytest.mark.asyncio
async def test_update_template_invalid_jinja(client, csrf):
    r = await client.put(
        "/mail-templates/default",
        data={
            "subject": "{{ unclosed",
            "body": "valid body",
        },
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    assert "Ungültiges Template" in r.text


@pytest.mark.asyncio
async def test_template_not_found(client, csrf):
    r = await client.put(
        "/mail-templates/nonexistent",
        data={"subject": "x", "body": "x"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404
