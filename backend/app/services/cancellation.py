from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import TEMPLATES_DIR, get_config
from app.db.yaml_store import YamlStore
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.plan import Plan

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


def generate_cancellation(contract_id: int, end_date: date, s: YamlStore) -> Path:
    contract_d = s.get_by_id("contracts", contract_id)
    if not contract_d:
        raise ValueError(f"Contract {contract_id} not found")
    contract = Contract(**contract_d)

    customer_d = s.get_by_id("customers", contract.customer_id)
    if not customer_d:
        raise ValueError(f"Customer {contract.customer_id} not found")
    customer = Customer(**customer_d)

    plan_d = s.get_by_id("plans", contract.plan_id)
    plan = Plan(**plan_d) if plan_d else None
    config = get_config()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template("cancellation.html.j2")
    html_str = template.render(
        contract=contract,
        customer=customer,
        plan=plan,
        company=config.company,
        end_date=end_date,
        today=date.today(),
    )

    output_path = OUTPUT_DIR / "cancellations" / f"cancellation-{contract_id}-{end_date}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_str, base_url=str(ASSETS_DIR)).write_pdf(str(output_path))
    return output_path
