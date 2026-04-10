from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    id: int
    vorname: str
    nachname: str
    adresse: str
    iban: str
    email: EmailStr
    comment: str | None = None


class CustomerCreate(BaseModel):
    vorname: str
    nachname: str
    adresse: str
    iban: str
    email: EmailStr
    comment: str | None = None


CustomerUpdate = CustomerCreate
