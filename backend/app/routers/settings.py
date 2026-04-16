import yaml
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import DATA_DIR, get_config

router = APIRouter(prefix="/settings")


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


@router.get("")
def settings_page(request: Request):
    from app.main import render

    try:
        raw = _read_raw()
    except FileNotFoundError:
        raw = {"company": {}, "smtp": {}, "invoice": {}}

    smtp = {k: v for k, v in raw.get("smtp", {}).items() if k != "password"}
    ctx = {
        "active_page": "settings",
        "company": raw.get("company", {}),
        "smtp": smtp,
        "invoice": raw.get("invoice", {}),
        "errors": {},
    }
    return render(request, "base.html.j2", "pages/settings.html.j2", ctx)


@router.put("")
async def update_settings(request: Request):
    from app.main import set_toast
    from app.main import templates as jinja_env

    form = await request.form()
    data = dict(form)

    # Rebuild nested structure
    company = {
        "name": data.get("company_name", ""),
        "street": data.get("company_street", ""),
        "house_number": data.get("company_house_number", ""),
        "postcode": data.get("company_postcode", ""),
        "city": data.get("company_city", ""),
        "email": data.get("company_email", ""),
        "phone": data.get("company_phone", ""),
        "tax_id": data.get("company_tax_id", ""),
        "bank_name": data.get("company_bank_name", ""),
        "iban": data.get("company_iban", ""),
        "bic": data.get("company_bic", ""),
    }
    smtp = {
        "host": data.get("smtp_host", ""),
        "port": int(data.get("smtp_port", 587) or 587),
        "username": data.get("smtp_username", ""),
        "use_tls": data.get("smtp_use_tls") == "on",
        "use_ssl": data.get("smtp_use_ssl") == "on",
        "sender_name": data.get("smtp_sender_name", ""),
        "sender_email": data.get("smtp_sender_email", ""),
    }
    invoice = {
        "number_format": data.get("invoice_number_format", ""),
        "payment_terms_days": int(data.get("invoice_payment_terms_days", 14) or 14),
        "vat_rate": float(data.get("invoice_vat_rate", 0.19) or 0.19),
        "currency": data.get("invoice_currency", "EUR"),
    }

    try:
        raw = _read_raw()
    except FileNotFoundError:
        raw = {}

    existing_password = raw.get("smtp", {}).get("password")
    raw["company"] = company
    raw["smtp"] = smtp
    if existing_password:
        raw["smtp"]["password"] = existing_password
    raw["invoice"] = invoice

    _write_raw(raw)
    get_config.cache_clear()

    smtp_display = {k: v for k, v in smtp.items() if k != "password"}
    html = jinja_env.get_template("pages/settings.html.j2").render(
        request=request,
        active_page="settings",
        company=company,
        smtp=smtp_display,
        invoice=invoice,
        errors={},
    )
    _r = HTMLResponse(html, status_code=200)
    set_toast(_r, "Einstellungen gespeichert.")
    return _r
