import shutil
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Point data directory to a temp dir before importing the app
_tmp_data = tempfile.mkdtemp()

import app.db.yaml_store as ys_module
import app.config as config_module

# Patch DATA_DIR before app loads
config_module.DATA_DIR = Path(_tmp_data)
ys_module.store = ys_module.YamlStore(Path(_tmp_data))


def _write_config():
    import yaml
    (Path(_tmp_data) / "config.yaml").write_text(yaml.dump({
        "company": {
            "name": "Test GmbH", "street": "Teststr.", "house_number": "1",
            "postcode": "12345", "city": "Teststadt", "email": "test@example.com",
            "phone": "", "tax_id": "", "bank_name": "", "iban": "", "bic": "",
        },
        "smtp": {
            "host": "localhost", "port": 587, "username": "u",
            "use_tls": True, "use_ssl": False,
            "sender_name": "Test", "sender_email": "test@example.com",
        },
        "invoice": {
            "number_format": "{customer_id}-{contract_id}-{year}-{month:02d}-{seq:04d}",
            "payment_terms_days": 14, "vat_rate": 0.19, "currency": "EUR",
        },
    }))


_write_config()

from app.main import app as fastapi_app  # noqa: E402 — must come after patching


def _csrf_token(headers: dict) -> str:
    """Extract CSRF token from response HTML meta tag."""
    import re
    body = headers.get("_body", "")
    m = re.search(r'name="csrf-token" content="([^"]+)"', body)
    return m.group(1) if m else ""


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def csrf(client):
    """Return a valid CSRF token by loading the homepage."""
    import re
    r = await client.get("/")
    m = re.search(r'name="csrf-token" content="([^"]+)"', r.text)
    return m.group(1) if m else ""


@pytest.fixture(autouse=True)
def clean_store():
    """Reset all YAML store files before each test."""
    import yaml
    for name in ("customers", "plans", "contracts", "invoices", "mail_templates"):
        p = Path(_tmp_data) / f"{name}.yaml"
        if name == "mail_templates":
            p.write_text(yaml.dump([]))
        else:
            p.write_text(yaml.dump([]))
    config_module.get_config.cache_clear()
    yield
    config_module.get_config.cache_clear()
