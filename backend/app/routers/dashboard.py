from datetime import date, datetime, timedelta

from fastapi import APIRouter, Request

from app.db.yaml_store import store
from app.models.invoice import Invoice, InvoiceStatus

router = APIRouter()


def _to_date(d: date | datetime) -> date:
    return d.date() if isinstance(d, datetime) else d


def _dashboard_context() -> dict:
    from app.config import get_config

    config = get_config()
    today = date.today()
    payment_terms = config.invoice.payment_terms_days

    all_invoices = [Invoice(**d) for d in store.load("invoices")]
    drafts = [i for i in all_invoices if i.status == InvoiceStatus.draft]

    customers = {c["id"]: c for c in store.load("customers")}
    contracts = {c["id"]: c for c in store.load("contracts")}
    plans = {p["id"]: p for p in store.load("plans")}

    enriched = []
    for inv in drafts:
        customer_d = customers.get(inv.customer_id)
        contract_d = contracts.get(inv.contract_id)
        plan_name = ""
        if contract_d:
            plan_d = plans.get(contract_d["plan_id"])
            plan_name = plan_d["name"] if plan_d else ""

        created = _to_date(inv.created_at)
        due_date = created + timedelta(days=payment_terms)
        overdue = due_date < today

        enriched.append({
            **inv.model_dump(mode="json"),
            "customer_name": (
                f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt"
            ),
            "plan_name": plan_name,
            "due_date": due_date,
            "overdue": overdue,
        })

    enriched.sort(key=lambda x: x["created_at"])

    from app.services.reconciliation import effective_status
    overdue_count = sum(
        1 for inv in all_invoices
        if effective_status(inv, today, payment_terms) == "overdue"
    )

    sent = [i for i in all_invoices if i.status == InvoiceStatus.sent]

    last_month = today.month - 1 or 12
    last_month_year = today.year if today.month > 1 else today.year - 1
    last_month_revenue = sum(
        i.amount for i in sent
        if i.period_start.month == last_month and i.period_start.year == last_month_year
    )

    current_quarter = (today.month - 1) // 3
    last_quarter = current_quarter or 4
    last_quarter_year = today.year if current_quarter > 0 else today.year - 1
    last_quarter_months = {
        (last_quarter - 1) * 3 + 1,
        (last_quarter - 1) * 3 + 2,
        (last_quarter - 1) * 3 + 3,
    }
    last_quarter_revenue = sum(
        i.amount for i in sent
        if i.period_start.month in last_quarter_months and i.period_start.year == last_quarter_year
    )

    return {
        "active_page": "dashboard",
        "draft_count": len(drafts),
        "overdue_count": overdue_count,
        "customer_count": len(customers),
        "last_month_revenue": last_month_revenue,
        "last_quarter_revenue": last_quarter_revenue,
        "draft_invoices": enriched,
    }


@router.get("/")
def dashboard(request: Request):
    from app.main import render

    ctx = _dashboard_context()
    return render(request, "base.html.j2", "fragments/dashboard_stats.html.j2", ctx)
