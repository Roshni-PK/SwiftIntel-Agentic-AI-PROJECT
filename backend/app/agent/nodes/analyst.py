from typing import Dict, Any, List
from backend.app.agent.state import InvestigationState
from backend.app.agent.prompts import ANALYST_PROMPT
from backend.app.agent.engine import llm_engine
from backend.app.retrieval.tools import build_event_timeline_tool
from backend.app.agent.events import log_workflow_event

def analyst_node(state: InvestigationState) -> Dict[str, Any]:
    case_id = state.get("case_id", "UNKNOWN-CASE")
    title = state.get("title", "")
    desc = state.get("incident_description", "")
    evidence_list = state.get("retrieved_evidence", [])
    
    # Format evidence for prompt
    evidence_text_parts = []
    record_ids = []
    for r in evidence_list:
        record_ids.append(r["record_id"])
        evidence_text_parts.append(
            f"Record ID: {r['record_id']}\n"
            f"Type: {r['source_type']}\n"
            f"Title: {r['title']}\n"
            f"Timestamp: {r.get('timestamp', 'N/A')}\n"
            f"Content: {r['content']}\n"
            f"---"
        )
    evidence_text = "\n".join(evidence_text_parts) if evidence_text_parts else "No evidence retrieved."
    
    prompt = ANALYST_PROMPT.format(
        title=title,
        incident_description=desc,
        evidence_text=evidence_text
    )
    
    response = llm_engine.generate_json(
        prompt=prompt,
        system_prompt="You are an objective forensic analyst specializing in corporate incident root cause analysis."
    )
    
    timeline = response.get("timeline", [])
    if not timeline and record_ids:
        # Fallback to automated timeline builder tool
        timeline = build_event_timeline_tool(record_ids)
        
    hypotheses = response.get("hypotheses", [
        {
            "id": "H1",
            "title": "Primary Working Hypothesis",
            "description": "Analysis of operational logs indicates an unauthorized breach of corporate security controls.",
            "status": "active",
            "confidence_rationale": "Initial correlation of timestamps and credentials.",
            "supporting_evidence": record_ids[:3],
            "contradictory_evidence": []
        }
    ])
    
    evidence_gaps = response.get("evidence_gaps", [
        "Need additional corroboration of peripheral access logs."
    ])
    
    # Organize supporting & contradictory evidence maps
    supporting_map: Dict[str, List[str]] = {}
    contradictory_map: Dict[str, List[str]] = {}
    for h in hypotheses:
        supporting_map[h["id"]] = h.get("supporting_evidence", [])
        contradictory_map[h["id"]] = h.get("contradictory_evidence", [])
        
    event = log_workflow_event(
        case_id=case_id,
        node="analyst",
        event_type="analysis_completed",
        message=f"Evidence Analyst synthesized {len(timeline)} timeline events, formulated {len(hypotheses)} competing hypotheses, and identified {len(evidence_gaps)} evidence gaps.",
        details={
            "timeline_event_count": len(timeline),
            "hypotheses": [h["title"] for h in hypotheses],
            "evidence_gaps": evidence_gaps
        }
    )
    
    events = list(state.get("workflow_events", []))
    events.append(event)
    
    return {
        "current_node": "analyst",
        "event_timeline": timeline,
        "hypotheses": hypotheses,
        "supporting_evidence": supporting_map,
        "contradictory_evidence": contradictory_map,
        "evidence_gaps": evidence_gaps,
        "workflow_events": events
    }
