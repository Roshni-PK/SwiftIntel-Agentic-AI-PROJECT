import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import CaseModel, InvestigationStateModel, ReportModel, WorkflowEventModel, HumanReviewModel
from backend.app.schemas import CaseCreate, CaseSummary, CaseDetail, HumanReviewResponse
from backend.app.data.generator import CASES_GROUND_TRUTH

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("/templates")
def get_synthetic_templates():
    """Returns pre-configured synthetic corporate cases for quick investigation startup."""
    return CASES_GROUND_TRUTH

@router.get("", response_model=List[CaseDetail])
def list_cases(db: Session = Depends(get_db)):
    """List all cases with summary statistics."""
    cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).all()
    results = []
    
    for c in cases:
        ev_count = len(c.evidences) if c.evidences else 0
        state = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == c.id).first()
        if state and state.full_state_json:
            try:
                state_dict = json.loads(state.full_state_json)
                ev_count = max(ev_count, len(state_dict.get("retrieved_evidence", [])))
            except Exception:
                pass
                
        events_count = db.query(WorkflowEventModel).filter(WorkflowEventModel.case_id == c.id).count()
        has_report = db.query(ReportModel).filter(ReportModel.case_id == c.id).first() is not None
        
        last_review_model = db.query(HumanReviewModel).filter(HumanReviewModel.case_id == c.id).order_by(HumanReviewModel.id.desc()).first()
        last_review = None
        if last_review_model:
            last_review = HumanReviewResponse.from_orm(last_review_model)
            
        results.append(CaseDetail(
            id=c.id,
            title=c.title,
            description=c.description,
            category=c.category,
            priority=c.priority or "Medium",
            objective=c.objective,
            additional_context=c.additional_context,
            status=c.status,
            mode=c.mode,
            created_at=c.created_at,
            updated_at=c.updated_at,
            has_report=has_report,
            workflow_step_count=events_count,
            retrieved_evidence_count=ev_count,
            last_review=last_review
        ))
    return results

@router.post("", response_model=CaseDetail)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    """Create a new investigation case."""
    if case_in.priority not in {"Low", "Medium", "High"}:
        raise HTTPException(status_code=422, detail="Priority must be Low, Medium, or High.")
    case_id = case_in.id
    if not case_id:
        case_id = f"INC-{datetime.utcnow().strftime('%Y')}-{datetime.utcnow().strftime('%m%d%H%M')}"
        
    existing = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Case with ID {case_id} already exists.")
        
    case = CaseModel(
        id=case_id,
        title=case_in.title,
        description=case_in.description,
        category=case_in.category or "Corporate Incident",
        priority=case_in.priority,
        objective=case_in.objective,
        additional_context=case_in.additional_context,
        status="pending",
        mode=case_in.mode or "agentic",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return CaseDetail(
        id=case.id,
        title=case.title,
        description=case.description,
        category=case.category,
        priority=case.priority or "Medium",
        objective=case.objective,
        additional_context=case.additional_context,
        status=case.status,
        mode=case.mode,
        created_at=case.created_at,
        updated_at=case.updated_at,
        has_report=False,
        workflow_step_count=0,
        retrieved_evidence_count=0,
        last_review=None
    )

@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    events_count = db.query(WorkflowEventModel).filter(WorkflowEventModel.case_id == case.id).count()
    has_report = db.query(ReportModel).filter(ReportModel.case_id == case.id).first() is not None
    last_review_model = db.query(HumanReviewModel).filter(HumanReviewModel.case_id == case.id).order_by(HumanReviewModel.id.desc()).first()
    
    ev_count = len(case.evidences) if case.evidences else 0
    state = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == case.id).first()
    if state and state.full_state_json:
        try:
            state_dict = json.loads(state.full_state_json)
            ev_count = max(ev_count, len(state_dict.get("retrieved_evidence", [])))
        except Exception:
            pass
            
    return CaseDetail(
        id=case.id,
        title=case.title,
        description=case.description,
        category=case.category,
        priority=case.priority or "Medium",
        objective=case.objective,
        additional_context=case.additional_context,
        status=case.status,
        mode=case.mode,
        created_at=case.created_at,
        updated_at=case.updated_at,
        has_report=has_report,
        workflow_step_count=events_count,
        retrieved_evidence_count=ev_count,
        last_review=HumanReviewResponse.from_orm(last_review_model) if last_review_model else None
    )

@router.post("/{case_id}/reopen")
def reopen_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = "reopened"
    case.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "reopened", "case_id": case_id}

@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    db.delete(case)
    db.commit()
    return {"status": "deleted", "case_id": case_id}
