from typing import Dict, Any, List
from backend.app.agent.state import InvestigationState
from backend.app.agent.prompts import CRITIC_PROMPT
from backend.app.agent.engine import llm_engine
from backend.app.config import settings
from backend.app.agent.events import log_workflow_event

def critic_node(state: InvestigationState) -> Dict[str, Any]:
    case_id = state.get("case_id", "UNKNOWN-CASE")
    title = state.get("title", "")
    desc = state.get("incident_description", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", settings.MAX_CRITIC_RETRIES)
    
    questions = state.get("questions_to_investigate", [])
    evidence = state.get("retrieved_evidence", [])
    timeline = state.get("event_timeline", [])
    hypotheses = state.get("hypotheses", [])
    gaps = state.get("evidence_gaps", [])
    
    hyp_summary = "\n".join([f"- {h['id']}: {h['title']} (Status: {h['status']})" for h in hypotheses])
    
    prompt = CRITIC_PROMPT.format(
        title=title,
        incident_description=desc,
        retry_count=retry_count,
        max_retries=max_retries,
        evidence_count=len(evidence),
        questions="\n".join([f"- {q}" for q in questions]),
        timeline_count=len(timeline),
        hypotheses_summary=hyp_summary or "None",
        evidence_gaps="\n".join([f"- {g}" for g in gaps]) or "None"
    )
    
    response = llm_engine.generate_json(
        prompt=prompt,
        system_prompt="You are an exacting investigation critic who rejects unsubstantiated claims and demands rigor."
    )
    
    raw_decision = response.get("decision", "SUFFICIENT").upper().strip()
    reasoning = response.get("reasoning", "Evidence sufficiently corroborated.")
    suggested_queries = response.get("suggested_queries", [])
    
    # Bounded Loop Enforcement: If we have reached or exceeded max retries, force termination
    if raw_decision == "RETRIEVE_MORE" and retry_count >= max_retries:
        final_decision = "SUFFICIENT"
        reasoning += f" (Loop limit reached: {retry_count}/{max_retries} retries completed. Halting further automated retrieval to generate preliminary report)."
    else:
        final_decision = raw_decision
        
    new_retry_count = retry_count + 1 if final_decision == "RETRIEVE_MORE" else retry_count
    
    event = log_workflow_event(
        case_id=case_id,
        node="critic",
        event_type="critic_reflection",
        message=f"Investigation Critic rendered decision '{final_decision}' (Retry: {retry_count}/{max_retries}). {reasoning}",
        details={
            "decision": final_decision,
            "reasoning": reasoning,
            "suggested_queries": suggested_queries,
            "retry_count": new_retry_count,
            "max_retries": max_retries
        }
    )
    
    events = list(state.get("workflow_events", []))
    events.append(event)
    
    updated_state: Dict[str, Any] = {
        "current_node": "critic",
        "critic_decision": final_decision,
        "critic_feedback": reasoning,
        "retry_count": new_retry_count,
        "workflow_events": events
    }
    
    if final_decision == "RETRIEVE_MORE" and suggested_queries:
        updated_state["planned_queries"] = suggested_queries
        
    return updated_state
