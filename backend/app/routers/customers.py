from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from app.db.yaml_store import store
from app.models.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers")


def _to_customer(d: dict) -> Customer:
    return Customer(**d)


def _customer_list(q: str | None = None) -> list[Customer]:
    customers = [_to_customer(d) for d in store.load("customers")]
    if q:
        q_lower = q.lower()
        customers = [
            c for c in customers
            if q_lower in c.vorname.lower()
            or q_lower in c.nachname.lower()
            or q_lower in c.email.lower()
        ]
    return customers


@router.get("")
def list_customers(request: Request, q: str | None = None):
    from app.main import render

    customers = _customer_list(q)
    ctx = {"active_page": "customers", "customers": customers, "q": q or ""}
    return render(
        request,
        "base.html.j2",
        "fragments/customer_table.html.j2",
        ctx,
    )


@router.get("/new")
def new_customer_form(request: Request):
    from app.main import render

    ctx = {"active_page": "customers", "customer": None, "errors": {}}
    return render(request, "base.html.j2", "pages/customer_form.html.j2", ctx)


@router.get("/{customer_id}")
def edit_customer_form(request: Request, customer_id: int):
    from app.main import render

    d = store.get_by_id("customers", customer_id)
    if not d:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    ctx = {"active_page": "customers", "customer": _to_customer(d), "errors": {}}
    return render(request, "base.html.j2", "pages/customer_form.html.j2", ctx)


@router.post("")
async def create_customer(request: Request, response: Response):
    from app.main import set_toast
    from app.main import templates as jinja_env

    form = await request.form()
    data = dict(form)
    errors = _validate_customer(data)
    if errors:
        html = jinja_env.get_template("pages/customer_form.html.j2").render(
            request=request,
            active_page="customers",
            customer=None,
            form_data=data,
            errors=errors,
        )
        response.status_code = 422
        response.headers["HX-Reswap"] = "innerHTML"
        return HTMLResponse(html, status_code=422)

    record = store.create("customers", data)
    customer = _to_customer(record)
    set_toast(response, f"Kunde {customer.vorname} {customer.nachname} erstellt.")
    response.headers["HX-Redirect"] = "/customers"
    return HTMLResponse("", status_code=200)


@router.put("/{customer_id}")
async def update_customer(request: Request, response: Response, customer_id: int):
    from app.main import set_toast
    from app.main import templates as jinja_env

    d = store.get_by_id("customers", customer_id)
    if not d:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    form = await request.form()
    data = dict(form)
    errors = _validate_customer(data)
    if errors:
        html = jinja_env.get_template("pages/customer_form.html.j2").render(
            request=request,
            active_page="customers",
            customer=_to_customer(d),
            form_data=data,
            errors=errors,
        )
        response.status_code = 422
        return HTMLResponse(html, status_code=422)

    updated = store.update("customers", customer_id, data)
    customer = _to_customer(updated)
    set_toast(response, f"Kunde {customer.vorname} {customer.nachname} aktualisiert.")
    response.headers["HX-Redirect"] = "/customers"
    return HTMLResponse("", status_code=200)


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, response: Response):
    from app.main import set_toast

    d = store.get_by_id("customers", customer_id)
    if not d:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    contracts = store.load("contracts")
    if any(c.get("customer_id") == customer_id for c in contracts):
        raise HTTPException(
            status_code=409,
            detail="Kunde hat noch Verträge und kann nicht gelöscht werden",
        )
    store.delete("customers", customer_id)
    set_toast(response, "Kunde gelöscht.")
    return HTMLResponse("", status_code=200)


def _validate_customer(data: dict) -> dict:
    errors = {}
    for field in ("vorname", "nachname", "street", "house_number", "postcode", "city", "iban", "email"):
        if not data.get(field, "").strip():
            errors[field] = "Pflichtfeld"
    if "email" not in errors and "@" not in data.get("email", ""):
        errors["email"] = "Ungültige E-Mail-Adresse"
    return errors
