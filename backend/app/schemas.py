from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Evidence Schemas
class EvidenceBase(BaseModel):
    record_id: str
    source_type: str  # email, access_log, employee_record, transaction, internal_message, meeting_note, policy
    title: str
    timestamp: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    custom: bool = False
    file_name: Optional[str] = None
    added_at: Optional[datetime] = None

class EvidenceCreate(EvidenceBase):
    case_id: Optional[str] = None

class EvidenceResponse(EvidenceBase):
    case_id: Optional[str] = None
    class Config:
        from_attributes = True

# Timeline Event
class TimelineEvent(BaseModel):
    timestamp: str
    event: str
    source_records: List[str]
    category: str = "general"
    verified: bool = True

# Hypothesis
class Hypothesis(BaseModel):
    id: str
    title: str
    description: str
    status: str = "active"  # active, supported, challenged, refuted
    confidence_rationale: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)

# Workflow Event (actual streamed step)
class WorkflowEventSchema(BaseModel):
    id: Optional[int] = None
    case_id: str
    timestamp: datetime
    node: str
    event_type: str  # planner, retriever, analyst, critic, reporter, human_review
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

# Human Review
class HumanReviewCreate(BaseModel):
    decision: str  # approved, changes_requested
    reviewer_name: str = "Lead Investigator"
    feedback: str

class HumanReviewResponse(HumanReviewCreate):
    id: int
    case_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Investigation Report
class StructuredReport(BaseModel):
    incident_summary: str
    timeline: List[TimelineEvent] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    competing_hypotheses: List[Hypothesis] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    uncertainty_declaration: Optional[str] = None
    human_review_status: str = "awaiting_review"

class ReportResponse(BaseModel):
    id: int
    case_id: str
    title: str
    summary: str
    report_json: Dict[str, Any]
    markdown_content: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Case Schemas
class CaseCreate(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    category: Optional[str] = "Corporate Incident"
    mode: Optional[str] = "agentic"  # agentic or basic
    priority: str = "Medium"
    objective: Optional[str] = None
    additional_context: Optional[str] = None

class CaseSummary(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: str
    mode: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseDetail(CaseSummary):
    priority: str = "Medium"
    objective: Optional[str] = None
    additional_context: Optional[str] = None
    has_report: bool = False
    workflow_step_count: int = 0
    retrieved_evidence_count: int = 0
    last_review: Optional[HumanReviewResponse] = None

# Investigation State Schema (for state sync and inspection)
class InvestigationStateSchema(BaseModel):
    case_id: str
    title: str
    incident_description: str
    current_node: str
    questions_to_investigate: List[str] = Field(default_factory=list)
    planned_queries: List[str] = Field(default_factory=list)
    queries_attempted: List[str] = Field(default_factory=list)
    retrieved_evidence: List[EvidenceBase] = Field(default_factory=list)
    event_timeline: List[TimelineEvent] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    critic_decision: Optional[str] = None
    critic_feedback: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    final_report: Optional[Dict[str, Any]] = None
    human_review_status: str = "pending"
    human_feedback: Optional[str] = None

# Settings Response
class SettingsResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    project_name: str
    version: str
    llm_provider: str
    model_name: str
    api_key_configured: bool
    demo_mode_active: bool
    database_url: str
    chroma_persist_dir: str
    max_critic_retries: int

class SettingsUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
