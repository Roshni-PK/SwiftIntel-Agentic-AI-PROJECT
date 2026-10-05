import json
from typing import Dict, Any, List
from datetime import datetime
from backend.app.agent.state import InvestigationState
from backend.app.agent.prompts import REPORTER_PROMPT
from backend.app.agent.engine import llm_engine
from backend.app.database import SessionLocal
from backend.app.models import ReportModel, CaseModel
from backend.app.agent.events import log_workflow_event


def _clean_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    cleaned: List[str] = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        item = " ".join(item.split()).strip(" -•")
        key = item.casefold()
        if item and key not in seen:
            cleaned.append(item)
            seen.add(key)
    return cleaned


def _refresh_seeded_finance_currency(value: Any, case_id: str) -> Any:
    if case_id != "INC-2024-1142":
        return value
    replacements = (
        ("$48,500.00", "₹41,22,500"), ("$48,500", "₹41,22,500"),
        ("$48.5k", "₹41,22,500"), ("$100,000", "₹85,00,000"),
        ("$10,000.00", "₹8,50,000"), ("$10,000", "₹8,50,000"),
        ("$342.10", "₹29,078.50"), ("$412.50", "₹35,062.50"),
        ("$5,000", "5,000 USDT"),
    )
    if isinstance(value, str):
        for old, new in replacements:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_refresh_seeded_finance_currency(item, case_id) for item in value]
    if isinstance(value, dict):
        return {key: _refresh_seeded_finance_currency(item, case_id) for key, item in value.items()}
    return value


def _markdown_report(report: Dict[str, Any], evidence: List[Dict[str, Any]]) -> str:
    def bullets(items: List[str], empty: str) -> str:
        return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"

    sections = [
        "# SwiftIntel Investigation Report",
        f"\n**Investigation:** {report['investigation']}  \n**Priority:** {report['priority']}  \n**Status:** {report['status']}",
        "\n## Executive Summary\n" + report["incident_summary"],
        "\n## What Happened\n" + report["what_happened"],
        "\n## Investigation Goal\n" + (report["investigation_goal"] or "No separate investigation goal was provided."),
        "\n## Key Evidence\n" + ("\n".join(f"- **{record.get('title') or 'Evidence record'}** [{record.get('record_id', 'source ID')}]: {record.get('content', '')}" for record in evidence) if evidence else "- No evidence records were retrieved for this investigation."),
        "\n## Key Findings\n" + bullets(report["key_findings"], "No specific findings could be established from the available records."),
        "\n## Possible Explanations\n" + ("\n".join(f"- **{hyp.get('title', 'Possible explanation')}** ({hyp.get('status', 'under review')}): {hyp.get('description', '')} Supporting records: {', '.join(hyp.get('supporting_evidence', [])) or 'none cited'}. Conflicting records: {', '.join(hyp.get('contradictory_evidence', [])) or 'none cited'}." for hyp in report["competing_hypotheses"]) if report["competing_hypotheses"] else "No possible explanations were recorded."),
        "\n## Evidence Strength\n" + report["evidence_strength"],
        "\n## Uncertainties and Evidence Gaps\n" + bullets(report["unresolved_questions"], report["uncertainty_declaration"] or "No additional questions were recorded; this does not by itself establish a conclusion."),
        "\n## Recommended Next Steps\n" + bullets(report["recommendations"], "Have an appropriate reviewer assess the available records and decide whether further action is needed."),
        "\n## Human Review\nAn appropriate human reviewer should assess these findings before any decision is made. This report does not independently establish wrongdoing."
    ]
    return "\n".join(sections)

