import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from jinja2 import BaseLoader, Environment

from app.config import get_config
from app.db.yaml_store import YamlStore
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus


def select_template(invoice: Invoice, s: YamlStore) -> str:
    all_invoices = [Invoice(**d) for d in s.load("invoices")]
    sent = [
        i
        for i in all_invoices
        if i.customer_id == invoice.customer_id
        and i.id != invoice.id
        and i.status == InvoiceStatus.sent
    ]
    if not sent:
        return "new_customer"
    last = max(sent, key=lambda i: (i.year, i.month))
    if abs(last.amount - invoice.amount) > 0.001:
        return "price_increase"
    return "default"


def send_invoice(invoice: Invoice, template_id: str, s: YamlStore) -> None:
    config = get_config()
    template_d = s.get_by_id("mail_templates", template_id)
    if not template_d:
        template_d = s.get_by_id("mail_templates", "default")
    customer_d = s.get_by_id("customers", invoice.customer_id)
    if not customer_d:
        raise ValueError(f"Customer {invoice.customer_id} not found")
    customer = Customer(**customer_d)

    env = Environment(loader=BaseLoader())
    subject = env.from_string(template_d["subject"]).render(invoice=invoice, customer=customer)
    body = env.from_string(template_d["body"]).render(invoice=invoice, customer=customer)

    msg = EmailMessage()
    msg["From"] = f"{config.smtp.sender_name} <{config.smtp.sender_email}>"
    msg["To"] = customer.email
    msg["Subject"] = subject
    msg.set_content(body)

    if invoice.pdf_path and Path(invoice.pdf_path).exists():
        with open(invoice.pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=f"{invoice.invoice_number}.pdf",
            )

    with smtplib.SMTP(config.smtp.host, config.smtp.port) as smtp:
        if config.smtp.use_tls:
            smtp.starttls()
        if config.smtp.username and config.smtp.password:
            smtp.login(config.smtp.username, config.smtp.password)
        smtp.send_message(msg)

    s.update(
        "invoices",
        invoice.id,
        {
            "status": InvoiceStatus.sent.value,
            "sent_at": datetime.now().isoformat(),
            "mail_template": template_id,
        },
    )
