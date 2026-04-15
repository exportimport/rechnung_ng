from datetime import date

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from app.db.yaml_store import store
from app.models.plan import Plan, current_price

router = APIRouter(prefix="/plans")


def _enrich_plan(plan: Plan) -> dict:
    data = plan.model_dump(mode="json")
    price = current_price(plan, date.today())
    data["current_price"] = float(price) if price is not None else None
    return data


@router.get("")
def list_plans(request: Request):
    from app.main import render

    plans = [Plan(**d) for d in store.load("plans")]
    enriched = [_enrich_plan(p) for p in plans]
    ctx = {"active_page": "plans", "plans": enriched}
    return render(request, "base.html.j2", "fragments/plan_table.html.j2", ctx)


@router.get("/new")
def new_plan_form(request: Request):
    from app.main import render

    ctx = {"active_page": "plans", "plan": None, "errors": {}}
    return render(request, "base.html.j2", "pages/plan_form.html.j2", ctx)


@router.get("/{plan_id}")
def edit_plan_form(request: Request, plan_id: int):
    from app.main import render

    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    plan = Plan(**d)
    ctx = {"active_page": "plans", "plan": _enrich_plan(plan), "errors": {}}
    return render(request, "base.html.j2", "pages/plan_form.html.j2", ctx)


@router.post("")
async def create_plan(request: Request, response: Response):
    from app.main import set_toast
    from app.main import templates as jinja_env

    form = await request.form()
    data = dict(form)
    errors = _validate_plan(data)
    if errors:
        html = jinja_env.get_template("pages/plan_form.html.j2").render(
            request=request, active_page="plans", plan=None, form_data=data, errors=errors
        )
        return HTMLResponse(html, status_code=422)

    record = store.create("plans", {
        "name": data["name"].strip(),
        "price_history": [{"amount": data["initial_price"].strip(), "valid_from": data["valid_from"].strip()}],
    })
    plan = Plan(**record)
    set_toast(response, f'Tarif "{plan.name}" erstellt.')
    response.headers["HX-Redirect"] = "/plans"
    return HTMLResponse("", status_code=200)


@router.put("/{plan_id}")
async def update_plan(request: Request, response: Response, plan_id: int):
    from app.main import set_toast
    from app.main import templates as jinja_env

    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")

    form = await request.form()
    data = dict(form)
    errors = {}
    if not data.get("name", "").strip():
        errors["name"] = "Pflichtfeld"
    if errors:
        html = jinja_env.get_template("pages/plan_form.html.j2").render(
            request=request, active_page="plans",
            plan=_enrich_plan(Plan(**d)), form_data=data, errors=errors
        )
        return HTMLResponse(html, status_code=422)

    updated = store.update("plans", plan_id, {"name": data["name"].strip()})
    plan = Plan(**updated)
    set_toast(response, f'Tarif "{plan.name}" aktualisiert.')
    response.headers["HX-Redirect"] = "/plans"
    return HTMLResponse("", status_code=200)


@router.post("/{plan_id}/price")
async def add_price(request: Request, response: Response, plan_id: int):
    from app.main import set_toast
    from app.main import templates as jinja_env

    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")

    form = await request.form()
    data = dict(form)
    errors = {}
    if not data.get("amount", "").strip():
        errors["amount"] = "Pflichtfeld"
    if not data.get("valid_from", "").strip():
        errors["valid_from"] = "Pflichtfeld"

    if errors:
        plan = Plan(**d)
        html = jinja_env.get_template("fragments/plan_price_form.html.j2").render(
            request=request, plan=_enrich_plan(plan), form_data=data, errors=errors
        )
        return HTMLResponse(html, status_code=422)

    plan = Plan(**d)
    history = list(plan.model_dump(mode="json")["price_history"])
    history.append({"amount": data["amount"].strip(), "valid_from": data["valid_from"].strip()})
    history.sort(key=lambda e: e["valid_from"])
    updated = store.update("plans", plan_id, {"price_history": history})
    set_toast(response, "Preis hinzugefügt.")

    updated_plan = Plan(**updated)
    html = jinja_env.get_template("fragments/plan_price_history.html.j2").render(
        request=request, plan=_enrich_plan(updated_plan)
    )
    return HTMLResponse(html, status_code=200)


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, response: Response):
    from app.main import set_toast

    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    contracts = store.load("contracts")
    if any(c.get("plan_id") == plan_id for c in contracts):
        raise HTTPException(status_code=409, detail="Tarif wird von einem Vertrag verwendet")
    store.delete("plans", plan_id)
    set_toast(response, "Tarif gelöscht.")
    return HTMLResponse("", status_code=200)


def _validate_plan(data: dict) -> dict:
    errors = {}
    if not data.get("name", "").strip():
        errors["name"] = "Pflichtfeld"
    if not data.get("initial_price", "").strip():
        errors["initial_price"] = "Pflichtfeld"
    else:
        try:
            float(data["initial_price"].replace(",", "."))
        except ValueError:
            errors["initial_price"] = "Ungültiger Betrag"
    if not data.get("valid_from", "").strip():
        errors["valid_from"] = "Pflichtfeld"
    return errors
