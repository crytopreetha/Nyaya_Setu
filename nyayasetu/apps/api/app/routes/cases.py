import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Case, Fact, Deadline, RiskItem, ActionItem, Extraction, User
from app.schemas.schemas import (
    CaseCreate,
    CaseOut,
    CaseStatusOut,
    AnalysisOut,
    FactUpdate,
    FactOut,
)
from app.services.auth import get_current_user
from app.services.analysis_pipeline import run_analysis
from app.services.storage import delete_case_files

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _get_owned_case(db: Session, case_id: str, user: User) -> Case:
    """Fetches a case and checks it belongs to the current user. Returns 404
    (not 403) on mismatch so an attacker can't tell a case exists at all."""
    case = db.get(Case, case_id)
    if not case or case.status == "deleted" or case.user_id != user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("", response_model=CaseOut, status_code=201)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Consent is required before a case can be created.")

    case = Case(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=payload.title or "Untitled case",
        domain=payload.domain,
        input_type=payload.input_type,
        text_input=payload.text_input,
        status="created",
        consent_at=datetime.utcnow(),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Case)
        .filter(Case.user_id == current_user.id, Case.status != "deleted")
        .order_by(Case.created_at.desc())
        .all()
    )


@router.get("/{case_id}/status", response_model=CaseStatusOut)
def get_status(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = _get_owned_case(db, case_id, current_user)
    return CaseStatusOut(id=case.id, status=case.status, error_message=case.error_message)


@router.post("/{case_id}/analyze", response_model=CaseStatusOut)
def start_analysis(
    case_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = _get_owned_case(db, case_id, current_user)
    if case.status not in ("created", "failed"):
        return CaseStatusOut(id=case.id, status=case.status, error_message=case.error_message)

    case.status = "extracting"
    case.error_message = None
    db.commit()
    background_tasks.add_task(run_analysis, case_id)
    return CaseStatusOut(id=case.id, status=case.status)


@router.get("/{case_id}/analysis", response_model=AnalysisOut)
def get_analysis(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = _get_owned_case(db, case_id, current_user)

    facts = db.query(Fact).filter(Fact.case_id == case_id).all()
    risk_items = db.query(RiskItem).filter(RiskItem.case_id == case_id).all()
    deadlines = db.query(Deadline).filter(Deadline.case_id == case_id).all()
    action_items = (
        db.query(ActionItem).filter(ActionItem.case_id == case_id).order_by(ActionItem.position).all()
    )
    extractions = db.query(Extraction).filter(Extraction.case_id == case_id).all()
    low_quality_pages = sorted(
        {page for e in extractions for page in (e.low_quality_pages or [])}
    )

    risk_items_out = []
    for r in risk_items:
        citations_out = [
            {
                "source_id": c.source_id,
                "title": _source_title(db, c.source_id),
                "url": _source_url(db, c.source_id),
                "quote": c.quote,
                "page": c.page,
            }
            for c in r.citations
        ]
        risk_items_out.append(
            {
                "id": r.id,
                "title": r.title,
                "severity": r.severity,
                "explanation": r.explanation,
                "is_inference": r.is_inference,
                "citations": citations_out,
            }
        )

    return AnalysisOut(
        case_id=case.id,
        status=case.status,
        domain=case.domain,
        summary=None,
        document_type=case.title,
        facts=[FactOut.model_validate(f) for f in facts],
        risk_items=risk_items_out,
        important_dates=deadlines,
        next_steps=action_items,
        low_quality_pages=low_quality_pages,
        disclaimer=(
            "This is legal information, not legal advice. Consult a qualified advocate or your "
            "nearest legal-aid authority for advice on your specific situation."
        )
        if case.status == "ready"
        else None,
    )


def _source_title(db: Session, source_id: str) -> str:
    from app.models import Source

    s = db.get(Source, source_id)
    return s.title if s else source_id


def _source_url(db: Session, source_id: str) -> str:
    from app.models import Source

    s = db.get(Source, source_id)
    return s.url if s else ""


@router.patch("/{case_id}/facts", response_model=FactOut)
def update_fact(
    case_id: str,
    payload: FactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_case(db, case_id, current_user)
    fact = db.get(Fact, payload.id)
    if not fact or fact.case_id != case_id:
        raise HTTPException(status_code=404, detail="Fact not found for this case")
    fact.value = payload.value
    fact.user_edited = True
    db.commit()
    db.refresh(fact)
    return fact


@router.post("/{case_id}/deadlines/{deadline_id}/confirm")
def confirm_deadline(
    case_id: str,
    deadline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_case(db, case_id, current_user)
    deadline = db.get(Deadline, deadline_id)
    if not deadline or deadline.case_id != case_id:
        raise HTTPException(status_code=404, detail="Deadline not found for this case")
    deadline.status = "confirmed"
    db.commit()
    return {"id": deadline.id, "status": deadline.status}


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = _get_owned_case(db, case_id, current_user)
    delete_case_files(case_id)
    case.status = "deleted"
    db.commit()
    return None
