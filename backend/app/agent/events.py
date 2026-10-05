import json
from datetime import datetime
from typing import Dict, Any, Optional
from backend.app.database import SessionLocal
from backend.app.models import WorkflowEventModel, InvestigationStateModel, CaseModel

def log_workflow_event(
    case_id: str,
    node: str,
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Records an actual workflow execution event in SQLite and returns event dict."""
    details = details or {}
    now = datetime.utcnow()
    event_dict = {
        "case_id": case_id,
        "timestamp": now.isoformat(),
        "node": node,
        "event_type": event_type,
        "message": message,
        "details": details
    }
    
    try:
        db = SessionLocal()
        event_record = WorkflowEventModel(
            case_id=case_id,
            timestamp=now,
            node=node,
            event_type=event_type,
            message=message,
            details_json=json.dumps(details)
        )
        db.add(event_record)
        
        # Also update case status if relevant
        case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if case:
            if event_type == "start":
                case.status = "investigating"
            elif node == "reporter" and event_type == "report_generated":
                case.status = "awaiting_review"
            elif node == "critic" and details.get("decision") == "NEEDS_HUMAN_REVIEW":
                case.status = "awaiting_review"
            case.updated_at = now
            
        db.commit()
        db.close()
    except Exception as e:
        # Avoid crashing workflow if logging database error occurs
        print(f"Warning: Failed to persist workflow event to DB: {e}")
        
    return event_dict
