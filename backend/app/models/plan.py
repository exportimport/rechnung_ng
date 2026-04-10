from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PriceEntry(BaseModel):
    amount: Decimal
    valid_from: date


class Plan(BaseModel):
    id: int
    name: str
    price_history: list[PriceEntry]


class PlanCreate(BaseModel):
    name: str
    initial_price: Decimal
    valid_from: date


class PlanUpdate(BaseModel):
    name: str


class AddPriceRequest(BaseModel):
    amount: Decimal
    valid_from: date


def current_price(plan: Plan, as_of: date) -> Decimal | None:
    eligible = [e for e in plan.price_history if e.valid_from <= as_of]
    if not eligible:
        return None
    return max(eligible, key=lambda e: e.valid_from).amount
