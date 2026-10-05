import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from backend.app.database import get_db, SessionLocal
from backend.app.models import CaseModel, InvestigationStateModel, WorkflowEventModel, ReportModel, HumanReviewModel
from backend.app.schemas import (
    WorkflowEventSchema,
    InvestigationStateSchema,
    HumanReviewCreate,
    HumanReviewResponse
)
from backend.app.agent.graph import execute_investigation

router = APIRouter(prefix="/cases/{case_id}", tags=["Investigation Workflow"])

def investigation_prompt(case: CaseModel) -> str:
    parts = [case.description]
    if case.objective:
        parts.append(f"Investigation objective: {case.objective}")
    if case.additional_context:
        parts.append(f"Additional investigator context: {case.additional_context}")
    return "\n\n".join(parts)

def run_investigation_in_background(case_id: str, title: str, description: str, category: str, feedback: Optional[str] = None):
    """Executes LangGraph in a background thread while logging events to SQLite."""
    try:
        execute_investigation(
            case_id=case_id,
            title=title,
            incident_description=description,
            category=category,
            human_feedback=feedback
        )
    except Exception as e:
        print(f"Error in background investigation: {e}")

@router.post("/investigate")
def start_investigation(
    case_id: str,
    background_tasks: BackgroundTasks,
    run_sync: bool = False,
    db: Session = Depends(get_db)
):
    """
    Start or re-run the stateful LangGraph investigation workflow for a case.
    Can be run in background (default) or synchronously.
    """
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = "investigating"
    case.updated_at = datetime.utcnow()
    db.commit()
    
    if run_sync:
        state = execute_investigation(
            case_id=case.id,
            title=case.title,
            incident_description=investigation_prompt(case),
            category=case.category
        )
        return {"status": "completed", "current_node": state.get("current_node")}
    else:
        background_tasks.add_task(
            run_investigation_in_background,
            case_id=case.id,
            title=case.title,
            description=investigation_prompt(case),
            category=case.category
        )
        return {"status": "investigation_started", "case_id": case_id}

@router.get("/workflow-events", response_model=List[WorkflowEventSchema])
def get_workflow_events(case_id: str, since_id: int = 0, db: Session = Depends(get_db)):
    """Fetch real-time workflow events for the case, with incremental polling support via since_id."""
    events = (
        db.query(WorkflowEventModel)
        .filter(WorkflowEventModel.case_id == case_id, WorkflowEventModel.id > since_id)
        .order_by(WorkflowEventModel.id.asc())
        .all()
    )
    
    output = []
    for ev in events:
        details_dict = {}
        if ev.details_json:
            try:
                details_dict = json.loads(ev.details_json)
            except Exception:
                details_dict = {}
        output.append(WorkflowEventSchema(
            id=ev.id,
            case_id=ev.case_id,
            timestamp=ev.timestamp,
            node=ev.node,
            event_type=ev.event_type,
            message=ev.message,
            details=details_dict
        ))
    return output

@router.get("/state")
def get_investigation_state(case_id: str, db: Session = Depends(get_db)):
    """Fetch full LangGraph state (hypotheses, timeline, gaps, evidence, critic decision)."""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    state_rec = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == case_id).first()
    if not state_rec or not state_rec.full_state_json:
        return {
            "case_id": case.id,
            "title": case.title,
            "incident_description": case.description,
            "current_node": "not_started",
            "questions_to_investigate": [],
            "planned_queries": [],
            "queries_attempted": [],
            "retrieved_evidence": [],
            "event_timeline": [],
            "hypotheses": [],
            "supporting_evidence": {},
            "contradictory_evidence": {},
            "evidence_gaps": [],
            "critic_decision": None,
            "retry_count": 0,
            "final_report": None,
            "human_review_status": "pending"
        }
        
    try:
        state_dict = json.loads(state_rec.full_state_json)
        return state_dict
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to deserialize investigation state")

@router.get("/report")
def get_case_report(case_id: str, export_format: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch structured investigation report. Supports export as markdown or plain text."""
    report = db.query(ReportModel).filter(ReportModel.case_id == case_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Investigation report not generated yet.")
        
    if export_format == "markdown":
        return Response(
            content=report.markdown_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={case_id}_report.md"}
        )
    elif export_format == "text":
        return Response(
            content=report.markdown_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={case_id}_report.txt"}
        )
        
    report_data = {}
    if report.report_json:
        try:
            report_data = json.loads(report.report_json)
        except Exception:
            report_data = {}
            
    return {
        "id": report.id,
        "case_id": report.case_id,
        "title": report.title,
        "summary": report.summary,
        "report_json": report_data,
        "markdown_content": report.markdown_content,
        "status": report.status,
        "created_at": report.created_at,
        "updated_at": report.updated_at
    }

@router.post("/review", response_model=HumanReviewResponse)
def submit_human_review(
    case_id: str,
    review_in: HumanReviewCreate,
    db: Session = Depends(get_db)
):
    """
    Submit human investigator review (e.g. approve report or request further investigation).
    Persists decision and updates case status.
    """
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    new_review = HumanReviewModel(
        case_id=case_id,
        decision=review_in.decision,
        reviewer_name=review_in.reviewer_name,
        feedback=review_in.feedback,
        created_at=datetime.utcnow()
    )
    db.add(new_review)
    
    # Update case and report status
    report = db.query(ReportModel).filter(ReportModel.case_id == case_id).first()
    if review_in.decision == "approved":
        case.status = "completed"
        if report:
            report.status = "approved"
    elif review_in.decision == "changes_requested":
        case.status = "reopened"
        if report:
            report.status = "revised"
            
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(new_review)
    
    # Log workflow event
    from backend.app.agent.events import log_workflow_event
    log_workflow_event(
        case_id=case_id,
        node="human_review",
        event_type="human_review_submitted",
        message=f"Human Review submitted by {review_in.reviewer_name}: Decision '{review_in.decision}'. Feedback: {review_in.feedback}",
        details={"decision": review_in.decision, "feedback": review_in.feedback}
    )
    
    return HumanReviewResponse.from_orm(new_review)

@router.post("/resume")
def resume_investigation(
    case_id: str,
    background_tasks: BackgroundTasks,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Resumes investigation with human reviewer guidance or supplementary questions."""
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = "investigating"
    case.updated_at = datetime.utcnow()
    db.commit()
    
    background_tasks.add_task(
        run_investigation_in_background,
        case_id=case.id,
        title=case.title,
        description=investigation_prompt(case),
        category=case.category,
        feedback=feedback
    )
    return {"status": "investigation_resumed", "case_id": case_id}
