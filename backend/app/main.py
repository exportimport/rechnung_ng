from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent.parent


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


app = FastAPI(title="rechnung_ng", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


from app.routers import contracts, customers, dashboard, invoices, mail_templates, plans  # noqa: E402

app.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])
app.include_router(mail_templates.router, prefix="/api/v1/mail-templates", tags=["mail-templates"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])

# Serve generated PDFs
app.mount("/output", StaticFiles(directory=str(BASE_DIR / "output")), name="output")
