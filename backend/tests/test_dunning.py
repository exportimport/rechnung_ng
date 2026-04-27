"""Dunning (Mahnwesen) tests."""
import pytest


def _seed_sent_invoice(store, inv_id=1):
    store.create("invoices", {
        "id": inv_id,
        "contract_id": 1, "customer_id": 1,
        "invoice_number": f"1-1-2024-01-000{inv_id}",
        "year": 2024, "month": 1,
        "amount": 49.99,
        "period_start": "2024-01-01", "period_end": "2024-01-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-01-01T10:00:00", "sent_at": "2024-01-05T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })


@pytest.mark.asyncio
async def test_remind_increments_dunning_level(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    r = await client.post(
        "/invoices/1/remind",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    r2 = await client.get("/invoices/1")
    assert "Mahnung 1" in r2.text


@pytest.mark.asyncio
async def test_remind_twice_increments_to_level_2(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    await client.post("/invoices/1/remind",
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.post("/invoices/1/remind",
                          headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    assert r.status_code == 200
    r2 = await client.get("/invoices/1")
    assert "Mahnung 2" in r2.text


@pytest.mark.asyncio
async def test_remind_only_allowed_on_sent_invoice(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("invoices", {
        "id": 2, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-01-0002", "year": 2024, "month": 1,
        "amount": 49.99, "period_start": "2024-01-01", "period_end": "2024-01-31",
        "status": "draft", "pdf_path": None, "mail_template": None,
        "created_at": "2024-01-01T10:00:00", "sent_at": None,
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.post(
        "/invoices/2/remind",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_overdue_invoice_shown_in_list(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    await client.post("/invoices/1/remind",
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    r = await client.get("/invoices?year=2024&month=1")
    assert "mahnung" in r.text.lower()


@pytest.mark.asyncio
async def test_remind_sets_last_reminded_at(client, csrf):
    from datetime import date
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    await client.post("/invoices/1/remind",
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    d = ys.store.get_by_id("invoices", 1)
    assert d.get("last_reminded_at") == date.today().isoformat()


@pytest.mark.asyncio
async def test_mahnen_button_shown_for_sent_invoice(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    r = await client.get("/invoices?year=2024&month=1")
    assert "Mahnen" in r.text


@pytest.mark.asyncio
async def test_invoice_detail_shows_invoice_info(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    r = await client.get("/invoices/1")
    assert r.status_code == 200
    assert "1-1-2024-01-0001" in r.text


@pytest.mark.asyncio
async def test_invoice_detail_full_page_has_sidebar(client, csrf):
    import app.db.yaml_store as ys
    _seed_sent_invoice(ys.store)
    r = await client.get("/invoices/1")
    assert "sidebar" in r.text
