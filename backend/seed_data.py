#!/usr/bin/env python3
"""Seed script: 100 customers, 4 plans, contracts + 3 years of invoice history."""
import calendar
import random
from datetime import date, datetime
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).parent / "data"
random.seed(42)

FIRST_NAMES = [
    "Anna", "Marie", "Sophie", "Laura", "Julia", "Lisa", "Lena", "Hannah", "Emma", "Mia",
    "Lea", "Sara", "Katharina", "Claudia", "Sabine", "Monika", "Petra", "Stefanie", "Nicole", "Andrea",
    "Thomas", "Michael", "Andreas", "Stefan", "Markus", "Christian", "Daniel", "Martin", "Peter", "Klaus",
    "Frank", "Wolfgang", "Jürgen", "Hans", "Dieter", "Uwe", "Ralf", "Bernd", "Gerhard", "Heinz",
    "Felix", "Max", "Leon", "Lukas", "Noah", "Elias", "Jonas", "Tim", "Moritz", "Paul",
    "Nico", "Jan", "Tobias", "Sebastian", "Florian", "Philipp", "Dominik", "Alexander", "Christoph", "Patrick",
]

LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann",
    "Braun", "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier",
    "Lehmann", "Schmid", "Schulze", "Maier", "Köhler", "Herrmann", "König", "Walter", "Mayer", "Huber",
    "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung", "Hahn", "Schubert",
]

STREETS = [
    "Hauptstraße", "Bahnhofstraße", "Gartenstraße", "Schillerstraße", "Goethestraße",
    "Lindenstraße", "Kirchstraße", "Schulstraße", "Bergstraße", "Waldstraße",
    "Friedrichstraße", "Bismarckstraße", "Mozartstraße", "Beethovenstraße", "Ringstraße",
    "Am Markt", "Rosenstraße", "Dorfstraße", "Brückenstraße", "Poststraße",
]

CITIES = [
    ("Berlin", "10115"), ("Hamburg", "20095"), ("München", "80331"), ("Köln", "50667"),
    ("Frankfurt", "60311"), ("Stuttgart", "70173"), ("Düsseldorf", "40213"), ("Leipzig", "04109"),
    ("Dortmund", "44135"), ("Essen", "45127"), ("Bremen", "28195"), ("Dresden", "01067"),
    ("Hannover", "30159"), ("Nürnberg", "90402"), ("Bochum", "44787"), ("Wuppertal", "42103"),
    ("Bonn", "53111"), ("Bielefeld", "33602"), ("Mannheim", "68161"), ("Karlsruhe", "76133"),
]


def gen_iban(i: int) -> str:
    return f"DE{(i % 90 + 10):02d}37040044{i:010d}"


def gen_email(vorname: str, nachname: str, i: int) -> str:
    v = vorname.lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    n = nachname.lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    domains = ["gmail.com", "web.de", "gmx.de", "t-online.de", "freenet.de"]
    return f"{v}.{n}{i}@{random.choice(domains)}"


# ── Customers ──────────────────────────────────────────────────────────────────
customers = []
used = set()
for i in range(1, 101):
    while True:
        fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        if (fn, ln) not in used:
            used.add((fn, ln))
            break
    city, postcode = random.choice(CITIES)
    customers.append({
        "id": i,
        "vorname": fn,
        "nachname": ln,
        "street": random.choice(STREETS),
        "house_number": str(random.randint(1, 120)),
        "postcode": postcode,
        "city": city,
        "iban": gen_iban(i),
        "email": gen_email(fn, ln, i),
        "comment": None,
    })

# ── Plans ──────────────────────────────────────────────────────────────────────
plans = [
    {
        "id": 1,
        "name": "DSL Basic",
        "price_history": [
            {"amount": "19.99", "valid_from": "2022-01-01"},
            {"amount": "24.99", "valid_from": "2024-01-01"},
        ],
    },
    {
        "id": 2,
        "name": "DSL Plus",
        "price_history": [
            {"amount": "29.99", "valid_from": "2022-01-01"},
            {"amount": "34.99", "valid_from": "2023-07-01"},
        ],
    },
    {
        "id": 3,
        "name": "Fiber 100",
        "price_history": [
            {"amount": "39.99", "valid_from": "2022-01-01"},
            {"amount": "44.99", "valid_from": "2024-01-01"},
        ],
    },
    {
        "id": 4,
        "name": "Fiber 250",
        "price_history": [
            {"amount": "59.99", "valid_from": "2022-01-01"},
            {"amount": "69.99", "valid_from": "2023-07-01"},
        ],
    },
]

