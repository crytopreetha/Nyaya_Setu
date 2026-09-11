from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Case, LawyerProfile, RiskItem, User
from app.schemas.schemas import (
    LawyerProfileCreate,
    LawyerProfileOut,
    CaseListingOut,
)
from app.services.auth import get_current_user
from app.services.risk_engine import highest_severity

router = APIRouter(prefix="/api/lawyers", tags=["lawyers"])


def _require_lawyer(db: Session, user: User) -> LawyerProfile:
    profile = db.query(LawyerProfile).filter(LawyerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=403, detail="Register as a lawyer first.")
    return profile


@router.post("/me", response_model=LawyerProfileOut, status_code=201)
def register_lawyer(
    payload: LawyerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(LawyerProfile).filter(LawyerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a lawyer profile.")

    profile = LawyerProfile(
        user_id=current_user.id,
        full_name=payload.full_name,
        bar_registration_number=payload.bar_registration_number,
        practice_domains=payload.practice_domains,
        city=payload.city,
        state=payload.state,
        languages=payload.languages,
        bio=payload.bio,
        phone=payload.phone,
        verified=False,  # see README: real Bar Council verification is a follow-up, not in this prototype
    )
    db.add(profile)
    current_user.role = "lawyer"
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=LawyerProfileOut)
def get_my_lawyer_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _require_lawyer(db, current_user)


@router.get("/cases", response_model=list[CaseListingOut])
def browse_open_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cases the citizen has explicitly opted to share, not yet claimed,
    filtered to this lawyer's declared practice domains."""
    profile = _require_lawyer(db, current_user)

    cases = (
        db.query(Case)
        .filter(
            Case.shared_for_lawyer_review == True,  # noqa: E712
            Case.claimed_by_lawyer_id.is_(None),
            Case.status == "ready",
            Case.domain.in_(profile.practice_domains),
        )
        .order_by(Case.created_at.desc())
        .all()
    )

    out = []
    for case in cases:
        risk_items = db.query(RiskItem).filter(RiskItem.case_id == case.id).all()
        severity = highest_severity([{"severity": r.severity} for r in risk_items]) if risk_items else None
        out.append(
            CaseListingOut(
                id=case.id,
                domain=case.domain,
                title=case.title,
                summary=None,  # deliberately omitted from the browse list; full analysis only after claiming
                highest_severity=severity,
                created_at=case.created_at,
            )
        )
    return out


@router.post("/cases/{case_id}/claim", response_model=CaseListingOut)
def claim_case(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = _require_lawyer(db, current_user)

    case = db.get(Case, case_id)
    if not case or not case.shared_for_lawyer_review or case.status != "ready":
        raise HTTPException(status_code=404, detail="Case not available")
    if case.claimed_by_lawyer_id:
        raise HTTPException(status_code=409, detail="This case has already been claimed by another lawyer.")
    if case.domain not in profile.practice_domains:
        raise HTTPException(status_code=403, detail="This case is outside your declared practice domains.")

    case.claimed_by_lawyer_id = profile.id
    case.claimed_at = datetime.utcnow()
    db.commit()

    return CaseListingOut(
        id=case.id, domain=case.domain, title=case.title, summary=None,
        highest_severity=None, created_at=case.created_at,
    )


@router.get("/cases/{case_id}/full")
def get_claimed_case_detail(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Full case detail — visible only to the lawyer who has actually
    claimed this specific case, never before a claim, and never to any
    other lawyer."""
    from app.models import Fact, Deadline, ActionItem, Source

    profile = _require_lawyer(db, current_user)
    case = db.get(Case, case_id)
    if not case or case.claimed_by_lawyer_id != profile.id:
        raise HTTPException(status_code=404, detail="Case not found or not claimed by you.")

    facts = db.query(Fact).filter(Fact.case_id == case_id).all()
    risk_items = db.query(RiskItem).filter(RiskItem.case_id == case_id).all()
    deadlines = db.query(Deadline).filter(Deadline.case_id == case_id).all()
    action_items = db.query(ActionItem).filter(ActionItem.case_id == case_id).order_by(ActionItem.position).all()

    def _source(sid: str):
        s = db.get(Source, sid)
        return {"title": s.title, "url": s.url} if s else {"title": sid, "url": ""}

    return {
        "case_id": case.id,
        "domain": case.domain,
        "title": case.title,
        "facts": [{"fact_type": f.fact_type, "value": f.value, "confidence": f.confidence} for f in facts],
        "risk_items": [
            {
                "title": r.title,
                "severity": r.severity,
                "explanation": r.explanation,
                "is_inference": r.is_inference,
                "sources": [{**_source(c.source_id)} for c in r.citations],
            }
            for r in risk_items
        ],
        "important_dates": [{"label": d.label, "date": d.date, "status": d.status} for d in deadlines],
        "next_steps": [{"text": a.text, "reason": a.reason} for a in action_items],
    }
