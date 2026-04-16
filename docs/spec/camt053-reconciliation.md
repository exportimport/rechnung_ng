# Spec: CAMT.053 Payment Reconciliation

**Branch:** `feature/camt-payment-reconciliation`  
**Status:** Draft — drives TDD implementation  
**Format:** CAMT.053 version 8 (`urn:iso:std:iso:20022:tech:xsd:camt.053.001.08`)  
**Scope:** Import → Parse → Match → Reconciliation views

---

## 1. Decisions in effect

| Topic | Decision |
|---|---|
| Storage | Raw `camt_transactions` YAML — full audit trail, enables re-matching |
| Month display | Both invoice month AND payment month, with reconciliation column |
| Confidence tiers | Tier 1 → auto-match; Tier 2 + 3 → manual review queue |
| Unmatched transactions | Shown in dedicated list; can be manually linked to any invoice |
| `paid` state | Reversible — wrong matches can be undone, invoice returns to `sent` |
| Views | Monthly reconciliation + per-customer overview + unmatched transactions |
| Draft invoices | Hidden from all reconciliation views |
| Overdue threshold | `config.invoice.payment_terms_days` (currently 14) |
| Duplicate import | Skip silently, show count in import summary |
| Navigation | Own top-level menu item ("Zahlungsabgleich") |

---

## 2. Data models

### 2.1 `InvoiceStatus` changes

```python
class InvoiceStatus(StrEnum):
    draft = "draft"
    sent = "sent"
    paid = "paid"       # NEW — reversible, set by reconciliation
    overdue = "overdue" # NEW — derived/computed, NOT stored; calculated at read time
```

> **Note:** `overdue` is never written to YAML. It is computed on the fly:
> `status == sent AND sent_at + payment_terms_days < today`.
> Only `draft`, `sent`, `paid` are persisted.

### 2.2 `Invoice` model additions

```python
class Invoice(BaseModel):
    # ... existing fields unchanged ...
    paid_at: date | None = None                  # NEW — date payment was booked
    payment_transaction_id: str | None = None    # NEW — FK to CamtTransaction.transaction_id
```

### 2.3 `CamtTransaction` (new model)

```python
class CamtTransaction(BaseModel):
    transaction_id: str          # Unique: AcctSvcrRef or EndToEndId from XML — used for dedup
    booking_date: date
    value_date: date
    amount: float                # Always positive
    currency: str                # e.g. "EUR"
    credit_debit: Literal["CRDT", "DBIT"]
    debtor_name: str | None      # Name of the paying party (Auftraggeber)
    debtor_iban: str | None      # IBAN of the paying party
    remittance_info: str | None  # Verwendungszweck (unstructured)
    imported_at: datetime        # When this record was created in our system
    source_file: str             # Original filename of the imported CAMT file

    # Matching result — mutable
    match_status: MatchStatus = MatchStatus.unmatched
    matched_invoice_id: int | None = None
    matched_at: datetime | None = None
    match_confidence: MatchConfidence | None = None
```

### 2.4 `MatchStatus` (new enum)

```python
class MatchStatus(StrEnum):
    unmatched = "unmatched"         # Not yet matched to any invoice
    auto_matched = "auto_matched"   # Matched automatically (Tier 1)
    manually_matched = "manually_matched"  # Matched by user
    ignored = "ignored"             # User explicitly dismissed (not an invoice payment)
```

### 2.5 `MatchConfidence` (new enum)

```python
class MatchConfidence(StrEnum):
    high = "high"     # Tier 1: invoice number in Verwendungszweck
    medium = "medium" # Tier 2: amount + debtor IBAN
    low = "low"       # Tier 3: amount + fuzzy debtor name
```

---

## 3. CAMT.053 XML parsing

### 3.1 Supported namespace

```
urn:iso:std:iso:20022:tech:xsd:camt.053.001.08
```

The parser **must** read the namespace from the file root element and validate it before parsing. Future versions (v9, v10) map to the same `CamtTransaction` model via a namespace registry — the rest of the system is version-agnostic.

### 3.2 XML field mapping

| `CamtTransaction` field | XML XPath (relative to `<Ntry>`) |
|---|---|
| `transaction_id` | `NtryDtls/TxDtls/Refs/AcctSvcrRef` or `NtryDtls/TxDtls/Refs/EndToEndId` |
| `booking_date` | `BookgDt/Dt` |
| `value_date` | `ValDt/Dt` |
| `amount` | `Amt` (text, always positive) |
| `currency` | `Amt/@Ccy` |
| `credit_debit` | `CdtDbtInd` (`CRDT` or `DBIT`) |
| `debtor_name` | `NtryDtls/TxDtls/RltdPties/Dbtr/Pty/Nm` |
| `debtor_iban` | `NtryDtls/TxDtls/RltdPties/DbtrAcct/Id/IBAN` |
| `remittance_info` | `NtryDtls/TxDtls/RmtInf/Ustrd` (unstructured, concatenated if multiple) |

