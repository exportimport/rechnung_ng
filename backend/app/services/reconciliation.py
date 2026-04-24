from datetime import date, timedelta

from app.models.camt import CamtTransaction, MatchConfidence, MatchResult
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus

MIN_NAME_MATCH_OVERLAP = 0.8


def effective_status(invoice: Invoice, today: date, payment_terms_days: int) -> str:
    if invoice.status == InvoiceStatus.paid:
        return "paid"
    if invoice.status == InvoiceStatus.sent and invoice.sent_at is not None:
        due_date = invoice.sent_at.date() + timedelta(days=payment_terms_days)
        if today > due_date:
            return "overdue"
    return invoice.status


def match_transaction(
    transaction: CamtTransaction,
    invoices: list[Invoice],
    customers: list[Customer],
) -> MatchResult:
    remittance = (transaction.remittance_info or "").lower().replace(" ", "")

    # Tier 1 — invoice number in Verwendungszweck
    tier1_matches = [
        inv for inv in invoices
        if inv.invoice_number.lower().replace(" ", "") in remittance
        and round(inv.amount, 2) == round(transaction.amount, 2)
        and inv.status != InvoiceStatus.paid
    ]
    if len(tier1_matches) == 1:
        return MatchResult(
            confidence=MatchConfidence.high,
            invoice_id=tier1_matches[0].id,
            reason=f"invoice number {tier1_matches[0].invoice_number!r} found in Verwendungszweck",
        )

    # Tier 2 — amount + debtor IBAN
    if transaction.debtor_iban:
        customer_by_iban = {c.iban: c for c in customers}
        matched_customer = customer_by_iban.get(transaction.debtor_iban)
        if matched_customer:
            tier2_matches = [
                inv for inv in invoices
                if inv.customer_id == matched_customer.id
                and round(inv.amount, 2) == round(transaction.amount, 2)
                and inv.status != InvoiceStatus.paid
            ]
            if len(tier2_matches) == 1:
                return MatchResult(
                    confidence=MatchConfidence.medium,
                    invoice_id=tier2_matches[0].id,
                    reason="amount and debtor IBAN match",
                )

    # Tier 3 — amount + fuzzy debtor name
    if transaction.debtor_name:
        tx_tokens = set(transaction.debtor_name.lower().split())
        tier3_matches = []
        for inv in invoices:
            if inv.status == InvoiceStatus.paid:
                continue
            if round(inv.amount, 2) != round(transaction.amount, 2):
                continue
            customer = next((c for c in customers if c.id == inv.customer_id), None)
            if customer is None:
                continue
            full_name = f"{customer.vorname} {customer.nachname}".lower()
            cust_tokens = set(full_name.split())
            if not cust_tokens:
                continue
            overlap = len(tx_tokens & cust_tokens) / len(cust_tokens)
            if overlap >= MIN_NAME_MATCH_OVERLAP:
                tier3_matches.append(inv)
        if len(tier3_matches) == 1:
            return MatchResult(
                confidence=MatchConfidence.low,
                invoice_id=tier3_matches[0].id,
                reason="amount and fuzzy name match",
            )

    return MatchResult(confidence=None, invoice_id=None, reason="no match")
