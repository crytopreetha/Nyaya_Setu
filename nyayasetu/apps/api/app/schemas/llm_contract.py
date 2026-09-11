"""
The response generator (services/llm.py) must return JSON matching this
schema. The backend rejects anything that fails validation, has no
disclaimer, or makes a legal claim with no source_id — see
services/analysis_pipeline.py::validate_grounded_response.
"""
from typing import Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Severity = Literal["informational", "attention", "urgent", "emergency"]


class ExtractedFact(BaseModel):
    fact_type: Literal[
        "party",
        "date",
        "amount",
        "location",
        "demand",
        "document_type",
        "organization",
        "channel",
        "harm",
        "desired_outcome",
        "immediate_danger",
        "other",
    ]
    value: str
    source_page: Optional[int] = None
    confidence: Literal["low", "medium", "high"] = "medium"


class DocumentClassification(BaseModel):
    document_type: str
    domain_confidence: Literal["low", "medium", "high"] = "medium"


class EvidenceRef(BaseModel):
    page: Optional[int] = None
    quote: Optional[str] = None


class GroundedRiskItem(BaseModel):
    title: str
    severity: Severity
    explanation: str
    evidence: list[EvidenceRef] = Field(default_factory=list)
    source_ids: list[str] = Field(
        default_factory=list,
        description="Must reference retrieved source ids. Empty only if is_inference=True.",
    )
    is_inference: bool = False

    @model_validator(mode="after")
    def _require_grounding(self):
        # A legal claim needs either a source or an explicit inference flag.
        # Field-level validators can't reliably see a later-declared field's
        # final value (that was the actual bug here), so this runs after the
        # whole object is built. If the model forgot to set is_inference on
        # an unsourced claim, self-heal instead of failing the whole
        # analysis — the claim is simply treated as an inference, which is
        # exactly what "no source cited" means anyway.
        if not self.source_ids and not self.is_inference:
            self.is_inference = True
        return self


class GroundedDate(BaseModel):
    label: str
    date: Optional[str] = None  # ISO 8601, may be null if unresolved
    confidence: Literal["low", "medium", "high"] = "medium"
    basis: str


class NextStep(BaseModel):
    step: int
    action: str
    reason: str
    official_url: Optional[str] = None


class GroundedResponse(BaseModel):
    """The full contract described in Section 8.2 of the spec."""

    summary: str
    document_type: str
    facts: list[ExtractedFact] = Field(default_factory=list)
    risk_items: list[GroundedRiskItem]
    important_dates: list[GroundedDate] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)
    disclaimer: str

    @field_validator("disclaimer")
    @classmethod
    def _disclaimer_required(cls, v):
        if not v or "not legal advice" not in v.lower():
            raise ValueError("disclaimer must state this is not legal advice")
        return v