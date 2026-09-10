"""
Wraps the language-model calls described in Section 8. If OPENAI_API_KEY is
unset, MockLLM produces a deterministic, clearly-labelled offline response so
the whole pipeline (and demo) still works without any external credentials —
see README's simplification table.
"""
import json
import re
from abc import ABC, abstractmethod

from app.config import get_settings
from app.services.redaction import redact_pii
from app.services.retrieval import RetrievedChunk

settings = get_settings()

AMOUNT_PATTERN = re.compile(r"(?:₹|rs\.?|inr)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)

SYSTEM_PROMPT = """You are the analysis component of NyayaSetu, a preventive \
legal-information tool for Indian citizens. You are not a lawyer and must \
never give legal advice or predict a court outcome. You will be given \
extracted document/incident text and a set of retrieved official source \
chunks with their source_id. Respond with ONLY a single JSON object matching \
this schema, nothing else:

{
  "summary": "plain-language summary of the situation, 2-4 sentences",
  "document_type": "one of: rental_notice | employment_notice | consumer_complaint | cyber_fraud_incident | general_legal_notice",
  "facts": [
    {
      "fact_type": "party | date | amount | location | demand | document_type | organization | channel | harm | desired_outcome | immediate_danger | other",
      "value": "short extracted value, e.g. a person's role, an amount, a place, what the person wants to happen",
      "source_page": 1,
      "confidence": "low | medium | high"
    }
  ],
  "risk_items": [
    {
      "title": "short title",
      "severity": "informational | attention | urgent | emergency",
      "explanation": "plain-language explanation",
      "evidence": [{"page": 1, "quote": "short quote under 15 words from the input text"}],
      "source_ids": ["must be one of the retrieved source_id values, or empty if is_inference is true"],
      "is_inference": false
    }
  ],
  "important_dates": [
    {"label": "what the date is for", "date": "YYYY-MM-DD or null if unresolved", "confidence": "low|medium|high", "basis": "why you think this is the date"}
  ],
  "next_steps": [
    {"step": 1, "action": "what to do", "reason": "why", "official_url": "https://... or null"}
  ],
  "disclaimer": "This is legal information, not legal advice. Consult a qualified advocate or your nearest legal-aid authority for advice on your specific situation."
}

Rules:
- Pull out every fact you can find that fits the incident-structuring \
categories above (party, organization, location, amount, channel, harm, \
desired_outcome, immediate_danger) — this is what lets the user verify and \
correct what you understood before anything else happens.
- Every risk_items entry needs at least one source_id from the retrieved \
sources, UNLESS is_inference is true (then source_ids must be empty).
- Never invent a source_id that wasn't given to you.
- Never fabricate a date; if you cannot find one in the text, set date to null.
- Some identifiers in the input may already be replaced with \
[REDACTED-...] placeholders — never try to guess, reconstruct, or comment \
on what they might have been.
- Keep the tone calm, plain-language, and non-alarmist even for urgent items.
- Output ONLY the JSON object, no markdown fences, no commentary.
"""


class BaseLLM(ABC):
    @abstractmethod
    def generate_grounded_response(
        self, extracted_text: str, domain: str, retrieved: list[RetrievedChunk]
    ) -> dict:
        ...


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base)

    def generate_grounded_response(
        self, extracted_text: str, domain: str, retrieved: list[RetrievedChunk]
    ) -> dict:
        # Section 12.1: strip Aadhaar/phone/bank-account/email before this
        # text leaves the server to an external API. Local steps (dates,
        # deterministic risk checks, retrieval) already ran on the original
        # text before this point, so nothing local loses accuracy.
        safe_text = redact_pii(extracted_text)

        sources_block = "\n".join(
            f"- source_id: {c.source_id} | {c.source_title} ({c.source_url})\n  \"{c.content}\""
            for c in retrieved
        ) or "(no sources retrieved for this topic)"

        user_prompt = f"""Domain: {domain}

Retrieved sources:
{sources_block}

Extracted text (page markers like [page 1] indicate source pages; some
identifiers have been redacted for privacy and appear as [REDACTED-...] —
do not attempt to guess or reconstruct them):
---
{safe_text[:8000]}
---

Return the JSON object now."""

        response = self.client.chat.completions.create(
            model=settings.openai_model_explanation,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        return _parse_json_relaxed(raw)


def _parse_json_relaxed(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return json.loads(raw)


class MockLLM(BaseLLM):
    """Deterministic, rule-driven fallback used when no API key is configured.
    Produces a valid GroundedResponse so the rest of the pipeline (validation,
    risk engine, deadlines) is fully exercised in offline demos."""

    DOMAIN_TO_DOCTYPE = {
        "rental_tenancy": "rental_notice",
        "employment": "employment_notice",
        "consumer_disputes": "consumer_complaint",
        "cyber_fraud": "cyber_fraud_incident",
        "general_notice": "general_legal_notice",
    }

    def generate_grounded_response(
        self, extracted_text: str, domain: str, retrieved: list[RetrievedChunk]
    ) -> dict:
        from app.services.dates import find_candidate_date_strings, normalize_date

        doc_type = self.DOMAIN_TO_DOCTYPE.get(domain, "general_legal_notice")
        candidates = find_candidate_date_strings(extracted_text)
        important_dates = []
        facts = []
        for raw_date in candidates[:3]:
            iso = normalize_date(raw_date)
            important_dates.append(
                {
                    "label": "Date mentioned in the document",
                    "date": iso,
                    "confidence": "medium" if iso else "low",
                    "basis": f"Text contains the date-like phrase '{raw_date}'",
                }
            )
            facts.append(
                {
                    "fact_type": "date",
                    "value": raw_date,
                    "source_page": None,
                    "confidence": "medium" if iso else "low",
                }
            )

        for amount_match in AMOUNT_PATTERN.findall(extracted_text)[:3]:
            facts.append(
                {"fact_type": "amount", "value": amount_match.strip(), "source_page": None, "confidence": "medium"}
            )

        facts.append(
            {
                "fact_type": "document_type",
                "value": doc_type.replace("_", " "),
                "source_page": None,
                "confidence": "medium",
            }
        )

        risk_items = []
        top_source = retrieved[0] if retrieved else None
        if top_source:
            risk_items.append(
                {
                    "title": "Review recommended against official guidance",
                    "severity": "attention",
                    "explanation": (
                        "Running in offline mode (no language model key configured), so this is a "
                        "template review rather than a document-specific reading. Compare your "
                        f"document against: {top_source.content[:220]}"
                    ),
                    "evidence": [],
                    "source_ids": [top_source.source_id],
                    "is_inference": False,
                }
            )
        else:
            risk_items.append(
                {
                    "title": "No matching official source found",
                    "severity": "informational",
                    "explanation": (
                        "Offline mode could not match this case to a curated source. This is an "
                        "inference, not a verified legal claim — treat it as a prompt to seek advice, "
                        "not a finding."
                    ),
                    "evidence": [],
                    "source_ids": [],
                    "is_inference": True,
                }
            )

        return {
            "summary": (
                "This is an offline placeholder summary (no OPENAI_API_KEY configured). "
                "Configure one in .env for a document-specific, model-generated summary."
            ),
            "document_type": doc_type,
            "facts": facts,
            "risk_items": risk_items,
            "important_dates": important_dates,
            "next_steps": [
                {
                    "step": 1,
                    "action": "Keep the original document and any proof of when you received it",
                    "reason": "These materials may be needed later to verify dates or claims",
                    "official_url": None,
                }
            ],
            "disclaimer": (
                "This is legal information, not legal advice. Consult a qualified advocate or "
                "your nearest legal-aid authority for advice on your specific situation."
            ),
        }


def get_llm() -> BaseLLM:
    if settings.llm_enabled:
        return OpenAICompatibleLLM()
    return MockLLM()
