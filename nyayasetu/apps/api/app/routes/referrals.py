from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Source
from app.schemas.schemas import ReferralOut, SourceOut
from app.services.referrals import get_referrals_for_domain

router = APIRouter(prefix="/api/referrals", tags=["referrals"])


@router.get("", response_model=list[ReferralOut])
def get_referrals(domain: str = Query(...), db: Session = Depends(get_db)):
    entries = get_referrals_for_domain(domain)
    out = []
    for entry in entries:
        source = db.get(Source, entry["source_id"])
        if not source:
            continue
        out.append(
            ReferralOut(
                need=entry["need"],
                action=entry["action"],
                source=SourceOut.model_validate(source),
            )
        )
    return out
