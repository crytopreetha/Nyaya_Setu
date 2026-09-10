from datetime import datetime
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db  # noqa: F401 (Session type used in signatures below)
from app.models import Case, RiskItem, Deadline, Draft, User
from app.schemas.schemas import DraftCreate, DraftOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["drafts"])

DOMAIN_LABELS = {
    "rental_tenancy": "rental/tenancy matter",
    "employment": "employment matter",
    "consumer_disputes": "consumer complaint",
    "cyber_fraud": "cyber fraud incident",
    "general_notice": "legal notice",
}


def _build_response_letter(case: Case, risk_items: list[RiskItem], deadlines: list[Deadline]) -> str:
    domain_label = DOMAIN_LABELS.get(case.domain, "matter")
    deadline_lines = "\n".join(
        f"- {d.label}: {d.date or 'date not confirmed'}" for d in deadlines
    ) or "- No specific deadline was identified."
    risk_lines = "\n".join(f"- {r.title}: {r.explanation}" for r in risk_items) or "- No specific issues flagged."

    return f"""[DRAFT — NOT SUBMITTED. Review and edit before sending.]

Subject: Response regarding {domain_label}

To whom it may concern,

I am writing in response to the {domain_label} referred to above. I request that
the following points be noted:

{risk_lines}

I note the following date(s) associated with this matter and request written
confirmation if any of them are incorrect:

{deadline_lines}

I am preserving all related documents and correspondence and reserve all my
rights in this matter. Please treat this communication as a good-faith
attempt to resolve the matter directly.

Sincerely,
[Your name]
[Date: {datetime.utcnow().date().isoformat()}]

---
This draft was generated from the information you provided and is NOT legal
advice and NOT submitted anywhere. Have it reviewed — for free, if you're
eligible — by your State Legal Services Authority (helpline 15100) before
sending it.
"""


@router.post("/{case_id}/drafts", response_model=DraftOut)
def create_draft(
    case_id: str,
    payload: DraftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if not case or case.status == "deleted" or case.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status != "ready":
        raise HTTPException(status_code=409, detail="Case analysis is not ready yet.")

    risk_items = db.query(RiskItem).filter(RiskItem.case_id == case_id).all()
    deadlines = db.query(Deadline).filter(Deadline.case_id == case_id).all()

    if payload.draft_type == "response_letter":
        content = _build_response_letter(case, risk_items, deadlines)
    elif payload.draft_type == "evidence_summary":
        content = "[DRAFT — evidence summary]\n\n" + "\n".join(
            f"- {r.title} (severity: {r.severity})" for r in risk_items
        )
    else:
        content = "[DRAFT — complaint summary]\n\n" + "\n".join(
            f"- {r.title}: {r.explanation}" for r in risk_items
        )

    draft = Draft(case_id=case_id, draft_type=payload.draft_type, content=content)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/{case_id}/drafts", response_model=list[DraftOut])
def list_drafts(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if not case or case.status == "deleted" or case.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(Draft).filter(Draft.case_id == case_id).order_by(Draft.created_at.desc()).all()


@router.get("/{case_id}/drafts/{draft_id}/pdf")
def download_draft_pdf(
    case_id: str,
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Renders a draft as a downloadable PDF (Section 6.1: Draft center
    requires 'download as PDF')."""
    from fpdf import FPDF

    case = db.get(Case, case_id)
    if not case or case.status == "deleted" or case.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    draft = db.get(Draft, draft_id)
    if not draft or draft.case_id != case_id:
        raise HTTPException(status_code=404, detail="Draft not found for this case")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    # Encode to latin-1 with replacement since core PDF fonts don't support
    # full Unicode (e.g. the ₹ symbol) — good enough for a plain-text draft.
    safe_text = draft.content.encode("latin-1", "replace").decode("latin-1")
    for line in safe_text.split("\n"):
        pdf.multi_cell(0, 6, line)

    pdf_bytes = bytes(pdf.output())
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="draft-{draft.draft_type}.pdf"'},
    )
