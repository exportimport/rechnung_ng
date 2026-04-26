from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.db.yaml_store import store

router = APIRouter()


@router.get("/search")
def search(request: Request, q: str = ""):
    q = q.strip()
    customers = []
    if len(q) >= 2:
        q_lower = q.lower()
        for c in store.load("customers"):
            name = f"{c.get('vorname', '')} {c.get('nachname', '')}".lower()
            if q_lower in name or q_lower in c.get("email", "").lower():
                customers.append(c)

    invoices = []
    if len(q) >= 2:
        q_lower = q.lower()
        for inv in store.load("invoices"):
            if q_lower in inv.get("invoice_number", "").lower():
                invoices.append(inv)

    transactions = []
    if len(q) >= 2:
        q_lower = q.lower()
        for tx in store.load("camt_transactions"):
            if (
                q_lower in (tx.get("debtor_name") or "").lower()
                or q_lower in (tx.get("remittance_info") or "").lower()
            ):
                transactions.append(tx)

    from app.main import templates as jinja_env

    html = jinja_env.get_template("fragments/search_results.html.j2").render(
        request=request,
        q=q,
        customers=customers,
        invoices=invoices,
        transactions=transactions,
    )
    return HTMLResponse(html)
