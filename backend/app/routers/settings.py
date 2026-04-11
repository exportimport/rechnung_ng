from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import DATA_DIR, get_config

router = APIRouter()


class CompanySettings(BaseModel):
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


class SmtpSettings(BaseModel):
    host: str
    port: int = 587
    username: str
    use_tls: bool = True
    use_ssl: bool = False
    sender_name: str
    sender_email: str


class InvoiceSettings(BaseModel):
    number_format: str
    payment_terms_days: int
    vat_rate: float
    currency: str


class Settings(BaseModel):
    company: CompanySettings
    smtp: SmtpSettings
    invoice: InvoiceSettings


def _read_raw() -> dict:
    config_path = DATA_DIR / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def _write_raw(data: dict) -> None:
    config_path = DATA_DIR / "config.yaml"
    bak = config_path.with_suffix(".yaml.bak")
    if config_path.exists():
        bak.write_text(config_path.read_text())
    with open(config_path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


@router.get("", response_model=Settings)
def get_settings():
    raw = _read_raw()
    # Strip password from smtp before returning
    smtp = {k: v for k, v in raw.get("smtp", {}).items() if k != "password"}
    return Settings(company=raw["company"], smtp=smtp, invoice=raw["invoice"])


@router.put("", response_model=Settings)
def update_settings(body: Settings):
    raw = _read_raw()
    # Preserve password field if present
    existing_password = raw.get("smtp", {}).get("password")

    raw["company"] = body.company.model_dump()
    raw["smtp"] = body.smtp.model_dump()
    if existing_password:
        raw["smtp"]["password"] = existing_password
    raw["invoice"] = body.invoice.model_dump()

    _write_raw(raw)
    get_config.cache_clear()

    return body
