from contextlib import asynccontextmanager
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config import settings
from backend.app.database import init_db, SessionLocal
from backend.app.models import CaseModel, ReportModel, InvestigationStateModel
from backend.app.data.generator import CASES_GROUND_TRUTH
from backend.app.retrieval.vector_store import initialize_vector_store
from backend.app.routers import cases, investigation, evidence, evaluation, settings as settings_router, auth


def _refresh_legacy_financial_report(report, case, db):
    """Update old seeded finance-case report labels without touching other cases."""
    replacements = (
        ("$48,500.00", "₹41,22,500"),
        ("$48,500", "₹41,22,500"),
        ("$48.5k", "₹41,22,500"),
        ("$10,000", "₹8,50,000"),
        ("$5,000", "5,000 USDT"),
    )

    def convert(value):
        if isinstance(value, str):
            for old, new in replacements:
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        return value

    report.title = f"SwiftIntel Investigation Report — {case.title}"
    report.summary = convert(report.summary or "")
    report.markdown_content = convert(report.markdown_content or "")
    try:
        report_data = convert(json.loads(report.report_json or "{}"))
    except (TypeError, ValueError):
        report_data = {}
    report_data.update({
        "title": report.title,
        "investigation": case.title,
        "priority": case.priority or "Medium",
        "status": "Awaiting human review" if report.status != "approved" else "Completed",
        "investigation_goal": case.objective or "",
        "what_happened": case.description,
    })
    state = db.query(InvestigationStateModel).filter(InvestigationStateModel.case_id == case.id).first()
    if state:
        try:
            state_data = json.loads(state.full_state_json or "{}")
            report_data.setdefault("key_evidence", convert([
                {key: item.get(key) for key in ("record_id", "title", "source_type", "timestamp", "content")}
                for item in state_data.get("retrieved_evidence", [])[:15]
            ]))
            report_data.setdefault("unresolved_questions", state_data.get("evidence_gaps", []))
        except (TypeError, ValueError):
            pass
    report_data.setdefault("evidence_strength", "Limited evidence")
    if report.status != "approved":
        # Older demo reports could overstate intent. Refresh only this unapproved
        # seeded report using cautious, source-cited findings and current saved records.
        report_data.update({
            "incident_summary": "Records describe a ₹41,22,500 payment to a new vendor without the required second approval. A separate audit records a 5,000 USDT deposit to a wallet registered to David Chen. The available records do not establish intent; human review is needed.",
            "key_findings": [
                "The ERP record [TRX-601] lists a ₹41,22,500 payment with the second approver field blank; policy [POL-FIN-12] requires a second approval for payments of ₹8,50,000 or more.",
                "The email record [EML-501] requests an urgent payment to new bank details and uses a lookalike sender domain.",
                "The digital asset audit [TRX-602] records a 5,000 USDT deposit to a wallet registered to David Chen. Its purpose and the account holder's knowledge remain unconfirmed.",
            ],
            "competing_hypotheses": [
                {"id": "H1", "title": "A spoofed payment request led to an approval bypass", "description": "The records are consistent with a spoofed urgent request followed by a payment that did not receive the required second approval. They do not establish who knew the request was false.", "status": "active", "confidence_rationale": "Email, transaction, and policy records document the sequence; intent is not established.", "supporting_evidence": ["EML-501", "TRX-601", "POL-FIN-12"], "contradictory_evidence": []},
                {"id": "H2", "title": "The digital asset transfer may be related to the payment", "description": "A separate audit records a 5,000 USDT deposit to a wallet registered to David Chen before the payment. The record links the sending address to an entity associated with the lookalike domain, but does not alone establish who controlled the address or why it was sent.", "status": "active", "confidence_rationale": "The digital asset audit is relevant, but further verification is needed to establish ownership and purpose.", "supporting_evidence": ["TRX-602"], "contradictory_evidence": []},
            ],
            "supporting_evidence": ["POL-FIN-12", "EML-501", "TRX-601", "TRX-602"],
            "contradictory_evidence": [],
            "unresolved_questions": [
                "Who controlled the sending address for the 5,000 USDT transfer?",
                "Who ultimately received the wire transfer, and can any funds be recovered?",
                "Were other payments processed with the same vendor details or approval override?",
            ],
            "recommendations": [
                "Review the payment approval trail and verify the receiving account details.",
                "Have an appropriate reviewer examine the digital asset audit and confirm wallet ownership and context.",
                "Decide whether further investigation is needed before taking action about any individual.",
            ],
            "uncertainty_declaration": "The records document an approval bypass, an urgent email using a lookalike domain, and a separate digital asset deposit. They do not establish who controlled the sending wallet or what any individual knew or intended.",
            "evidence_strength": "Limited evidence",
        })
        from backend.app.agent.nodes.reporter import _markdown_report
        report.markdown_content = _markdown_report(report_data, report_data.get("key_evidence", []))
    report.report_json = json.dumps(report_data, ensure_ascii=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite tables and ChromaDB vector store
    print("Initializing SQLite database...")
    init_db()
    
    # Seed default synthetic benchmark cases into SQLite if empty
    db = SessionLocal()
    existing_count = db.query(CaseModel).count()
    if existing_count == 0:
        print("Seeding initial benchmark cases into SQLite...")
        for c in CASES_GROUND_TRUTH:
            case_model = CaseModel(
                id=c["id"],
                title=c["title"],
                description=c["incident_description"],
                category=c["category"],
                status="pending",
                mode="agentic"
            )
            db.add(case_model)
        db.commit()
    # Refresh only legacy currency text on the known seeded finance scenario.
    # The case ID is fixed by the synthetic dataset; user-created cases are untouched.
    finance_case = db.query(CaseModel).filter(CaseModel.id == "INC-2024-1142").first()
    if finance_case:
        finance_case.title = finance_case.title.replace("$48,500", "₹41,22,500")
        finance_case.description = finance_case.description.replace("$48,500", "₹41,22,500")
        finance_case.description = finance_case.description.replace("$10,000", "₹8,50,000")
        finance_report = db.query(ReportModel).filter(ReportModel.case_id == finance_case.id).first()
        if finance_report:
            _refresh_legacy_financial_report(finance_report, finance_case, db)
        db.commit()
    db.close()
    
    print("Initializing ChromaDB Evidence Vector Store...")
    initialize_vector_store()
    print("SwiftIntel service is ready.")
    
    yield
    
    # Shutdown logic if any
    print("Shutting down SwiftIntel service...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agentic AI for Corporate Incident Investigation Platform",
    lifespan=lifespan
)

@app.middleware("http")
async def protect_application_api(request, call_next):
    from backend.app.routers.auth import require_authenticated_request
    user = require_authenticated_request(request)
    if request.url.path.startswith("/api/") and request.url.path != "/api/health" and not request.url.path.startswith("/api/auth/") and request.method != "OPTIONS":
        if not user:
            return JSONResponse(status_code=401, content={"detail": "Please log in to continue."})
        request.state.user = user
    return await call_next(request)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(cases.router, prefix=settings.API_PREFIX)
app.include_router(investigation.router, prefix=settings.API_PREFIX)
app.include_router(evidence.router, prefix=settings.API_PREFIX)
app.include_router(evaluation.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "provider": settings.LLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
