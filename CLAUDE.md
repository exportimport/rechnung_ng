# CLAUDE.md — rechnung_ng

## What this repo is

Web-based contract and invoice management system for a single company. Single-user, local deployment. Processes personal data (customer names, addresses, IBANs, email addresses, tax IDs) and sends invoices via SMTP.

The frontend was rewritten from React/TypeScript/Vite to **HTMX + Jinja2**, served directly by FastAPI. No npm, no Node.js, no build step. Client-side footprint: 2 local JS files (~53 KB). This minimises supply-chain attack surface.

## Dev environment

- **Distrobox:** `rechnung-htmx` (Ubuntu 24.04) — run all shell commands here
- **Python:** 3.12, venv under `backend/.venv/`
- **Start:** `distrobox enter rechnung-htmx -- bash -c "cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"`
- **Styling:** Plain CSS, no build step

## Architecture

```
Browser → HTMX (~14 KB, local) → GET/POST /... → FastAPI renders HTML fragment → HTMX swaps DOM
                                                    ↓
                                         Jinja2 templates + WeasyPrint (PDF)
```

One server, one process, one port. No CORS config, no separate dev server.

## Tech stack

| Component | Technology |
|---|---|
| Backend / Server | FastAPI + Uvicorn |
| Templating | Jinja2 |
| Client interactivity | HTMX 2.x (`/static/js/htmx.min.js`) |
| SSE (progress) | htmx SSE extension (`/static/js/ext/sse.js`) |
| Styling | Plain CSS (`/static/css/style.css`) |
| Validation | Pydantic (server-side), native HTML5 (client-side) |
| Storage | YAML flat-file (YamlStore) |
| PDF generation | WeasyPrint + Jinja2 |
| Email | smtplib |

## Directory layout

```
backend/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py
│   ├── db/yaml_store.py
│   ├── models/              # Pydantic models (customer, contract, plan, invoice)
│   ├── services/            # Business logic (invoice_generator, mail_service, cancellation)
│   ├── routers/             # HTML-returning routes (customers, contracts, plans, invoices, …)
│   ├── templates/
│   │   ├── base.html.j2     # Layout: sidebar, HTMX includes, toast container
│   │   ├── pages/           # Full-page templates
│   │   ├── fragments/       # HTMX swap targets
│   │   ├── invoice.html.j2  # PDF template
│   │   └── cancellation.html.j2
│   └── static/
│       ├── js/htmx.min.js
│       ├── js/ext/sse.js
│       ├── css/style.css
│       └── img/logo.svg
├── data/                    # Runtime YAML files
├── output/                  # Generated PDFs
└── tests/
```

## Routing pattern

HTMX requests (`HX-Request: true`) receive only the HTML fragment; direct browser requests receive the full page with layout (for bookmarks, reload, back-navigation).

```python
def render(request, template, fragment_template, context) -> HTMLResponse:
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        html = templates.get_template(fragment_template).render(**context)
    else:
        context["content_template"] = fragment_template
        html = templates.get_template(template).render(**context)
    return HTMLResponse(html)
```

## Jinja2 conventions

- Files end in `.html.j2`
- Autoescape is globally active; `|safe` only where explicitly needed (and commented why)
- Never use `|safe` on user input
- Available filters: `euro`, `date_de`
- Available globals: `InvoiceStatus`, `ContractStatus`

## Security

- CSRF token in every form via `hx-headers` on `<body>`
- Jinja2 autoescape active for all HTML templates
- SandboxedEnvironment for mail templates (user-controlled content)
- CSP header set in middleware
- File uploads: MIME type checked via magic bytes

## Code style

- Python: Ruff (`ruff check`, `ruff format`), py312, line-length 100
- HTML templates: 2-space indent, Jinja2 blocks on own line
- CSS: BEM naming
- Commits: Conventional Commits (`feat:`, `fix:`, `style:`, `refactor:`, `test:`, `docs:`)

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest
```
