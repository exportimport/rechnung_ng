# rechnung_ng

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
