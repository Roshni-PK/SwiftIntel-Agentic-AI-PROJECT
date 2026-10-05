import json
from typing import Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from backend.app.agent.state import InvestigationState
from backend.app.agent.nodes.planner import planner_node
from backend.app.agent.nodes.retriever import retriever_node
from backend.app.agent.nodes.analyst import analyst_node
from backend.app.agent.nodes.critic import critic_node
from backend.app.agent.nodes.reporter import reporter_node
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models import InvestigationStateModel, CaseModel
from backend.app.agent.events import log_workflow_event

def route_after_critic(state: InvestigationState) -> str:
    """
    Conditional routing edge following critic reflection.
    Returns the next node identifier: 'retriever' or 'reporter'.
    """
    decision = state.get("critic_decision", "SUFFICIENT")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", settings.MAX_CRITIC_RETRIES)
    
    if decision == "RETRIEVE_MORE" and retry_count <= max_retries:
        return "retriever"
    return "reporter"

def build_investigation_graph():
    """Builds and compiles the stateful LangGraph investigation workflow."""
    workflow = StateGraph(InvestigationState)
    
    # 1. Register logical nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("reporter", reporter_node)
    
    # 2. Set entry point
    workflow.set_entry_point("planner")
    
    # 3. Add deterministic edges
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "analyst")
    workflow.add_edge("analyst", "critic")
    
    # 4. Add conditional routing edge from critic
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "retriever": "retriever",
            "reporter": "reporter"
        }
    )
    
    # 5. Reporter to finish
    workflow.add_edge("reporter", END)
    
    return workflow.compile()

# Global compiled graph instance
investigation_graph = build_investigation_graph()

def execute_investigation(
    case_id: str,
    title: str,
    incident_description: str,
    category: str = "Corporate Incident",
    human_feedback: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the full LangGraph investigation for a case and persists state in SQLite.
    """
    # 1. Log start event
    log_workflow_event(
        case_id=case_id,
        node="workflow_engine",
        event_type="start",
        message=f"Investigation workflow initialized for case {case_id}: '{title}'.",
        details={"mode": "agentic", "provider": settings.LLM_PROVIDER}
    )
    
    # 2. Construct initial state
    initial_state: InvestigationState = {
        "case_id": case_id,
        "title": title,
        "incident_description": incident_description,
        "category": category,
        "current_node": "initialized",
        "questions_to_investigate": [],
        "planned_queries": [],
        "queries_attempted": [],
        "retrieved_evidence": [],
        "event_timeline": [],
        "hypotheses": [],
        "supporting_evidence": {},
        "contradictory_evidence": {},
        "evidence_gaps": [],
        "critic_decision": "PENDING",
        "critic_feedback": "",
        "retry_count": 0,
        "max_retries": settings.MAX_CRITIC_RETRIES,
        "final_report": None,
        "markdown_report": None,
        "human_review_status": "pending",
        "human_feedback": human_feedback,
        "workflow_events": []
    }
    
    # 3. Invoke LangGraph
    final_state = investigation_graph.invoke(initial_state)
    
    # 4. Persist updated investigation state in SQLite
    try:
        db = SessionLocal()
        state_record = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == case_id).first()
        if state_record:
            state_record.current_node = final_state.get("current_node", "completed")
            state_record.full_state_json = json.dumps(final_state)
            state_record.retry_count = final_state.get("retry_count", 0)
            state_record.updated_at = datetime.utcnow()
        else:
            state_record = InvestigationStateModel(
                case_id=case_id,
                current_node=final_state.get("current_node", "completed"),
                full_state_json=json.dumps(final_state),
                retry_count=final_state.get("retry_count", 0)
            )
            db.add(state_record)
            
        case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if case:
            case.status = "awaiting_review"
            case.updated_at = datetime.utcnow()
            
        db.commit()
        db.close()
    except Exception as e:
        print(f"Warning: Failed to persist investigation state: {e}")
        
    return final_state
