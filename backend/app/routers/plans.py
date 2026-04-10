from datetime import date

from fastapi import APIRouter, HTTPException

from app.db.yaml_store import store
from app.models.plan import AddPriceRequest, Plan, PlanCreate, PlanUpdate, current_price

router = APIRouter()


def _to_plan(d: dict) -> Plan:
    return Plan(**d)


def _serialize(plan: Plan) -> dict:
    return plan.model_dump(mode="json")


@router.get("", response_model=list[dict])
def list_plans():
    today = date.today()
    plans = [_to_plan(d) for d in store.load("plans")]
    result = []
    for p in plans:
        data = _serialize(p)
        price = current_price(p, today)
        data["current_price"] = float(price) if price is not None else None
        result.append(data)
    return result


@router.get("/{plan_id}")
def get_plan(plan_id: int):
    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    plan = _to_plan(d)
    data = _serialize(plan)
    data["current_price"] = float(current_price(plan, date.today()) or 0)
    return data


@router.post("", status_code=201)
def create_plan(body: PlanCreate):
    data = {
        "name": body.name,
        "price_history": [
            {"amount": str(body.initial_price), "valid_from": body.valid_from.isoformat()}
        ],
    }
    record = store.create("plans", data)
    return _serialize(_to_plan(record))


@router.put("/{plan_id}")
def update_plan(plan_id: int, body: PlanUpdate):
    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    updated = store.update("plans", plan_id, {"name": body.name})
    return _serialize(_to_plan(updated))


@router.post("/{plan_id}/price")
def add_price(plan_id: int, body: AddPriceRequest):
    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    plan = _to_plan(d)
    new_entry = {"amount": str(body.amount), "valid_from": body.valid_from.isoformat()}
    history = list(plan.model_dump(mode="json")["price_history"])
    history.append(new_entry)
    history.sort(key=lambda e: e["valid_from"])
    updated = store.update("plans", plan_id, {"price_history": history})
    return _serialize(_to_plan(updated))


@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: int):
    d = store.get_by_id("plans", plan_id)
    if not d:
        raise HTTPException(status_code=404, detail="Tarif nicht gefunden")
    # Guard: check no contracts reference this plan
    contracts = store.load("contracts")
    if any(c.get("plan_id") == plan_id for c in contracts):
        raise HTTPException(status_code=409, detail="Tarif wird von einem Vertrag verwendet")
    store.delete("plans", plan_id)
