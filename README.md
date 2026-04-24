<img src="assets/logo.svg" alt="rechnung_ng" width="160">

Web based contract and invoice management with payment reconciliation of Camt0.53 imports.

<video src="https://github.com/user-attachments/assets/a1631864-5f57-4c5d-b72b-ce8f1920a045" autoplay loop muted playsinline width="100%"></video>

---

## Features

- **Customers & Contracts** — manage customer data with monthly or quarterly billing cycles
- **Automatic invoice generation** — generates PDFs for all active contracts in one click, rendered in parallel
- **Mail dispatch** — sends invoices via SMTP with per-customer Jinja2 mail templates
- **Payment reconciliation** — import CAMT.053 v8 bank exports; transactions are auto-matched to invoices by invoice number, IBAN, or fuzzy name; unmatched ones can be reviewed or manually assigned
- **Cancellation letters** — generate PDF cancellation notices for ended contracts
- **Dashboard** — live overview of open, overdue, and paid invoices

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Templating | Jinja2 (server-rendered) |
| Interactivity | HTMX 2.x — no build step, no npm |
| PDF generation | WeasyPrint |
| Storage | YAML flat-files |
| Email | smtplib |

No Node.js. No database server. No frontend build pipeline. Client-side footprint: two local JS files (~53 KB total).

## Self-hosting

### Docker

```bash
docker run -d \
  --name rechnung-ng \
  -p 8000:8000 \
  -v /your/data:/app/data \
  -v /your/output:/app/output \
  -v /your/uploads:/app/uploads \
  --env-file /your/env \
  ghcr.io/exportimport/rechnung-ng:latest
```

Copy `example/config.yaml` to `/your/data/config.yaml` and fill in your company and SMTP details.

### Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000`.

## Configuration

`data/config.yaml`:

```yaml
company:
  name: Musterfirma GmbH
  street: Musterstraße
  house_number: "1"
  postcode: "12345"
  city: Berlin
  email: kontakt@musterfirma.de
  iban: DE00 1234 5678 9012 3456 78
  bic: BELADEBEXXX

smtp:
  host: smtp.example.com
  port: 587
  username: user@example.com
  use_tls: true
  sender_name: Musterfirma
  sender_email: rechnungen@musterfirma.de

invoice:
  number_format: "{customer_id}-{contract_id}-{year}-{month:02d}-{seq:04d}"
  payment_terms_days: 14
  vat_rate: 0.19
```

Set `SMTP_PASSWORD` in `.env` 

## Development

```bash
pytest                  # run tests
ruff check app/         # lint
ruff format app/        # format
```

CI runs lint → tests → Docker build → deploy on every push to `main`.