# ── Contracts ──────────────────────────────────────────────────────────────────
start_pool = [
    date(yr, mo, 1)
    for yr in (2022, 2023)
    for mo in range(1, 13)
] + [date(2024, mo, 1) for mo in range(1, 7)]

cycles = ["monthly"] * 3 + ["quarterly"]

contracts = []
cid = 1
cancelled = 0
for c in customers[:93]:
    start = random.choice(start_pool)
    plan_id = random.choice([1, 2, 3, 4])
    cycle = random.choice(cycles)

    end_date = None
    if cancelled < 15 and random.random() < 0.20:
        mo = start.month + random.randint(8, 24)
        yr = start.year + (mo - 1) // 12
        mo = (mo - 1) % 12 + 1
        ed = date(yr, mo, calendar.monthrange(yr, mo)[1])
        if ed < date(2026, 4, 1):
            end_date = ed.isoformat()
            cancelled += 1

    contracts.append({
        "id": cid,
        "customer_id": c["id"],
        "plan_id": plan_id,
        "start_date": start.isoformat(),
        "end_date": end_date,
        "billing_cycle": cycle,
        "reference": None,
        "scan_file": None,
        "cancellation_pdf": None,
        "comment": None,
    })
    cid += 1

# ── Invoices (2023-01 → 2026-03, all marked sent) ──────────────────────────────
def price_at(plan_id: int, yr: int, mo: int) -> float:
    plan = next(p for p in plans if p["id"] == plan_id)
    d = f"{yr}-{mo:02d}-01"
    amount = None
    for entry in sorted(plan["price_history"], key=lambda e: e["valid_from"]):
        if entry["valid_from"] <= d:
            amount = float(entry["amount"])
    return amount or 0.0


invoices = []
iid = 1

for yr in range(2023, 2027):
    for mo in range(1, 13):
        if yr == 2026 and mo > 3:
            break
        first = date(yr, mo, 1)
        last = date(yr, mo, calendar.monthrange(yr, mo)[1])
        seq = 1
        for contract in contracts:
            start = date.fromisoformat(contract["start_date"])
            end = date.fromisoformat(contract["end_date"]) if contract["end_date"] else None
            if start > last or (end is not None and end < first):
                continue
            if contract["billing_cycle"] == "quarterly" and mo not in (1, 4, 7, 10):
                continue
            p = price_at(contract["plan_id"], yr, mo)
            if not p:
                continue
            amount = p * 3 if contract["billing_cycle"] == "quarterly" else p
            if contract["billing_cycle"] == "quarterly":
                em = mo + 2
                ey = yr + (em - 1) // 12
                em = (em - 1) % 12 + 1
                period_end = date(ey, em, calendar.monthrange(ey, em)[1])
            else:
                period_end = last
            invoices.append({
                "id": iid,
                "contract_id": contract["id"],
                "customer_id": contract["customer_id"],
                "invoice_number": f"{contract['customer_id']}-{contract['id']}-{yr}-{mo:02d}-{seq:04d}",
                "year": yr,
                "month": mo,
                "amount": amount,
                "period_start": first.isoformat(),
                "period_end": period_end.isoformat(),
                "status": "sent",
                "pdf_path": None,
                "mail_template": None,
                "created_at": datetime(yr, mo, 2, 10, 0).isoformat(),
                "sent_at": datetime(yr, mo, 3, 9, 0).isoformat(),
            })
            iid += 1
            seq += 1

print(f"Customers : {len(customers)}")
print(f"Plans     : {len(plans)}")
print(f"Contracts : {len(contracts)}  (cancelled: {cancelled})")
print(f"Invoices  : {len(invoices)}")

(DATA_DIR / "customers.yaml").write_text(yaml.dump(customers, allow_unicode=True))
(DATA_DIR / "plans.yaml").write_text(yaml.dump(plans, allow_unicode=True))
(DATA_DIR / "contracts.yaml").write_text(yaml.dump(contracts, allow_unicode=True))
(DATA_DIR / "invoices.yaml").write_text(yaml.dump(invoices, allow_unicode=True))
print("Written to", DATA_DIR)
