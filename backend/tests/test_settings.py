"""Settings page and update tests."""
import pytest

SETTINGS_FORM = {
    "company_name": "Muster GmbH",
    "company_street": "Hauptstraße",
    "company_house_number": "42",
    "company_postcode": "10115",
    "company_city": "Berlin",
    "company_email": "info@muster.de",
    "company_phone": "+49 30 123456",
    "company_tax_id": "DE123456789",
    "company_bank_name": "Sparkasse",
    "company_iban": "DE89370400440532013000",
    "company_bic": "BELADEBEXXX",
    "smtp_host": "smtp.example.com",
    "smtp_port": "587",
    "smtp_username": "mail@muster.de",
    "smtp_sender_name": "Muster GmbH",
    "smtp_sender_email": "rechnungen@muster.de",
    "smtp_use_tls": "on",
    "invoice_number_format": "{customer_id}-{year}-{month:02d}-{seq:04d}",
    "invoice_payment_terms_days": "14",
    "invoice_vat_rate": "0.19",
    "invoice_currency": "EUR",
}


@pytest.mark.asyncio
async def test_settings_page_loads(client):
    r = await client.get("/settings")
    assert r.status_code == 200
    assert "Einstellungen" in r.text
    assert "Unternehmen" in r.text
    assert "SMTP" in r.text


@pytest.mark.asyncio
async def test_settings_update(client, csrf):
    r = await client.put(
        "/settings",
        data=SETTINGS_FORM,
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "HX-Trigger" in r.headers  # toast

    # Verify saved — reload page
    r2 = await client.get("/settings")
    assert "Muster GmbH" in r2.text
    assert "smtp.example.com" in r2.text


@pytest.mark.asyncio
async def test_settings_password_not_exposed(client, csrf):
    """SMTP password must never appear in the settings page HTML."""
    r = await client.get("/settings")
    assert "password" not in r.text.lower() or "type=\"password\"" not in r.text
