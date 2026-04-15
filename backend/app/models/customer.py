from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    id: int
    vorname: str
    nachname: str
    street: str
    house_number: str
    postcode: str
    city: str
    iban: str
    email: EmailStr
    comment: str | None = None


class CustomerCreate(BaseModel):
    vorname: str
    nachname: str
    street: str
    house_number: str
    postcode: str
    city: str
    iban: str
    email: EmailStr
    comment: str | None = None


CustomerUpdate = CustomerCreate