def reporter_node(state: InvestigationState) -> Dict[str, Any]:
    case_id = state.get("case_id", "UNKNOWN-CASE")
    title = state.get("title", "")
    desc = state.get("incident_description", "")
    timeline = state.get("event_timeline", [])
    hypotheses = state.get("hypotheses", [])
    evidence = state.get("retrieved_evidence", [])
    critic_feedback = state.get("critic_feedback", "")
    human_feedback = state.get("human_feedback", "")
    db = SessionLocal()
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if case:
        # Prefer the current case intake over any stale title/description cached in
        # a previously saved investigation state.
        title = case.title
        desc = case.description
    if case_id == "INC-2024-1142":
        timeline = _refresh_seeded_finance_currency(timeline, case_id)
        hypotheses = _refresh_seeded_finance_currency(hypotheses, case_id)
        evidence = _refresh_seeded_finance_currency(evidence, case_id)
        critic_feedback = _refresh_seeded_finance_currency(critic_feedback, case_id)
        human_feedback = _refresh_seeded_finance_currency(human_feedback, case_id)
    priority = case.priority if case else "Medium"
    objective = case.objective if case else ""
    additional_context = case.additional_context if case else ""
    case_status = case.status if case else "awaiting_review"
    db.close()
    
    # Format texts for prompt
    timeline_str = "\n".join([f"- {t['timestamp']}: {t['event']} [Sources: {', '.join(t.get('source_records', []))}]" for t in timeline])
    hyp_str = "\n".join([f"- {h['title']} (Status: {h['status']}): {h['description']}" for h in hypotheses])
    
    evidence_brief = "\n".join([f"[{r['record_id']}] {r.get('title', 'Evidence record')} ({r.get('source_type', 'record')}, {r.get('timestamp') or 'date not provided'}): {r.get('content', '')[:500]}" for r in evidence[:15]])
    
    prompt = REPORTER_PROMPT.format(
        case_id=case_id,
        title=title,
        incident_description=desc,
        priority=priority,
        objective=objective or "Not specified",
        additional_context=additional_context or "None provided",
        timeline_text=timeline_str or "No timeline events established.",
        hypotheses_text=hyp_str or "No hypotheses recorded.",
        evidence_text=evidence_brief or "No evidence records available.",
        critic_feedback=critic_feedback or "No critic feedback.",
        human_feedback=human_feedback or "None"
    )
    
    response = llm_engine.generate_json(
        prompt=prompt,
        system_prompt="You are an executive corporate investigation report author who produces audit-ready documentation."
    )
    response = _refresh_seeded_finance_currency(response, case_id)
    
    summary = str(response.get("incident_summary") or ("No evidence records were retrieved, so no incident conclusion can be drawn." if not evidence else f"The investigation reviewed {len(evidence)} evidence record(s). The available information requires human review before any conclusion is made."))
    key_findings = _clean_list(response.get("key_findings"))
    if not key_findings:
        key_findings = ["No specific finding could be established from the available evidence."]
    uncertainty = str(response.get("uncertainty_declaration") or "The available records may be incomplete. The findings below should be checked by a human reviewer.")
    unresolved = _clean_list(response.get("unresolved_questions")) or _clean_list(state.get("evidence_gaps"))
    recommendations = _clean_list(response.get("recommendations")) or ["Review the cited source records and determine whether further evidence is needed."]
    evidence_strength = response.get("evidence_strength")
    allowed_strengths = {"Strongly supported", "Moderately supported", "Limited evidence", "Inconclusive"}
    if evidence_strength not in allowed_strengths:
        evidence_strength = "Inconclusive" if not evidence else "Limited evidence"
    what_happened = desc.strip() or "No incident description was provided."
    
    # Keep citations strictly within records actually retrieved for this investigation.
    retrieved_ids = {record.get("record_id") for record in evidence}
    report_hypotheses = []
    for hypothesis in hypotheses:
        cleaned_hypothesis = dict(hypothesis)
        cleaned_hypothesis["supporting_evidence"] = [rid for rid in hypothesis.get("supporting_evidence", []) if rid in retrieved_ids]
        cleaned_hypothesis["contradictory_evidence"] = [rid for rid in hypothesis.get("contradictory_evidence", []) if rid in retrieved_ids]
        report_hypotheses.append(cleaned_hypothesis)

    # Compile all cited supporting and contradictory evidence
    all_supporting = []
    all_contradictory = []
    for h in report_hypotheses:
        for s in h.get("supporting_evidence", []):
            if s not in all_supporting: all_supporting.append(s)
        for c in h.get("contradictory_evidence", []):
            if c not in all_contradictory: all_contradictory.append(c)
            
    final_report_dict = {
        "case_id": case_id,
        "title": f"SwiftIntel Investigation Report — {title}",
        "investigation": title,
        "priority": priority,
        "status": "Awaiting human review" if case_status != "completed" else "Completed",
        "investigation_goal": objective,
        "additional_context": additional_context,
        "what_happened": what_happened,
        "incident_summary": summary,
        "timeline": timeline,
        "key_findings": key_findings,
        "competing_hypotheses": report_hypotheses,
        "key_evidence": [{"record_id": r.get("record_id"), "title": r.get("title"), "source_type": r.get("source_type"), "timestamp": r.get("timestamp"), "content": r.get("content", "")} for r in evidence[:15]],
        "supporting_evidence": all_supporting,
        "contradictory_evidence": all_contradictory,
        "unresolved_questions": unresolved,
        "recommendations": recommendations,
        "evidence_strength": evidence_strength,
        "uncertainty_declaration": uncertainty,
        "human_review_status": "awaiting_review",
        "generated_at": datetime.utcnow().isoformat()
    }
    markdown_content = _markdown_report(final_report_dict, evidence[:15])
    
    # Persist report in database
    try:
        db = SessionLocal()
        existing_report = db.query(ReportModel).filter(ReportModel.case_id == case_id).first()
        if existing_report:
            existing_report.title = final_report_dict["title"]
            existing_report.summary = summary
            existing_report.report_json = json.dumps(final_report_dict)
            existing_report.markdown_content = markdown_content
            existing_report.status = "awaiting_review"
            existing_report.updated_at = datetime.utcnow()
        else:
            new_report = ReportModel(
                case_id=case_id,
                title=final_report_dict["title"],
                summary=summary,
                report_json=json.dumps(final_report_dict),
                markdown_content=markdown_content,
                status="awaiting_review"
            )
            db.add(new_report)
            
        case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if case:
            case.status = "awaiting_review"
            
        db.commit()
        db.close()
    except Exception as e:
        print(f"Warning: Failed to persist report in database: {e}")
        
    event = log_workflow_event(
        case_id=case_id,
        node="reporter",
        event_type="report_generated",
        message=f"Final Report Generator compiled structured report with {len(key_findings)} key findings and {len(timeline)} timeline citations. Report marked as 'awaiting_review'.",
        details={
            "report_title": final_report_dict["title"],
            "has_uncertainty": bool(uncertainty),
            "findings_count": len(key_findings),
            "recommendations_count": len(recommendations)
        }
    )
    
    events = list(state.get("workflow_events", []))
    events.append(event)
    
    return {
        "current_node": "reporter",
        "final_report": final_report_dict,
        "markdown_report": markdown_content,
        "human_review_status": "awaiting_review",
        "workflow_events": events
    }
