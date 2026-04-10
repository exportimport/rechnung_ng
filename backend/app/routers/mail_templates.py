from fastapi import APIRouter, HTTPException

from app.db.yaml_store import store
from app.models.mail_template import MailTemplate, MailTemplateUpdate

router = APIRouter()


@router.get("")
def list_templates():
    return store.load("mail_templates")


@router.get("/{template_id}")
def get_template(template_id: str):
    d = store.get_by_id("mail_templates", template_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    return d


@router.put("/{template_id}")
def update_template(template_id: str, body: MailTemplateUpdate):
    d = store.get_by_id("mail_templates", template_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    updated = store.update("mail_templates", template_id, body.model_dump())
    return updated
