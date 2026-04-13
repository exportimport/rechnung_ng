<img src="frontend/src/assets/logo.svg" alt="rechnung_ng" width="200">
Web-based contract and invoice management system. Single-user, local deployment.

## Features

- Customer, contract, and plan management
- Automatic invoice generation as PDF
- Email dispatch with configurable templates
- Dashboard for open and overdue invoices

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, WeasyPrint
- **Frontend**: React 18, TypeScript, Vite, TanStack Query
- **Storage**: Flat-file YAML

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add your SMTP password
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs on `http://localhost:5173`, API on `http://localhost:8000`.

## Configuration

Edit `backend/data/config.yaml` for company info, SMTP settings, and invoice format.
Set `SMTP_PASSWORD` in `backend/.env` (never committed).

## Heads up: flat-file storage

Data is stored as YAML files (`invoices.yaml`, `customers.yaml`, etc.). Every API request reads the entire file from disk — fine for years of normal use, but worth knowing.

At ~20 customers with monthly billing, `invoices.yaml` grows roughly 60KB/year and hits ~1MB after a decade. That's manageable in size, but the load-everything-on-every-request pattern will get sluggish before that.

**When to migrate:** if the dashboard or invoice list starts feeling slow, the fix is SQLite — still a single file, zero server setup, but with indexed queries and proper transactions. A migration script from YAML → SQLite would be ~50 lines of Python.
