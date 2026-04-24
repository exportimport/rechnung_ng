from datetime import datetime

from app.db.yaml_store import YamlStore
from app.models.camt import ImportSummary, MatchConfidence, MatchStatus
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.services.camt_parser import parse_camt053
from app.services.reconciliation import match_transaction


def import_camt_file(xml_bytes: bytes, filename: str, store: YamlStore) -> ImportSummary:
    transactions = parse_camt053(xml_bytes, source_file=filename)

    existing_ids = {r["transaction_id"] for r in store.load("camt_transactions")}
    new_transactions = [tx for tx in transactions if tx.transaction_id not in existing_ids]
    skipped = len(transactions) - len(new_transactions)

    invoices = [Invoice(**d) for d in store.load("invoices")]
    customers = [Customer(**d) for d in store.load("customers")]

    auto_matched = 0
    for tx in new_transactions:
        result = match_transaction(tx, invoices, customers)
        if result.confidence == MatchConfidence.high:
            auto_matched += 1
            tx.match_status = MatchStatus.auto_matched
            tx.matched_invoice_id = result.invoice_id
            tx.match_confidence = result.confidence
            tx.matched_at = datetime.now()
            matched_inv = next(inv for inv in invoices if inv.id == result.invoice_id)
            store.update(
                "invoices",
                matched_inv.id,
                {
                    **matched_inv.model_dump(mode="json"),
                    "status": "paid",
                    "paid_at": tx.booking_date.isoformat(),
                    "payment_transaction_id": tx.transaction_id,
                },
            )
        elif result.confidence is not None:
            tx.match_confidence = result.confidence
            tx.matched_invoice_id = result.invoice_id
        store.create("camt_transactions", tx.model_dump(mode="json"))

    return ImportSummary(
        total_parsed=len(transactions),
        imported=len(new_transactions),
        skipped_duplicates=skipped,
        auto_matched=auto_matched,
    )
