from datetime import date, datetime

from fastapi import APIRouter

from app.config import get_config
from app.db.yaml_store import store
from app.models.invoice import Invoice, InvoiceStatus

router = APIRouter()


@router.get("")
def get_dashboard():
    config = get_config()
    today = date.today()
    payment_terms = config.invoice.payment_terms_days

    all_invoices = [Invoice(**d) for d in store.load("invoices")]
    drafts = [i for i in all_invoices if i.status == InvoiceStatus.draft]

    enriched = []
    for inv in drafts:
        customer_d = store.get_by_id("customers", inv.customer_id)
        contract_d = store.get_by_id("contracts", inv.contract_id)
        plan_name = ""
        if contract_d:
            plan_d = store.get_by_id("plans", contract_d["plan_id"])
            plan_name = plan_d["name"] if plan_d else ""

        created = datetime.fromisoformat(inv.created_at.isoformat() if hasattr(inv.created_at, 'isoformat') else inv.created_at)
        due_date = date(created.year, created.month, created.day)
        from datetime import timedelta
        due_date = due_date + timedelta(days=payment_terms)
        overdue = due_date < today

        enriched.append({
            **inv.model_dump(mode="json"),
            "customer_name": f"{customer_d['vorname']} {customer_d['nachname']}" if customer_d else "Unbekannt",
            "plan_name": plan_name,
            "due_date": due_date.isoformat(),
            "overdue": overdue,
        })

    overdue_count = sum(1 for e in enriched if e["overdue"])

    return {
        "draft_count": len(drafts),
        "overdue_count": overdue_count,
        "draft_invoices": enriched,
    }
