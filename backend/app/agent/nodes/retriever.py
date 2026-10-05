from typing import Dict, Any, List
from backend.app.agent.state import InvestigationState
from backend.app.retrieval.tools import (
    search_evidence_tool,
    filter_access_logs_tool,
    lookup_company_policy_tool,
    examine_transaction_records_tool
)
from backend.app.agent.events import log_workflow_event

def retriever_node(state: InvestigationState) -> Dict[str, Any]:
    case_id = state.get("case_id", "UNKNOWN-CASE")
    planned_queries = state.get("planned_queries", [])
    queries_attempted = list(state.get("queries_attempted", []))
    existing_evidence = list(state.get("retrieved_evidence", []))
    existing_ids = {r["record_id"] for r in existing_evidence}
    
    newly_retrieved = []
    
    for query in planned_queries:
        if query not in queries_attempted:
            queries_attempted.append(query)
            
        # 1. Main vector search
        results = search_evidence_tool(query=query, n_results=4, case_id=case_id)
        for r in results:
            if r["record_id"] not in existing_ids:
                existing_ids.add(r["record_id"])
                newly_retrieved.append(r)
                
        # 2. Heuristic tool augmentations
        q_lower = query.lower()
        if "policy" in q_lower or "pol-" in q_lower:
            policies = lookup_company_policy_tool(query)
            for p in policies:
                if p["record_id"] not in existing_ids:
                    existing_ids.add(p["record_id"])
                    newly_retrieved.append(p)
                    
        if "log" in q_lower or "badge" in q_lower or "ip" in q_lower or "terminal" in q_lower:
            # Check for specific workstation or ip mention
            user_kw = None
            if "alice" in q_lower: user_kw = "alice"
            elif "mallory" in q_lower: user_kw = "mallory"
            elif "bob" in q_lower: user_kw = "bob"
            elif "marcus" in q_lower: user_kw = "marcus"
            elif "david" in q_lower: user_kw = "david"
            if user_kw:
                logs = filter_access_logs_tool(user_or_ip=user_kw)
                for l in logs:
                    if l["record_id"] not in existing_ids:
                        existing_ids.add(l["record_id"])
                        newly_retrieved.append(l)
                    
        if "wire" in q_lower or "transaction" in q_lower or "invoice" in q_lower or "payment" in q_lower:
            txs = examine_transaction_records_tool(entity_or_keyword="apex" if "apex" in q_lower else None)
            for tx in txs:
                if tx["record_id"] not in existing_ids:
                    existing_ids.add(tx["record_id"])
                    newly_retrieved.append(tx)
                    
    combined_evidence = existing_evidence + newly_retrieved
    
    event = log_workflow_event(
        case_id=case_id,
        node="retriever",
        event_type="evidence_retrieved",
        message=f"Evidence Retriever retrieved {len(newly_retrieved)} new records across {len(planned_queries)} queries (Total evidence: {len(combined_evidence)}).",
        details={
            "executed_queries": planned_queries,
            "new_record_ids": [r["record_id"] for r in newly_retrieved],
            "total_records_count": len(combined_evidence)
        }
    )
    
    events = list(state.get("workflow_events", []))
    events.append(event)
    
    return {
        "current_node": "retriever",
        "retrieved_evidence": combined_evidence,
        "queries_attempted": queries_attempted,
        "planned_queries": [],  # Clear planned queries once executed
        "workflow_events": events
    }
