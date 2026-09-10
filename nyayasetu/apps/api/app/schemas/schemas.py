from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

Domain = Literal[
    "rental_tenancy", "employment", "consumer_disputes", "cyber_fraud", "general_notice"
]
CaseStatus = Literal["created", "extracting", "analyzing", "ready", "failed", "deleted"]
Severity = Literal["informational", "attention", "urgent", "emergency"]


class CaseCreate(BaseModel):
    domain: Domain
    title: Optional[str] = None
    input_type: Literal["document", "text", "audio"] = "text"
    text_input: Optional[str] = None
    language: str = "en"
    consent: bool = Field(..., description="Must be true — user accepted the privacy notice")


class CaseOut(BaseModel):
    id: str
    title: str
    domain: str
    input_type: str
    status: CaseStatus
    created_at: datetime

    class Config:
        from_attributes = True


class CaseStatusOut(BaseModel):
    id: str
    status: CaseStatus
    error_message: Optional[str] = None


class FactOut(BaseModel):
    id: str
    fact_type: str
    value: str
    source_page: Optional[int] = None
    confidence: str
    user_edited: bool

    class Config:
        from_attributes = True


class FactUpdate(BaseModel):
    id: str
    value: str


class CitationOut(BaseModel):
    source_id: str
    title: str
    url: str
    quote: Optional[str] = None
    page: Optional[int] = None


class RiskItemOut(BaseModel):
    id: str
    title: str
    severity: Severity
    explanation: str
    is_inference: bool
    citations: list[CitationOut]

    class Config:
        from_attributes = True


class DeadlineOut(BaseModel):
    id: str
    label: str
    date: Optional[str]
    confidence: str
    basis: Optional[str]
    status: str

    class Config:
        from_attributes = True


class ActionItemOut(BaseModel):
    id: str
    position: int
    text: str
    reason: Optional[str]
    official_url: Optional[str]
    completed: bool

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    case_id: str
    status: CaseStatus
    domain: str
    summary: Optional[str] = None
    document_type: Optional[str] = None
    facts: list[FactOut] = []
    risk_items: list[RiskItemOut] = []
    important_dates: list[DeadlineOut] = []
    next_steps: list[ActionItemOut] = []
    low_quality_pages: list[int] = []
    disclaimer: Optional[str] = None


class SourceOut(BaseModel):
    id: str
    title: str
    url: str
    publisher: Optional[str]
    jurisdiction: Optional[str]
    topic: Optional[str]
    verification_status: str

    class Config:
        from_attributes = True


class ReferralOut(BaseModel):
    need: str
    action: str
    source: SourceOut


class DraftCreate(BaseModel):
    draft_type: Literal["response_letter", "complaint_summary", "evidence_summary"] = "response_letter"


class DraftOut(BaseModel):
    id: str
    draft_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="At least 8 characters")


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    preferred_language: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TranscriptionOut(BaseModel):
    text: str
    language: Optional[str] = None
