"""Tests for dashboard overdue count."""
import pytest


@pytest.mark.asyncio
async def test_dashboard_overdue_count_includes_sent_past_due(client):
    import app.db.yaml_store as ys
    # Invoice sent 60 days ago, payment terms typically 14-30 days → overdue
    ys.store.create("invoices", {
        "id": 1, "contract_id": 1, "customer_id": 1,
        "invoice_number": "2026-02-0001", "year": 2026, "month": 2,
        "amount": 119.00, "period_start": "2026-02-01", "period_end": "2026-02-28",
        "status": "sent", "created_at": "2026-02-01T10:00:00",
        "sent_at": "2026-02-01T10:00:00",
    })
    r = await client.get("/")
    # The danger class is only applied when overdue_count > 0
    assert "stat-card__value--danger" in r.text
