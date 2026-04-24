import hashlib
import xml.etree.ElementTree as ET
from datetime import date, datetime

from app.models.camt import CamtTransaction

SUPPORTED_NAMESPACES = {
    "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08",
}


class UnsupportedNamespaceError(Exception):
    pass


def _tag(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def parse_camt053(xml_bytes: bytes, source_file: str) -> list[CamtTransaction]:
    root = ET.fromstring(xml_bytes)
    ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    if ns not in SUPPORTED_NAMESPACES:
        raise UnsupportedNamespaceError(f"Unsupported namespace: {ns!r}")

    results = []
    now = datetime.now()

    for stmt in root.iter(_tag(ns, "Stmt")):
        for i, entry in enumerate(stmt.findall(_tag(ns, "Ntry"))):
            cdt_dbt_el = entry.find(_tag(ns, "CdtDbtInd"))
            if cdt_dbt_el is None or cdt_dbt_el.text != "CRDT":
                continue

            tx_details = entry.find(f".//{_tag(ns, 'TxDtls')}")
            transaction_id = None
            if tx_details is not None:
                refs = tx_details.find(_tag(ns, "Refs"))
                if refs is not None:
                    svr_ref = refs.find(_tag(ns, "AcctSvcrRef"))
                    if svr_ref is not None and svr_ref.text:
                        transaction_id = svr_ref.text
                    else:
                        e2e = refs.find(_tag(ns, "EndToEndId"))
                        if e2e is not None and e2e.text:
                            transaction_id = e2e.text

            booking_date_el = entry.find(f".//{_tag(ns, 'BookgDt')}")
            booking_date = (
                date.fromisoformat(booking_date_el.find(_tag(ns, "Dt")).text)
                if booking_date_el is not None
                else date.today()
            )

            value_date_el = entry.find(f".//{_tag(ns, 'ValDt')}")
            value_date = (
                date.fromisoformat(value_date_el.find(_tag(ns, "Dt")).text)
                if value_date_el is not None
                else booking_date
            )

            amt_el = entry.find(_tag(ns, "Amt"))
            amount = float(amt_el.text) if amt_el is not None else 0.0
            currency = amt_el.get("Ccy", "EUR") if amt_el is not None else "EUR"

            debtor_name = None
            debtor_iban = None
            remittance_info = None
            if tx_details is not None:
                rltd = tx_details.find(_tag(ns, "RltdPties"))
                if rltd is not None:
                    dbtr = rltd.find(_tag(ns, "Dbtr"))
                    if dbtr is not None:
                        pty = dbtr.find(_tag(ns, "Pty"))
                        if pty is not None:
                            nm = pty.find(_tag(ns, "Nm"))
                            if nm is not None:
                                debtor_name = nm.text
                    dbtr_acct = rltd.find(_tag(ns, "DbtrAcct"))
                    if dbtr_acct is not None:
                        id_el = dbtr_acct.find(_tag(ns, "Id"))
                        if id_el is not None:
                            iban_el = id_el.find(_tag(ns, "IBAN"))
                            if iban_el is not None:
                                debtor_iban = iban_el.text
                rmt = tx_details.find(_tag(ns, "RmtInf"))
                if rmt is not None:
                    ustrd = rmt.find(_tag(ns, "Ustrd"))
                    if ustrd is not None:
                        remittance_info = ustrd.text

            if not transaction_id:
                raw = f"{booking_date}_{amount}_{debtor_iban or 'NOIBAN'}_{remittance_info or ''}"
                transaction_id = "FALLBACK-" + hashlib.sha256(raw.encode()).hexdigest()[:16]

            results.append(
                CamtTransaction(
                    transaction_id=transaction_id,
                    booking_date=booking_date,
                    value_date=value_date,
                    amount=amount,
                    currency=currency,
                    credit_debit="CRDT",
                    debtor_name=debtor_name,
                    debtor_iban=debtor_iban,
                    remittance_info=remittance_info,
                    imported_at=now,
                    source_file=source_file,
                )
            )

    return results
