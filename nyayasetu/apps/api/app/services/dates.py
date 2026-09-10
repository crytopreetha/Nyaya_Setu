"""
Deterministic date engine. The model proposes candidate date phrases (as
part of the grounded response); this module is the ordinary-code half from
Section 4.2 — it normalizes whatever the model or a regex pass finds into
ISO dates, and never invents a date the text doesn't support.
"""
import re
from datetime import datetime, timedelta

import dateparser

RELATIVE_PATTERN = re.compile(
    r"within\s+(\d{1,3})\s+(day|days|week|weeks|month|months)", re.IGNORECASE
)

DATE_LIKE_PATTERN = re.compile(
    r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b",
    re.IGNORECASE,
)


def find_candidate_date_strings(text: str) -> list[str]:
    """Cheap regex pass used as a safety net alongside the model's own date
    extraction — catches obvious absolute dates the model might miss."""
    return list(dict.fromkeys(m.group(0) for m in DATE_LIKE_PATTERN.finditer(text)))


def normalize_date(raw: str, reference_date: datetime | None = None) -> str | None:
    """Best-effort normalization to YYYY-MM-DD. Returns None if unparseable —
    callers must not fabricate a date when this happens."""
    settings = {"PREFER_DATES_FROM": "future"}
    if reference_date:
        settings["RELATIVE_BASE"] = reference_date
    parsed = dateparser.parse(raw, settings=settings)
    if not parsed:
        return None
    return parsed.date().isoformat()


def resolve_relative_deadline(text: str, reference_date: datetime | None = None) -> str | None:
    """Handles phrases like 'within 15 days' relative to a reference date
    (e.g. the notice date, or today if the notice date is unknown)."""
    match = RELATIVE_PATTERN.search(text)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    base = reference_date or datetime.utcnow()

    if unit.startswith("day"):
        delta = timedelta(days=amount)
    elif unit.startswith("week"):
        delta = timedelta(weeks=amount)
    else:  # month(s) — approximate as 30 days, flagged as low confidence by the caller
        delta = timedelta(days=amount * 30)

    return (base + delta).date().isoformat()
