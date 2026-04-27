import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"
BUILD_NUMBER = os.environ.get("BUILD_NUMBER", "dev")
BUILD_SHA = os.environ.get("BUILD_SHA", "local")
TEMPLATES_DIR = Path(__file__).parent / "templates"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


class CompanyConfig(BaseModel):
    name: str
    street: str
    house_number: str
    postcode: str
    city: str
    email: str
    phone: str = ""
    tax_id: str = ""
    bank_name: str = ""
    iban: str = ""
    bic: str = ""
    logo: str = "assets/logo.png"


class SmtpConfig(BaseModel):
    host: str
    port: int = 587
    username: str
    password: str = Field(default_factory=lambda: os.environ.get("SMTP_PASSWORD", ""))
    use_tls: bool = True  # STARTTLS (port 587)
    use_ssl: bool = False  # SSL/TLS (port 465) — set to true instead of use_tls for port 465
    sender_name: str
    sender_email: str


class InvoiceConfig(BaseModel):
    number_format: str = "{customer_id}-{contract_id}-{year}-{month:02d}-{seq:04d}"
    payment_terms_days: int = 14
    vat_rate: float = 0.19
    currency: str = "EUR"


class AppConfig(BaseModel):
    company: CompanyConfig
    smtp: SmtpConfig
    invoice: InvoiceConfig


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    config_path = DATA_DIR / "config.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
