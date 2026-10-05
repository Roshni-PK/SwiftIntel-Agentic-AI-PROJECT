from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.retrieval.vector_store import (
    search_evidence as vs_search,
    get_record_by_id,
    get_all_records
)

def search_evidence_tool(query: str, n_results: int = 5, source_type: Optional[str] = None, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search corporate evidence database across emails, access logs, transactions, 
    messages, employee profiles, and policies using vector semantic retrieval.
    """
    return vs_search(query=query, n_results=n_results, source_type=source_type, case_id=case_id)

def filter_access_logs_tool(
    user_or_ip: Optional[str] = None,
    location_or_host: Optional[str] = None,
    time_window_start: Optional[str] = None,
    time_window_end: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter and inspect access logs (physical turnstiles, OS logins, Git pushes, firewalls)
    by user handle, IP address, hostname, or location.
    """
    all_recs = get_all_records()
    access_logs = [r for r in all_recs if r["source_type"] == "access_log"]
    matched = []
    
    for log in access_logs:
        content_lower = log["content"].lower()
        meta = log.get("metadata", {})
        
        matches_user = True
        if user_or_ip:
            target = user_or_ip.lower()
            matches_user = (
                target in content_lower or
                target in meta.get("user", "").lower() or
                target in meta.get("ip", "").lower() or
                target in meta.get("client_ip", "").lower() or
                target in meta.get("dest_ip", "").lower()
            )
            
        matches_loc = True
        if location_or_host:
            loc = location_or_host.lower()
            matches_loc = (
                loc in content_lower or
                loc in meta.get("hostname", "").lower() or
                loc in meta.get("location", "").lower() or
                loc in meta.get("repo", "").lower()
            )
            
        if matches_user and matches_loc:
            matched.append(log)
            
    return matched

def lookup_company_policy_tool(policy_code_or_topic: str) -> List[Dict[str, Any]]:
    """
    Look up authoritative corporate governance and compliance policies
    by policy identifier (e.g. POL-SEC-04, POL-FIN-12, POL-OPS-03) or regulatory topic.
    """
    all_recs = get_all_records()
    policy_records = [r for r in all_recs if r["source_type"] == "policy"]
    matched = []
    
    query_str = policy_code_or_topic.upper()
    for p in policy_records:
        if (query_str in p["record_id"].upper() or 
            query_str.lower() in p["title"].lower() or 
            query_str.lower() in p["content"].lower()):
            matched.append(p)
            
    if not matched:
        # Fallback to vector search specifically filtered by policy
        matched = vs_search(query=policy_code_or_topic, n_results=3, source_type="policy")
        
    return matched

def examine_transaction_records_tool(
    min_amount: Optional[float] = None,
    entity_or_keyword: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Inspect corporate accounts payable, wire transfers, and expense records
    matching disbursement thresholds or beneficiary entities.
    """
    all_recs = get_all_records()
    tx_records = [r for r in all_recs if r["source_type"] == "transaction"]
    matched = []
    
    for tx in tx_records:
        meta = tx.get("metadata", {})
        tx_amount = float(meta.get("amount", 0.0) or meta.get("illicit_deposit", 0.0))
        
        matches_amount = True
        if min_amount is not None:
            matches_amount = (tx_amount >= min_amount)
            
        matches_entity = True
        if entity_or_keyword:
            kw = entity_or_keyword.lower()
            content_lower = tx["content"].lower()
            meta_str = str(meta).lower()
            matches_entity = (kw in content_lower or kw in meta_str)
            
        if matches_amount and matches_entity:
            matched.append(tx)
            
    return matched

def build_event_timeline_tool(record_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Orders retrieved records chronologically to construct an event timeline.
    """
    events = []
    for rid in record_ids:
        rec = get_record_by_id(rid)
        if rec and rec.get("timestamp"):
            events.append({
                "timestamp": rec["timestamp"],
                "event": f"[{rec['source_type'].upper()}] {rec['title']}",
                "source_records": [rec["record_id"]],
                "category": rec["source_type"],
                "details": rec["content"][:200] + ("..." if len(rec["content"]) > 200 else "")
            })
            
    # Sort chronologically by timestamp
    events.sort(key=lambda x: x["timestamp"])
    return events
