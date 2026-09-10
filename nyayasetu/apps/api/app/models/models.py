import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db import Base

EMBEDDING_DIM = 384  # matches fastembed's BAAI/bge-small-en-v1.5


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    preferred_language = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="Untitled case")
    domain = Column(String, nullable=False)  # rental_tenancy | employment | consumer_disputes | cyber_fraud | general_notice
    input_type = Column(String, nullable=False, default="document")  # document | text | audio
    text_input = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="created")
    # created -> extracting -> analyzing -> ready -> failed -> deleted
    consent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cases")
    files = relationship("CaseFile", back_populates="case", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="case", cascade="all, delete-orphan")
    facts = relationship("Fact", back_populates="case", cascade="all, delete-orphan")
    risk_items = relationship("RiskItem", back_populates="case", cascade="all, delete-orphan")
    deadlines = relationship("Deadline", back_populates="case", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="case", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="case", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="case", cascade="all, delete-orphan")


class CaseFile(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    storage_key = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="files")


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    file_id = Column(UUID(as_uuid=False), ForeignKey("files.id"), nullable=True)
    text = Column(Text, nullable=False, default="")
    language = Column(String, default="en")
    method = Column(String, default="native_text")  # native_text | ocr | manual_text
    quality_score = Column(Float, nullable=True)
    low_quality_pages = Column(JSON, nullable=True)  # list[int]
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="extractions")


class Fact(Base):
    __tablename__ = "facts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    fact_type = Column(String, nullable=False)  # party | date | amount | location | demand | document_type | other
    value = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    confidence = Column(String, default="medium")  # low | medium | high
    user_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="facts")


class RiskItem(Base):
    __tablename__ = "risk_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # informational | attention | urgent | emergency
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # [{"page": 1, "quote": "..."}]
    is_inference = Column(Boolean, default=False)
    status = Column(String, default="open")  # open | acknowledged
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="risk_items")
    citations = relationship("Citation", back_populates="risk_item", cascade="all, delete-orphan")


class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    label = Column(String, nullable=False)
    date = Column(String, nullable=True)  # ISO date string; nullable if unresolved
    confidence = Column(String, default="medium")
    basis = Column(Text, nullable=True)
    reminder_at = Column(DateTime, nullable=True)
    status = Column(String, default="unconfirmed")  # unconfirmed | confirmed | dismissed
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="deadlines")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True)  # human-readable id, e.g. source-nalsa-001
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    publisher = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    language = Column(String, default="en")
    verification_status = Column(String, default="unverified")
    verified_at = Column(DateTime, nullable=True)

    chunks = relationship("SourceChunk", back_populates="source", cascade="all, delete-orphan")


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    content = Column(Text, nullable=False)
    topic = Column(String, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    source = relationship("Source", back_populates="chunks")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    risk_item_id = Column(UUID(as_uuid=False), ForeignKey("risk_items.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    quote = Column(Text, nullable=True)
    page = Column(Integer, nullable=True)

    risk_item = relationship("RiskItem", back_populates="citations")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    position = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    official_url = Column(String, nullable=True)
    completed = Column(Boolean, default=False)

    case = relationship("Case", back_populates="action_items")


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    draft_type = Column(String, nullable=False)  # response_letter | complaint_summary | evidence_summary
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="drafts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    event_type = Column(String, nullable=False)
    detail = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="audit_events")
