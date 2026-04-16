import json
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.contract import ContractStatus
from app.models.invoice import InvoiceStatus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# Jinja2 Environment
# ---------------------------------------------------------------------------

templates = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "html.j2"]),
)

# Filters
templates.filters["euro"] = (
    lambda v: f"{float(v):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    if v is not None
    else "—"
)
def _date_de(v):
    from datetime import date, datetime
    if not v:
        return "—"
    if isinstance(v, str):
        v = datetime.fromisoformat(v)
    return v.strftime("%d.%m.%Y")

templates.filters["date_de"] = _date_de
templates.filters["month_name"] = lambda v: [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
][int(v)]

# Globals
templates.globals["ContractStatus"] = ContractStatus
templates.globals["InvoiceStatus"] = InvoiceStatus
templates.globals["CONTRACT_STATUS_LABELS"] = {
    ContractStatus.active: "Aktiv",
    ContractStatus.not_yet_active: "Noch nicht aktiv",
    ContractStatus.cancelled: "Gekündigt",
}
templates.globals["csrf_token"] = ""   # overridden per-request in render()
templates.globals["INVOICE_STATUS_LABELS"] = {
    InvoiceStatus.draft: "Entwurf",
    InvoiceStatus.sent: "Versendet",
}


# ---------------------------------------------------------------------------
# Render helper
# ---------------------------------------------------------------------------

def render(
    request: Request,
    page_template: str,
    fragment_template: str,
    context: dict,
) -> HTMLResponse:
    """Returns fragment for HTMX requests, full page for direct browser access."""
    csrf_token = _get_or_create_csrf(request)
    ctx = {"request": request, "csrf_token": csrf_token, **context}
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        html = templates.get_template(fragment_template).render(**ctx)
    else:
        ctx["content_template"] = fragment_template
        html = templates.get_template(page_template).render(**ctx)
    resp = HTMLResponse(html)
    resp.set_cookie(_CSRF_COOKIE, csrf_token, httponly=False, samesite="strict")
    return resp


def set_toast(response: Response, message: str, ok: bool = True) -> None:
    """Sets HX-Trigger header to show a toast notification.
    Pass the HTMLResponse you are about to return, not the injected Response param.
    """
    response.headers["HX-Trigger"] = json.dumps(
        {"showToast": {"message": message, "ok": ok}}
    )


# ---------------------------------------------------------------------------
# CSRF  (double-submit cookie — stateless, survives server restarts)
# ---------------------------------------------------------------------------

_CSRF_COOKIE = "csrf_token"


def _get_or_create_csrf(request: Request) -> str:
    return request.cookies.get(_CSRF_COOKIE) or secrets.token_hex(32)


def validate_csrf(request: Request) -> bool:
    cookie = request.cookies.get(_CSRF_COOKIE, "")
    header = request.headers.get("X-CSRF-Token", "")
    return bool(cookie) and cookie == header


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    for d in [
        BASE_DIR / "data",
        BASE_DIR / "output" / "invoices",
        BASE_DIR / "output" / "cancellations",
        BASE_DIR / "uploads" / "contracts",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="rechnung_ng", version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    safe_methods = {"GET", "HEAD", "OPTIONS"}
    if request.method not in safe_methods:
        if not validate_csrf(request):
            return HTMLResponse("<p>CSRF-Token ungültig.</p>", status_code=403)
    response = await call_next(request)
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        html = '<div class="toast toast-error">Interner Serverfehler</div>'
    else:
        html = templates.get_template("pages/error.html.j2").render(
            request=request, message="Interner Serverfehler"
        )
    return HTMLResponse(html, status_code=500)


# Static files
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
(BASE_DIR / "output").mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(BASE_DIR / "output")), name="output")

# Routers
from app.routers import (  # noqa: E402
    contracts,
    customers,
    dashboard,
    invoices,
    mail_templates,
    plans,
    settings,
)

app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(plans.router)
app.include_router(contracts.router)
app.include_router(invoices.router)
app.include_router(mail_templates.router)
app.include_router(settings.router)
