import pytest
from backend.app.database import init_db, SessionLocal
from backend.app.agent.graph import execute_investigation, investigation_graph, route_after_critic
from backend.app.models import InvestigationStateModel, CaseModel, WorkflowEventModel, ReportModel

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()

def test_full_langgraph_workflow_execution():
    case_id = "TEST-CASE-001"
    title = "Test Incident: Unauthorized Repository Export"
    description = "On October 14, 2024, data transfer of Project Aegis codebase to 198.51.100.44 was flagged."
    
    final_state = execute_investigation(
        case_id=case_id,
        title=title,
        incident_description=description
    )
    
    # 1. Verify graph reached terminal node
    assert final_state["current_node"] == "reporter"
    
    # 2. Verify all logical nodes executed
    nodes_executed = {ev["node"] for ev in final_state.get("workflow_events", [])}
    assert "planner" in nodes_executed
    assert "retriever" in nodes_executed
    assert "analyst" in nodes_executed
    assert "critic" in nodes_executed
    assert "reporter" in nodes_executed
    
    # 3. Verify evidence was retrieved and preserved
    assert len(final_state["retrieved_evidence"]) > 0
    for rec in final_state["retrieved_evidence"]:
        assert "record_id" in rec
        assert "content" in rec
        
    # 4. Verify timeline and hypotheses generated
    assert len(final_state["event_timeline"]) > 0
    assert len(final_state["hypotheses"]) >= 2
    
    # 5. Verify report generated and awaiting human review
    assert final_state["final_report"] is not None
    assert final_state["final_report"]["human_review_status"] == "awaiting_review"
    assert len(final_state["final_report"]["key_findings"]) > 0

def test_bounded_critic_retries():
    # Test that route_after_critic terminates when retry_count exceeds max_retries
    state_under_limit = {
        "critic_decision": "RETRIEVE_MORE",
        "retry_count": 1,
        "max_retries": 2
    }
    assert route_after_critic(state_under_limit) == "retriever"
    
    state_at_limit = {
        "critic_decision": "RETRIEVE_MORE",
        "retry_count": 3,
        "max_retries": 2
    }
    assert route_after_critic(state_at_limit) == "reporter"

def test_sqlite_state_and_events_persistence():
    case_id = "TEST-PERSIST-002"
    execute_investigation(
        case_id=case_id,
        title="Persistence Verification Incident",
        incident_description="Testing SQLite state and event persistence for Case INC-2024-1142."
    )
    
    db = SessionLocal()
    # Check investigation_states record
    state_rec = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == case_id).first()
    assert state_rec is not None
    assert state_rec.current_node == "reporter"
    
    # Check workflow_events table
    events = db.query(WorkflowEventModel).filter(WorkflowEventModel.case_id == case_id).all()
    assert len(events) >= 5
    
    # Check report record
    report = db.query(ReportModel).filter(ReportModel.case_id == case_id).first()
    assert report is not None
    assert report.status == "awaiting_review"
    db.close()
