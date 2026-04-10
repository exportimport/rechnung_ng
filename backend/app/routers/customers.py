from fastapi import APIRouter, HTTPException

from app.db.yaml_store import store
from app.models.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter()


def _to_customer(d: dict) -> Customer:
    return Customer(**d)


def _serialize(c: Customer) -> dict:
    return c.model_dump(mode="json")


@router.get("")
def list_customers(q: str | None = None):
    customers = [_to_customer(d) for d in store.load("customers")]
    if q:
        q_lower = q.lower()
        customers = [
            c
            for c in customers
            if q_lower in c.vorname.lower()
            or q_lower in c.nachname.lower()
            or q_lower in c.email.lower()
        ]
    return [_serialize(c) for c in customers]


@router.get("/{customer_id}")
def get_customer(customer_id: int):
    d = store.get_by_id("customers", customer_id)
    if not d:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return _serialize(_to_customer(d))


@router.post("", status_code=201)
def create_customer(body: CustomerCreate):
    data = body.model_dump(mode="json")
    record = store.create("customers", data)
    return _serialize(_to_customer(record))


@router.put("/{customer_id}")
def update_customer(customer_id: int, body: CustomerUpdate):
    d = store.get_by_id("customers", customer_id)
    if not d:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    updated = store.update("customers", customer_id, body.model_dump(mode="json"))
    return _serialize(_to_customer(updated))


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int):
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
