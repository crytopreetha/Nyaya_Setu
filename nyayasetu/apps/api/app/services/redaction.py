"""
Redacts personally identifiable numbers/contacts from text BEFORE it is sent
to any external language-model API (Section 12.1, item 5: "Redact Aadhaar
numbers, bank-account numbers, phone numbers, and email addresses before
sending text to the model when those values are not needed").

This runs only on the copy of the text sent to the LLM — local processing
(date extraction, the deterministic risk engine, retrieval queries) keeps
working on the original, unredacted text, since none of that leaves the
server.
"""
import re

EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# Indian mobile numbers: optional +91/0 prefix, then 10 digits starting 6-9.
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[\s-]?|0)?[6-9]\d{9}(?!\d)")

# Aadhaar: 12 digits, often grouped in 4s with spaces or hyphens.
AADHAAR_PATTERN = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")

# Catch-all for other long digit runs (bank/account numbers), checked last
# so it doesn't eat into Aadhaar/phone matches already replaced.
GENERIC_ACCOUNT_PATTERN = re.compile(r"(?<!\d)\d{9,18}(?!\d)")


def redact_pii(text: str) -> str:
    """Returns a copy of `text` with emails, Aadhaar-shaped numbers, Indian
    phone numbers, and other long digit runs (bank/account numbers)
    replaced with clearly-labelled placeholders. Order matters: more
    specific patterns run first so a generic account-number replacement
    doesn't clobber an Aadhaar or phone match first."""
    redacted = EMAIL_PATTERN.sub("[REDACTED-EMAIL]", text)
    redacted = AADHAAR_PATTERN.sub("[REDACTED-AADHAAR-NUMBER]", redacted)
    redacted = PHONE_PATTERN.sub("[REDACTED-PHONE-NUMBER]", redacted)
    redacted = GENERIC_ACCOUNT_PATTERN.sub("[REDACTED-ACCOUNT-NUMBER]", redacted)
    return redacted
