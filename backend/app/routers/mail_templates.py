from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2.sandbox import SandboxedEnvironment

from app.db.yaml_store import store

router = APIRouter(prefix="/mail-templates")

_sandbox = SandboxedEnvironment(autoescape=False)


@router.get("")
def list_templates(request: Request):
    from app.main import render

    templates_data = store.load("mail_templates")
    ctx = {"active_page": "mail_templates", "mail_templates": templates_data}
    return render(request, "base.html.j2", "pages/mail_templates.html.j2", ctx)


@router.put("/{template_id}")
async def update_template(request: Request, template_id: str):
    from app.main import set_toast

    d = store.get_by_id("mail_templates", template_id)
    if not d:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")

    form = await request.form()
    data = {
        "subject": form.get("subject", "").strip(),
        "body": form.get("body", "").strip(),
    }

    # Validate that templates are syntactically valid (sandboxed)
    errors = {}
    for field in ("subject", "body"):
        try:
            _sandbox.parse(data[field])
        except Exception as e:
            errors[field] = f"Ungültiges Template: {e}"

    if errors:
        from app.main import templates as jinja_env
        html = jinja_env.get_template("fragments/mail_template_form.html.j2").render(
            request=request,
            tpl={**d, **data},
            errors=errors,
        )
        return HTMLResponse(html, status_code=422)

    updated = store.update("mail_templates", template_id, data)
    from app.main import templates as jinja_env
    html = jinja_env.get_template("fragments/mail_template_form.html.j2").render(
        request=request, tpl=updated, errors={},
    )
    _r = HTMLResponse(html, status_code=200)
    set_toast(_r, "Vorlage gespeichert.")
    return _r
