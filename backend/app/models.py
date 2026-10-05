from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

class CaseModel(Base):
    __tablename__ = "cases"
    
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="Corporate Incident")
    priority = Column(String(20), nullable=False, default="Medium")
    objective = Column(Text, nullable=True)
    additional_context = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, investigating, awaiting_review, completed, reopened
    mode = Column(String(50), default="agentic")  # agentic or basic
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    state = relationship("InvestigationStateModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    events = relationship("WorkflowEventModel", back_populates="case", cascade="all, delete-orphan", order_by="WorkflowEventModel.id")
    report = relationship("ReportModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("HumanReviewModel", back_populates="case", cascade="all, delete-orphan", order_by="HumanReviewModel.id.desc()")
    evidences = relationship("EvidenceModel", back_populates="case", cascade="all, delete-orphan")

class EvidenceModel(Base):
    __tablename__ = "evidences"
    
    record_id = Column(String(100), primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=True)
    source_type = Column(String(50), index=True)  # email, access_log, employee_record, transaction, internal_message, meeting_note, policy
    title = Column(String(255), nullable=False)
    timestamp = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    file_name = Column(String(255), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="evidences")

class InvestigationStateModel(Base):
    __tablename__ = "investigation_states"
    
    case_id = Column(String(50), ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True)
    current_node = Column(String(50), default="not_started")
    full_state_json = Column(Text, default="{}")
    retry_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="state")

class WorkflowEventModel(Base):
    __tablename__ = "workflow_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    node = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)  # start, query, retrieval, analysis, critic_reflection, route, report, review
    message = Column(Text, nullable=False)
    details_json = Column(Text, default="{}")
    
    case = relationship("CaseModel", back_populates="events")

class ReportModel(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id", ondelete="CASCADE"), unique=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    report_json = Column(Text, default="{}")
    markdown_content = Column(Text, nullable=False)
    status = Column(String(50), default="draft")  # draft, awaiting_review, approved, revised
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="report")

class HumanReviewModel(Base):
    __tablename__ = "human_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    decision = Column(String(50), nullable=False)  # approved, changes_requested
    reviewer_name = Column(String(100), default="Lead Investigator")
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("CaseModel", back_populates="reviews")

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(160), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class UserSessionModel(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("UserModel")
