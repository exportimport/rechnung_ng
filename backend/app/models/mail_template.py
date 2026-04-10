from pydantic import BaseModel


class MailTemplate(BaseModel):
    id: str  # slug: "default", "new_customer", "price_increase", "cancellation"
    name: str
    subject: str  # Jinja2 template string
    body: str  # Jinja2 template string


class MailTemplateUpdate(BaseModel):
    subject: str
    body: str
