"""Unit tests for invoice generation logic — billing cycles, amounts, periods."""
import tempfile
from datetime import date
from pathlib import Path

import pytest
import yaml

from app.db.yaml_store import YamlStore
from app.services.invoice_generator import generate_invoices


def _make_store(customers=None, plans=None, contracts=None):
    tmp = tempfile.mkdtemp()
    s = YamlStore(Path(tmp))
    (Path(tmp) / "config.yaml").write_text(yaml.dump({
        "company": {
            "name": "Test GmbH", "street": "Str.", "house_number": "1",
            "postcode": "12345", "city": "Stadt", "email": "t@t.de",
            "phone": "", "tax_id": "", "bank_name": "", "iban": "", "bic": "",
        },
        "smtp": {
            "host": "localhost", "port": 587, "username": "",
            "use_tls": False, "use_ssl": False,
            "sender_name": "T", "sender_email": "t@t.de",
        },
        "invoice": {
            "number_format": "{customer_id}-{contract_id}-{year}-{month:02d}-{seq:04d}",
            "payment_terms_days": 14, "vat_rate": 0.19, "currency": "EUR",
        },
    }))
    import app.config as cfg
    cfg.get_config.cache_clear()
    cfg.DATA_DIR = Path(tmp)

    s.save("customers", customers or [{
        "id": 1, "vorname": "Max", "nachname": "Muster",
        "street": "Str.", "house_number": "1", "postcode": "10000", "city": "Berlin",
        "iban": "DE00000000000000000000", "email": "max@example.com",
    }])
    s.save("plans", plans or [{
        "id": 1, "name": "Basic",
        "price_history": [{"amount": "30.00", "valid_from": "2023-01-01"}],
    }])
    s.save("contracts", contracts or [])
    s.save("invoices", [])
    return s


def _run(s, year, month):
    """Run generator, return list of new Invoice objects."""
    events = list(generate_invoices(year, month, s))
    done = [e for e in events if e[0] == "done"]
    return done[0][1] if done else []


# ── Monthly billing ────────────────────────────────────────────────────────────

def test_monthly_generates_every_month():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "monthly",
    }])
    for month in range(1, 13):
        s.save("invoices", [])  # reset between runs
        result = _run(s, 2024, month)
        assert len(result) == 1, f"Expected 1 invoice for month {month}, got {len(result)}"


def test_monthly_amount_equals_plan_price():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 3)
    assert len(result) == 1
    assert abs(result[0].amount - 30.00) < 0.001


def test_monthly_period_end_is_last_day_of_month():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 2)  # February 2024 (leap year)
    assert result[0].period_end == date(2024, 2, 29)


# ── Quarterly billing ──────────────────────────────────────────────────────────

QUARTERLY_MONTHS = (1, 4, 7, 10)
NON_QUARTERLY_MONTHS = (2, 3, 5, 6, 8, 9, 11, 12)


@pytest.mark.parametrize("month", QUARTERLY_MONTHS)
def test_quarterly_generates_in_quarter_start_months(month):
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "quarterly",
    }])
    result = _run(s, 2024, month)
    assert len(result) == 1, f"Expected invoice in month {month}"


@pytest.mark.parametrize("month", NON_QUARTERLY_MONTHS)
def test_quarterly_skips_non_quarter_months(month):
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "quarterly",
    }])
    result = _run(s, 2024, month)
    assert len(result) == 0, f"Expected no invoice in month {month}"


def test_quarterly_amount_is_three_times_monthly():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "quarterly",
    }])
    result = _run(s, 2024, 1)
    assert abs(result[0].amount - 90.00) < 0.001  # 3 × 30.00


def test_quarterly_period_spans_three_months():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "quarterly",
    }])
    result = _run(s, 2024, 4)  # April → April–June
    assert result[0].period_start == date(2024, 4, 1)
    assert result[0].period_end == date(2024, 6, 30)


def test_quarterly_period_wraps_year_boundary():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "quarterly",
    }])
    result = _run(s, 2024, 10)  # October → October–December
    assert result[0].period_end == date(2024, 12, 31)


# ── Contract lifecycle ─────────────────────────────────────────────────────────

def test_no_invoice_before_contract_start():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-06-01", "end_date": None,
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 5)  # May — before start
    assert len(result) == 0


def test_invoice_in_start_month():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-06-15", "end_date": None,
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 6)
    assert len(result) == 1


def test_no_invoice_after_contract_end():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": "2024-03-31",
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 4)  # April — after end
    assert len(result) == 0


def test_invoice_in_end_month():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": "2024-03-31",
        "billing_cycle": "monthly",
    }])
    result = _run(s, 2024, 3)  # March — last active month
    assert len(result) == 1


def test_no_duplicate_invoice_same_period():
    s = _make_store(contracts=[{
        "id": 1, "customer_id": 1, "plan_id": 1,
        "start_date": "2024-01-01", "end_date": None,
        "billing_cycle": "monthly",
    }])
    _run(s, 2024, 1)
    result = _run(s, 2024, 1)  # second run same month
    assert len(result) == 0
