"""
Orchestrates the Section 5.2 processing sequence for one case:
extract -> retrieve -> generate -> validate -> persist.

Runs in-process via FastAPI BackgroundTasks for this prototype (see README
upgrade-path table for swapping in Celery/Redis).
"""
from datetime import datetime

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Case, CaseFile, Extraction, Fact, RiskItem, Citation, Deadline, ActionItem, AuditEvent
from app.services import ingestion, retrieval, risk_engine
from app.services.dates import normalize_date, resolve_relative_deadline
from app.services.llm import get_llm
from app.services.storage import read_file
from app.schemas.llm_contract import GroundedResponse

TOPIC_BY_DOMAIN = {
    "rental_tenancy": "rental_tenancy",
    "employment": "employment",
    "consumer_disputes": "consumer_disputes",
    "cyber_fraud": "cyber_fraud",
    "general_notice": None,  # search across all topics
}


def _log(db: Session, case_id: str, event_type: str, detail: str = "") -> None:
    db.add(AuditEvent(case_id=case_id, event_type=event_type, detail=detail[:500]))
    db.commit()


def validate_grounded_response(raw: dict, retrieved_ids: set[str]) -> GroundedResponse:
    """Validates schema AND that every non-inference risk item cites a real,
    retrieved source_id. Raises ValueError/ValidationError on failure — the
    caller does exactly one repair attempt before giving up."""
    parsed = GroundedResponse.model_validate(raw)
    for item in parsed.risk_items:
        if item.is_inference:
            continue
        unknown = [sid for sid in item.source_ids if sid not in retrieved_ids]
        if unknown:
            raise ValueError(f"risk item cites unknown source_id(s): {unknown}")
    return parsed


def run_analysis(case_id: str) -> None:
    db = SessionLocal()
    try:
        case = db.get(Case, case_id)
        if not case:
            return

        case.status = "extracting"
        db.commit()
        _log(db, case_id, "extraction_started")

        # --- 1. Ingestion / text extraction ---
        full_text_parts = []
        if case.input_type == "text" and case.text_input:
            result = ingestion.extract_from_text(case.text_input)
            full_text_parts.append(result.text)
            db.add(Extraction(case_id=case_id, text=result.text, method=result.method, quality_score=result.quality_score))
        else:
            files = db.query(CaseFile).filter(CaseFile.case_id == case_id).all()
            for f in files:
                content = read_file(f.storage_key)
                result = ingestion.extract(f.mime_type, content)
                full_text_parts.append(result.text)
                db.add(
                    Extraction(
                        case_id=case_id,
                        file_id=f.id,
                        text=result.text,
                        method=result.method,
                        quality_score=result.quality_score,
                        low_quality_pages=result.low_quality_pages,
                    )
                )
        db.commit()

        full_text = "\n\n".join(p for p in full_text_parts if p).strip()
        if not full_text:
            case.status = "failed"
            case.error_message = "No text could be extracted from the input. Try a clearer scan or type a description."
            db.commit()
            _log(db, case_id, "extraction_failed")
            return

        # --- 2. Retrieval ---
        case.status = "analyzing"
        db.commit()
        _log(db, case_id, "analysis_started")

        topic = TOPIC_BY_DOMAIN.get(case.domain)
        retrieved = retrieval.retrieve(db, query=full_text[:2000], topic=topic)
        retrieved_ids = {c.source_id for c in retrieved}

        # --- 3. Grounded generation (with one repair attempt) ---
        llm = get_llm()
        raw_response = llm.generate_grounded_response(full_text, case.domain, retrieved)
        try:
            grounded = validate_grounded_response(raw_response, retrieved_ids)
        except (ValidationError, ValueError) as e:
            _log(db, case_id, "validation_failed_retry", str(e))
            # One repair attempt: ask again (mock LLM is deterministic so this
            # mainly matters for the real API path).
            raw_response = llm.generate_grounded_response(full_text, case.domain, retrieved)
            try:
                grounded = validate_grounded_response(raw_response, retrieved_ids)
            except (ValidationError, ValueError) as e2:
                case.status = "failed"
                case.error_message = "The analysis could not be validated safely. Please try again."
                db.commit()
                _log(db, case_id, "validation_failed_final", str(e2))
                return

        # --- 4. Deterministic risk engine merge ---
        deterministic_items = risk_engine.deterministic_checks(full_text, case.domain)
        model_items = [item.model_dump() for item in grounded.risk_items]
        merged_items = risk_engine.merge_risk_items(model_items, deterministic_items)

        # --- 5. Persist structured facts (Section 7.3 incident structuring —
        # the user can review and correct every one of these via PATCH /facts) ---
        for fact_item in grounded.facts:
            db.add(
                Fact(
                    case_id=case_id,
                    fact_type=fact_item.fact_type,
                    value=fact_item.value,
                    source_page=fact_item.source_page,
                    confidence=fact_item.confidence,
                )
            )

        # --- 6. Persist risk items + citations ---
        source_lookup = {c.source_id: c for c in retrieved}
        for item in merged_items:
            risk_item = RiskItem(
                case_id=case_id,
                title=item["title"],
                severity=item["severity"],
                explanation=item["explanation"],
                evidence=item.get("evidence", []),
                is_inference=item.get("is_inference", False),
            )
            db.add(risk_item)
            db.flush()  # get risk_item.id
            for sid in item.get("source_ids", []):
                chunk = source_lookup.get(sid)
                db.add(
                    Citation(
                        risk_item_id=risk_item.id,
                        source_id=sid,
                        quote=chunk.content[:300] if chunk else None,
                    )
                )

        # --- 7. Persist deadlines, filling gaps with the deterministic date engine ---
        reference_date = case.created_at or datetime.utcnow()
        for date_item in grounded.important_dates:
            iso_date = date_item.date or normalize_date(date_item.basis, reference_date) or resolve_relative_deadline(
                full_text, reference_date
            )
            db.add(
                Deadline(
                    case_id=case_id,
                    label=date_item.label,
                    date=iso_date,
                    confidence=date_item.confidence if iso_date else "low",
                    basis=date_item.basis,
                )
            )

        # --- 8. Persist action plan ---
        for step in grounded.next_steps:
            db.add(
                ActionItem(
                    case_id=case_id,
                    position=step.step,
                    text=step.action,
                    reason=step.reason,
                    official_url=step.official_url,
                )
            )

        case.title = case.title or grounded.document_type.replace("_", " ").title()
        case.status = "ready"
        db.commit()
        _log(db, case_id, "analysis_ready")

    except Exception as e:  # noqa: BLE001 — top-level guard so a case never hangs at "analyzing"
        db.rollback()
        case = db.get(Case, case_id)
        if case:
            case.status = "failed"
            case.error_message = f"Unexpected error during analysis: {e}"
            db.commit()
        _log(db, case_id, "analysis_error", str(e))
    finally:
        db.close()
