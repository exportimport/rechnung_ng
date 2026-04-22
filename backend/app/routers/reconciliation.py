from fastapi import APIRouter, UploadFile
from fastapi.responses import HTMLResponse

from app.db.yaml_store import store
from app.services.camt_import import import_camt_file

router = APIRouter(prefix="/reconciliation")


@router.get("")
def monthly_view():
    return HTMLResponse("<p>Zahlungsabgleich</p>")


@router.get("/customers/{customer_id}")
def customer_view(customer_id: int):
    return HTMLResponse(f"<p>Kunde {customer_id}</p>")


@router.get("/unmatched")
def unmatched_list():
    return HTMLResponse("<p>Unabgeglichen</p>")


@router.get("/review")
def review_queue():
    return HTMLResponse("<p>Prüfwarteschlange</p>")


@router.get("/import")
def import_form():
    return HTMLResponse("<p>Import</p>")


@router.post("/import")
async def import_post(file: UploadFile):
    xml_bytes = await file.read()
    summary = import_camt_file(xml_bytes, file.filename or "upload.xml", store)
    return HTMLResponse(
        f"<p>Importiert: {summary.imported}, Übersprungen: {summary.skipped_duplicates}</p>"
    )
