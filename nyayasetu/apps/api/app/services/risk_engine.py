"""
Combines the model's classification with deterministic keyword/rule checks.
These checks run independently of the LLM and can only ADD risk items or
escalate an emergency banner — they never suppress a model finding. This is
what makes an incorrect model response unable to silently downgrade a real
danger (Section 4.2 / 12.2 threat model: "Unsafe advice in an emergency").
"""
import re

EMERGENCY_PATTERNS = [
    r"\bthreat(?:en(?:ed|ing)?)?\s+(?:to\s+)?(?:kill|harm|hurt)\b",
    r"\bsuicid",
    r"\bdomestic violence\b",
    r"\bin (?:immediate|physical) danger\b",
    r"\bassault(?:ed)?\b",
]

URGENT_FINANCIAL_LOSS_PATTERN = re.compile(
    r"\b(?:lost|transferred|debited)\s+(?:rs\.?|inr|₹)?\s?[\d,]+\b", re.IGNORECASE
)

DEPOSIT_CLAUSE_PATTERN = re.compile(
    r"\bsecurity deposit\b.{0,80}\b(damages|deduct|wear and tear)\b",
    re.IGNORECASE | re.DOTALL,
)

RESPONSE_DEADLINE_PATTERN = re.compile(
    r"\brespond(?:\s+in\s+writing)?\s+within\b|\bvacate\b.{0,40}\bwithin\b",
    re.IGNORECASE,
)

UNEXPLAINED_DEDUCTION_PATTERN = re.compile(
    r"\bdeduct(?:ed|ion)?\b.{0,60}\b(salary|wages|pay)\b", re.IGNORECASE | re.DOTALL
)


def check_emergency(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in EMERGENCY_PATTERNS)


def deterministic_checks(text: str, domain: str) -> list[dict]:
    """Returns extra risk_items in the same shape the LLM contract expects,
    each marked is_inference=True with an empty source list unless a real
    source is obviously applicable — these are triage flags, not citations."""
    findings: list[dict] = []

    if check_emergency(text):
        findings.append(
            {
                "title": "Possible immediate safety concern detected",
                "severity": "emergency",
                "explanation": (
                    "The description contains language suggesting a possible immediate threat to "
                    "physical safety. If you are in danger right now, contact local police (112) "
                    "or, for cyber-enabled financial fraud, call the 1930 helpline immediately."
                ),
                "evidence": [],
                "source_ids": [],
                "is_inference": True,
            }
        )

    if domain == "cyber_fraud" and URGENT_FINANCIAL_LOSS_PATTERN.search(text):
        findings.append(
            {
                "title": "Financial loss mentioned — time-sensitive",
                "severity": "urgent",
                "explanation": (
                    "A specific monetary loss is mentioned. Reporting promptly (within the first "
                    "hour where possible) materially improves the chance of freezing the funds."
                ),
                "evidence": [],
                "source_ids": ["source-ncrp-002"],
                "is_inference": False,
            }
        )

    if domain == "rental_tenancy" and DEPOSIT_CLAUSE_PATTERN.search(text):
        findings.append(
            {
                "title": "Security-deposit clause may need scrutiny",
                "severity": "attention",
                "explanation": (
                    "The document references deductions from the security deposit for damages or "
                    "wear and tear without (from what's visible) an itemised list — a common source "
                    "of disputes."
                ),
                "evidence": [],
                "source_ids": ["source-rental-general-001"],
                "is_inference": False,
            }
        )

    if domain == "rental_tenancy" and RESPONSE_DEADLINE_PATTERN.search(text):
        findings.append(
            {
                "title": "Response or vacate deadline detected",
                "severity": "attention",
                "explanation": (
                    "The notice appears to set a deadline to respond or vacate. Confirm the exact "
                    "date in the Important Dates card and keep proof of when you received the notice."
                ),
                "evidence": [],
                "source_ids": ["source-rental-general-001"],
                "is_inference": False,
            }
        )

    if domain == "employment" and UNEXPLAINED_DEDUCTION_PATTERN.search(text):
        findings.append(
            {
                "title": "Unexplained salary deduction referenced",
                "severity": "attention",
                "explanation": (
                    "A deduction from salary or wages is mentioned. Raise it in writing with the "
                    "employer first, and keep payslips as evidence."
                ),
                "evidence": [],
                "source_ids": ["source-employment-general-001"],
                "is_inference": False,
            }
        )

    return findings


def merge_risk_items(model_items: list[dict], deterministic_items: list[dict]) -> list[dict]:
    """De-duplicates by title (case-insensitive) — deterministic items win on
    conflict since they're rule-based rather than probabilistic."""
    seen_titles = {d["title"].strip().lower() for d in deterministic_items}
    merged = list(deterministic_items)
    for item in model_items:
        if item["title"].strip().lower() not in seen_titles:
            merged.append(item)
    return merged


SEVERITY_ORDER = {"informational": 0, "attention": 1, "urgent": 2, "emergency": 3}


def highest_severity(risk_items: list[dict]) -> str:
    if not risk_items:
        return "informational"
    return max(risk_items, key=lambda r: SEVERITY_ORDER.get(r["severity"], 0))["severity"]
