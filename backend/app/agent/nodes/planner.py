from typing import Dict, Any
from backend.app.agent.state import InvestigationState
from backend.app.agent.prompts import PLANNER_PROMPT
from backend.app.agent.engine import llm_engine
from backend.app.agent.events import log_workflow_event

def planner_node(state: InvestigationState) -> Dict[str, Any]:
    case_id = state.get("case_id", "UNKNOWN-CASE")
    title = state.get("title", "")
    desc = state.get("incident_description", "")
    feedback = state.get("human_feedback", "None")
    attempted = state.get("queries_attempted", [])
    
    prompt = PLANNER_PROMPT.format(
        case_id=case_id,
        title=title,
        incident_description=desc,
        human_feedback=feedback,
        queries_attempted=str(attempted)
    )
    
    response = llm_engine.generate_json(
        prompt=prompt,
        system_prompt="You are a meticulous corporate incident investigator."
    )
    
    questions = response.get("questions", [
        "What specific assets were affected during the incident window?",
        "Which credentials or access vectors were utilized?",
        "Are there verified alibis or conflicting records for the implicated parties?"
    ])
    
    queries = response.get("queries", [
        f"{title} access logs",
        f"{title} corporate security policy",
        f"{title} communications"
    ])
    
    # Filter out already attempted queries
    new_queries = [q for q in queries if q not in attempted]
    if not new_queries:
        new_queries = queries[:3]
        
    event = log_workflow_event(
        case_id=case_id,
        node="planner",
        event_type="plan_created",
        message=f"Investigation Planner formulated {len(questions)} investigative questions and scheduled {len(new_queries)} focused search queries.",
        details={
            "questions": questions,
            "queries": new_queries
        }
    )
    
    events = list(state.get("workflow_events", []))
    events.append(event)
    
    return {
        "current_node": "planner",
        "questions_to_investigate": questions,
        "planned_queries": new_queries,
        "workflow_events": events
    }