### 3.3 Filtering on import

Only entries with `CdtDbtInd == CRDT` (incoming payments) are imported. Debit entries are ignored.

### 3.4 `transaction_id` construction

Use `AcctSvcrRef` if present, else `EndToEndId`. If both are absent, construct a stable fallback:
```
{booking_date}_{amount}_{debtor_iban or "NOIBAN"}_{hash of remittance_info}
```
This fallback is deterministic so re-importing the same file stays idempotent.

---

## 4. Matching algorithm

The matcher is a **pure function** — no I/O, no database access, no side effects:

```python
def match_transaction(
    transaction: CamtTransaction,
    invoices: list[Invoice],
    customers: list[Customer],
) -> MatchResult:
    ...
```

```python
class MatchResult(BaseModel):
    confidence: MatchConfidence | None
    invoice_id: int | None
    reason: str  # human-readable explanation, shown in UI
```

### 4.1 Matching tiers (evaluated in order, first match wins)

#### Tier 1 — High confidence (auto-match)
**Condition:** `invoice.invoice_number` appears as a substring in `transaction.remittance_info` (case-insensitive, whitespace-normalized).

**Action:** Auto-match. Mark invoice `paid`, set `paid_at = transaction.booking_date`, set `transaction.match_status = auto_matched`.

**Ambiguity guard:** If multiple invoice numbers are found in the Verwendungszweck, do NOT auto-match — send to manual review with reason "multiple invoice numbers found".

#### Tier 2 — Medium confidence (manual review queue)
**Condition:** `transaction.amount == invoice.amount` AND `transaction.debtor_iban == customer.iban` for the customer linked to the invoice.

**Action:** Add to manual review queue with pre-selected invoice suggestion.

**Ambiguity guard:** If multiple invoices match (same customer, same amount, different months), show all candidates in the review UI.

#### Tier 3 — Low confidence (manual review queue)
**Condition:** `transaction.amount == invoice.amount` AND fuzzy name match between `transaction.debtor_name` and `customer.vorname + ' ' + customer.nachname` (threshold: ≥ 80% token overlap, case-insensitive).

**Action:** Add to manual review queue with pre-selected suggestion and low-confidence warning.

#### No match
**Condition:** None of the above.

**Action:** Transaction lands in unmatched list. No invoice is touched.

### 4.2 Amount comparison

Use `round(a, 2) == round(b, 2)` — never compare floats with `==` directly.

---

## 5. Fixture table (drives unit tests)

Each row is one test case for the matcher.

| # | remittance_info | amount | debtor_iban | expected confidence | expected invoice_id | notes |
|---|---|---|---|---|---|---|
| T01 | `"RE 2025-03-0001"` | 119.00 | any | `high` | invoice #1 | exact number match |
| T02 | `"Rechnung 2025-03-0001 danke"` | 119.00 | any | `high` | invoice #1 | number embedded in text |
| T03 | `"2025-03-0001 und 2025-04-0001"` | 238.00 | any | `None` (manual) | None | multiple numbers → no auto-match |
| T04 | `"Monatsbeitrag März"` | 119.00 | `DE89...` (customer IBAN) | `medium` | invoice #1 | amount + IBAN |
| T05 | `"Monatsbeitrag März"` | 119.00 | `DE89...` | `medium` | None (multiple) | same customer, 2 open invoices of same amount |
| T06 | `"zahlung florian maeschle"` | 119.00 | unknown IBAN | `low` | invoice #1 | fuzzy name match |
| T07 | `"Pizza"` | 12.50 | unknown IBAN | `None` | None | no match |
| T08 | `""` (empty) | 119.00 | unknown IBAN | `None` | None | no remittance, no known IBAN |
| T09 | `"RE 2025-03-0001"` | 50.00 | any | `None` (manual) | None | number matches but amount wrong → partial payment? flag it |
| T10 | `"RE 2025-03-0001"` | 119.00 | any | `high` | invoice #1 | already paid invoice → skip, add to unmatched |

> **T09 note:** Partial payments are out of scope — flag as unmatched with reason "amount mismatch despite invoice number match".
> **T10 note:** If the matched invoice is already `paid`, do not re-match — treat as unmatched.

---

## 6. Import service

