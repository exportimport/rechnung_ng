<img src="assets/logo.svg" alt="rechnung_ng" width="200">

Web-based contract and invoice management system. Single-user, local deployment.

## Features

- Customer, contract, and plan management
- Automatic invoice generation as PDF
- Email dispatch with configurable templates
- Dashboard for open and overdue invoices

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, WeasyPrint, Jinja2
- **Frontend**: HTMX 2.x + Jinja2 templates (no npm, no build step)
- **Storage**: Flat-file YAML

## Getting Started

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add your SMTP password
uvicorn app.main:app --reload --port 8000
```

App runs on `http://localhost:8000`.

## Configuration

Edit `backend/data/config.yaml` for company info, SMTP settings, and invoice number format.
Set `SMTP_PASSWORD` in `backend/.env` (never committed).

## Storage

Data is stored as YAML files (`invoices.yaml`, `customers.yaml`, etc.). Fine for years of normal use. If the dashboard starts feeling slow, the fix is SQLite — a ~50-line migration script would do it.
