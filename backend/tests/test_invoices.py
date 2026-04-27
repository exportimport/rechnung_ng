"""Invoice tests — uses made-up but realistic data."""
import pytest

# Shared setup data
CUSTOMER = {
    "vorname": "Anna", "nachname": "Schmidt",
    "street": "Berliner Str.", "house_number": "12",
    "postcode": "10115", "city": "Berlin",
    "iban": "DE89370400440532013000", "email": "anna@example.com",
}
PLAN = {"name": "Internet 100", "initial_price": "49.99", "valid_from": "2024-01-01"}
CONTRACT = {
    "customer_id": "1", "plan_id": "1", "start_date": "2024-01-01", "billing_cycle": "monthly"
}


async def _seed(client, csrf):
    await client.post("/customers", data=CUSTOMER,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    await client.post("/plans", data=PLAN,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})
    await client.post("/contracts", data=CONTRACT,
                      headers={"HX-Request": "true", "X-CSRF-Token": csrf})


@pytest.mark.asyncio
async def test_invoices_page_empty(client):
    r = await client.get("/invoices")
    assert r.status_code == 200
    assert "Rechnungen" in r.text


@pytest.mark.asyncio
async def test_invoices_filter_year_month(client, csrf):
    await _seed(client, csrf)
    r = await client.get("/invoices?year=2024&month=1")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_generate_invoices(client, csrf):
    await _seed(client, csrf)
    r = await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "3"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Fertig" in r.text
    assert "HX-Trigger" in r.headers


@pytest.mark.asyncio
async def test_generate_then_list(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "3"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/invoices?year=2024&month=3")
    assert r.status_code == 200
    assert "Schmidt" in r.text
    assert "Internet 100" in r.text


@pytest.mark.asyncio
async def test_generate_missing_params(client, csrf):
    r = await client.post(
        "/invoices/generate",
        data={"year": "0", "month": "0"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_draft_invoice(client, csrf):
    await _seed(client, csrf)
    # Generate first
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "4"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    # Delete invoice id=1
    r = await client.delete(
        "/invoices/1",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200

    r2 = await client.get("/invoices?year=2024&month=4")
    assert "Schmidt" not in r2.text


@pytest.mark.asyncio
async def test_bulk_delete(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "5"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.post(
        "/invoices/bulk-delete",
        data={"ids": "1"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == "/invoices"


@pytest.mark.asyncio
async def test_pdf_download(client, csrf):
    await _seed(client, csrf)
    await client.post(
        "/invoices/generate",
        data={"year": "2024", "month": "6"},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    r = await client.get("/invoices/1/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_invoice_not_found(client):
    r = await client.get("/invoices/999/pdf")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_mark_paid_sets_status_and_paid_at(client, csrf):
    """POST /invoices/{id}/mark-paid must set status=paid and paid_at=today."""
    from datetime import date
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 42, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-03-0001", "year": 2024, "month": 3,
        "amount": 29.99, "period_start": "2024-03-01", "period_end": "2024-03-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-03-01T10:00:00", "sent_at": "2024-03-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.post(
        "/invoices/42/mark-paid",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    updated = ys.store.get_by_id("invoices", 42)
    assert updated["status"] == "paid"
    assert updated["paid_at"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_mark_paid_button_shown_for_sent_invoice(client, csrf):
    """The invoice row must show a 'mark-paid' action for sent invoices."""
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 43, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-04-0001", "year": 2024, "month": 4,
        "amount": 29.99, "period_start": "2024-04-01", "period_end": "2024-04-30",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-04-01T10:00:00", "sent_at": "2024-04-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.get("/invoices?year=2024&month=4")
    assert r.status_code == 200
    assert "mark-paid" in r.text


@pytest.mark.asyncio
async def test_mark_paid_rejected_for_draft(client, csrf):
    """Drafts cannot be marked as paid."""
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 44, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-05-0001", "year": 2024, "month": 5,
        "amount": 29.99, "period_start": "2024-05-01", "period_end": "2024-05-31",
        "status": "draft", "pdf_path": None, "mail_template": None,
        "created_at": "2024-05-01T10:00:00", "sent_at": None,
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.post(
        "/invoices/44/mark-paid",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_paid_invoice_shows_bezahlt_badge(client, csrf):
    """Paid invoices must display badge--paid CSS class, not badge--sent."""
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 45, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-06-0001", "year": 2024, "month": 6,
        "amount": 29.99, "period_start": "2024-06-01", "period_end": "2024-06-30",
        "status": "paid", "pdf_path": None, "mail_template": None,
        "created_at": "2024-06-01T10:00:00", "sent_at": "2024-06-02T09:00:00",
        "paid_at": "2024-06-15", "payment_transaction_id": None,
    })
    r = await client.get("/invoices?year=2024&month=6")
    assert r.status_code == 200
    assert "badge--paid" in r.text
    assert "badge--sent" not in r.text


@pytest.mark.asyncio
async def test_invoice_filter_has_paid_option(client):
    """Status filter dropdown must include a 'Bezahlt' option."""
    r = await client.get("/invoices")
    assert r.status_code == 200
    assert 'value="paid"' in r.text


@pytest.mark.asyncio
async def test_mark_paid_response_shows_bezahlt_badge(client, csrf):
    """The row fragment returned by mark-paid must show badge--paid."""
    import app.db.yaml_store as ys

    ys.store.create("invoices", {
        "id": 46, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-07-0001", "year": 2024, "month": 7,
        "amount": 29.99, "period_start": "2024-07-01", "period_end": "2024-07-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-07-01T10:00:00", "sent_at": "2024-07-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.post(
        "/invoices/46/mark-paid",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert "badge--paid" in r.text


@pytest.mark.asyncio
async def test_delete_invoice_not_found(client, csrf):
    r = await client.delete(
        "/invoices/999",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_sent_invoice_returns_409(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("invoices", {
        "id": 50, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-01-0001", "year": 2024, "month": 1,
        "amount": 29.99, "period_start": "2024-01-01", "period_end": "2024-01-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-01-01T10:00:00", "sent_at": "2024-01-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.delete(
        "/invoices/50",
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_bulk_delete_drafts(client, csrf):
    import app.db.yaml_store as ys
    for i in (51, 52):
        ys.store.create("invoices", {
            "id": i, "contract_id": 1, "customer_id": 1,
            "invoice_number": f"1-1-2024-02-00{i}", "year": 2024, "month": 2,
            "amount": 29.99, "period_start": "2024-02-01", "period_end": "2024-02-28",
            "status": "draft", "pdf_path": None, "mail_template": None,
            "created_at": "2024-02-01T10:00:00", "sent_at": None,
            "paid_at": None, "payment_transaction_id": None,
        })
    r = await client.post(
        "/invoices/bulk-delete",
        data={"ids": ["51", "52"]},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_bulk_delete_non_drafts_returns_409(client, csrf):
    import app.db.yaml_store as ys
    ys.store.create("invoices", {
        "id": 53, "contract_id": 1, "customer_id": 1,
        "invoice_number": "1-1-2024-03-0001", "year": 2024, "month": 3,
        "amount": 29.99, "period_start": "2024-03-01", "period_end": "2024-03-31",
        "status": "sent", "pdf_path": None, "mail_template": None,
        "created_at": "2024-03-01T10:00:00", "sent_at": "2024-03-02T09:00:00",
        "paid_at": None, "payment_transaction_id": None,
    })
    r = await client.post(
        "/invoices/bulk-delete",
        data={"ids": ["53"]},
        headers={"HX-Request": "true", "X-CSRF-Token": csrf},
    )
    assert r.status_code == 409
