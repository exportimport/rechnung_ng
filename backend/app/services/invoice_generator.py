import calendar
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import get_config
from app.db.yaml_store import YamlStore
from app.models.contract import BillingCycle, Contract, compute_status, ContractStatus
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.plan import Plan, current_price

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


def _period_end_quarterly(year: int, month: int) -> date:
    end_month = month + 2
    end_year = year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    last_day = calendar.monthrange(end_year, end_month)[1]
    return date(end_year, end_month, last_day)


def _next_seq(all_invoices: list[dict], year: int, month: int) -> int:
    seqs = []
    for inv in all_invoices:
        if inv.get("year") == year and inv.get("month") == month:
            try:
                seqs.append(int(inv["invoice_number"].split("-")[-1]))
            except (KeyError, ValueError, IndexError):
                pass
    return max(seqs, default=0) + 1


def render_invoice_pdf(
    invoice: Invoice,
    contract: Contract,
    plan: Plan,
    customer: Customer,
    s: YamlStore,
) -> Path:
    config = get_config()
    gross = Decimal(str(invoice.amount))
    net = gross / Decimal("1.19")
    vat = gross - net

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template("invoice.html.j2")
    html_str = template.render(
        invoice=invoice,
        contract=contract,
        plan=plan,
        customer=customer,
        company=config.company,
        net=net,
        vat=vat,
        gross=gross,
        payment_terms_days=config.invoice.payment_terms_days,
    )

    output_path = OUTPUT_DIR / "invoices" / f"{invoice.invoice_number}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_str, base_url=str(ASSETS_DIR)).write_pdf(str(output_path))
    return output_path


def generate_invoices(year: int, month: int, s: YamlStore) -> list[Invoice]:
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    contracts = [Contract(**d) for d in s.load("contracts")]
    active = [
        c
        for c in contracts
        if c.start_date <= last_day and (c.end_date is None or c.end_date >= first_day)
    ]

    all_invoices = s.load("invoices")
    existing_contract_ids = {
        inv["contract_id"]
        for inv in all_invoices
        if inv.get("year") == year and inv.get("month") == month
    }

    seq = _next_seq(all_invoices, year, month)
    results: list[Invoice] = []

    for contract in active:
        if contract.id in existing_contract_ids:
            continue

        if contract.billing_cycle == BillingCycle.quarterly:
            if month not in (1, 4, 7, 10):
                continue

        plan_d = s.get_by_id("plans", contract.plan_id)
        if not plan_d:
            continue
        plan = Plan(**plan_d)
        price = current_price(plan, first_day)
        if price is None:
            continue

        amount = float(price * 3 if contract.billing_cycle == BillingCycle.quarterly else price)

        if contract.billing_cycle == BillingCycle.quarterly:
            period_end = _period_end_quarterly(year, month)
        else:
            period_end = last_day

        invoice_number = f"{contract.customer_id}-{contract.id}-{year}-{month:02d}-{seq:04d}"

        data = {
            "contract_id": contract.id,
            "customer_id": contract.customer_id,
            "invoice_number": invoice_number,
            "year": year,
            "month": month,
            "amount": amount,
            "period_start": first_day.isoformat(),
            "period_end": period_end.isoformat(),
            "status": InvoiceStatus.draft.value,
            "pdf_path": None,
            "mail_template": None,
            "created_at": datetime.now().isoformat(),
            "sent_at": None,
        }
        inv_dict = s.create("invoices", data)
        invoice = Invoice(**inv_dict)

        customer_d = s.get_by_id("customers", contract.customer_id)
        if customer_d:
            customer = Customer(**customer_d)
            pdf_path = render_invoice_pdf(invoice, contract, plan, customer, s)
            inv_dict = s.update("invoices", invoice.id, {"pdf_path": str(pdf_path)})
            invoice = Invoice(**inv_dict)

        seq += 1
        results.append(invoice)

    return results