```python
def import_camt_file(
    xml_bytes: bytes,
    filename: str,
    store: YamlStore,
) -> ImportSummary:
    ...

class ImportSummary(BaseModel):
    total_parsed: int         # All CRDT entries in the file
    imported: int             # New transactions stored
    skipped_duplicates: int   # Already known by transaction_id
    auto_matched: int         # Tier 1 auto-matches applied
    queued_for_review: int    # Tier 2+3 added to manual review
    unmatched: int            # No match found
```

**Steps:**
1. Parse XML → list of `CamtTransaction` (CRDT only)
2. Deduplicate against existing `camt_transactions` YAML by `transaction_id`
3. Run matcher on each new transaction
4. Apply Tier 1 auto-matches (update invoice + transaction atomically)
5. Store all new transactions (matched, review-queued, unmatched) to YAML
6. Return `ImportSummary`

---

## 7. Computed invoice status (read-time only)

When loading invoices for any reconciliation view, compute effective display status:

```python
def effective_status(invoice: Invoice, today: date, payment_terms_days: int) -> str:
    if invoice.status == InvoiceStatus.paid:
        return "paid"
    if invoice.status == InvoiceStatus.sent:
        due_date = invoice.sent_at.date() + timedelta(days=payment_terms_days)
        if today > due_date:
            return "overdue"
        return "sent"
    return invoice.status  # draft — should not appear in reconciliation views
```

This function is also a pure function — directly testable.

---

## 8. Views / UI contract

### 8.1 Navigation

New top-level sidebar entry: **"Zahlungsabgleich"** — links to the monthly reconciliation view.

### 8.2 Monthly reconciliation view

**URL:** `/reconciliation?year=YYYY&month=MM`

**Table columns:** Invoice #, Customer, Amount, Sent date, Due date, Status (paid / overdue / unpaid), Paid on, Days overdue

**Behaviour:**
- Only shows `sent` and `paid` invoices (drafts hidden)
- "Status" uses computed `effective_status()` — never raw stored value
- A paid invoice shows the payment date and a link to the matched transaction
- An overdue invoice shows days past due in red
- Month navigation: previous/next month arrows

**Reconciliation column:** Shows reconciliation state — "Abgeglichen" (paid, auto or manual), "Offen" (unpaid/overdue), "Entwurf" should never appear here.

### 8.3 Per-customer payment overview

**URL:** `/reconciliation/customers/<customer_id>`

Shows all invoices for that customer across all time, grouped by year, with the same status logic.

### 8.4 Unmatched transactions list

**URL:** `/reconciliation/unmatched`

Shows all `CamtTransaction` records where `match_status == unmatched` or `match_status == unmatched` after manual dismissal was reverted.

**Columns:** Date, Amount, Debtor name, Debtor IBAN, Verwendungszweck, Actions

**Actions per row:**
- "Link to invoice" → opens a search/select modal to manually link to any sent invoice
- "Ignore" → sets `match_status = ignored`, removes from this list

### 8.5 Manual review queue

**URL:** `/reconciliation/review`

Shows transactions in `match_status == unmatched` that have a suggested invoice (Tier 2 or 3 match). Each row shows the suggested invoice and confidence. User can confirm, reject, or link to a different invoice.

### 8.6 CAMT import

**URL:** `/reconciliation/import`

File upload form. Accepts `.xml`. On submit: calls import service, displays `ImportSummary` as a toast/result panel.

---

## 9. YAML storage

| File | Key | Description |
|---|---|---|
| `data/camt_transactions.yaml` | `transaction_id` (string) | All imported CAMT entries |
| `data/invoices.yaml` | `id` (int) | Extended with `paid_at`, `payment_transaction_id` |

---

## 10. Implementation order (TDD sequence)

1. **Models** — `InvoiceStatus` extension, `Invoice` new fields, `CamtTransaction`, `MatchStatus`, `MatchConfidence`, `MatchResult`, `ImportSummary`
2. **Parser** — `parse_camt053(xml_bytes) -> list[CamtTransaction]`; tested with fixture XML files
3. **`effective_status()`** — pure function; tested against all status/date combinations
4. **Matcher** — `match_transaction()`; tested against fixture table (§5)
5. **Import service** — `import_camt_file()`; tested with mock store
6. **Router** — `/reconciliation/*` endpoints; tested with `AsyncClient`
7. **Templates** — monthly view, unmatched list, review queue, import form

---

## 11. Out of scope (explicitly)

- Partial payments (amount < invoice amount)
- Multiple invoices paid in one transfer (auto-split)
- CAMT.052 / CAMT.054 support (parser namespace registry is ready for it, but no UI)
- Email notifications for overdue invoices
