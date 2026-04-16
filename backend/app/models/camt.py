from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class MatchStatus(StrEnum):
    unmatched = "unmatched"
    auto_matched = "auto_matched"
    manually_matched = "manually_matched"
    ignored = "ignored"


class MatchConfidence(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class CamtTransaction(BaseModel):
    credit_debit: Literal["CRDT", "DBIT"]
    debtor_name: str | None = None
    debtor_iban: str | None = None
    remittance_info: str | None = None
    match_status: MatchStatus = MatchStatus.unmatched
    matched_invoice_id: int | None = None
    matched_at: datetime | None = None
    match_confidence: MatchConfidence | None = None


class MatchResult(BaseModel):
    confidence: MatchConfidence | None
    invoice_id: int | None


class ImportSummary(BaseModel):
    total_parsed: int
    imported: int
    skipped_duplicates: int
