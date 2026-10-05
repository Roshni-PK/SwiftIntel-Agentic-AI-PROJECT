from typing import List, Dict, Any, Optional, TypedDict

class InvestigationState(TypedDict, total=False):
    case_id: str
    title: str
    incident_description: str
    category: str
    current_node: str
    
    # 1. Investigation Planner State
    questions_to_investigate: List[str]
    planned_queries: List[str]
    queries_attempted: List[str]
    
    # 2. Evidence Retriever State
    retrieved_evidence: List[Dict[str, Any]]
    
    # 3. Evidence Analyst State
    event_timeline: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    supporting_evidence: Dict[str, List[str]]
    contradictory_evidence: Dict[str, List[str]]
    
    # 4. Critic / Reflection State
    evidence_gaps: List[str]
    critic_decision: str  # "SUFFICIENT" | "RETRIEVE_MORE" | "NEEDS_HUMAN_REVIEW"
    critic_feedback: str
    retry_count: int
    max_retries: int
    
    # 5. Final Report Generator State
    final_report: Optional[Dict[str, Any]]
    markdown_report: Optional[str]
    
    # 6. Human Review State
    human_review_status: str  # "pending" | "awaiting_review" | "approved" | "changes_requested"
    human_feedback: Optional[str]
    
    # Workflow Execution Audit Log
    workflow_events: List[Dict[str, Any]]
