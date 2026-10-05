from typing import List, Optional
from pathlib import Path
from uuid import uuid4
import csv, hashlib, io, json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import CaseModel, EvidenceModel
from backend.app.retrieval.vector_store import get_all_records, get_record_by_id, search_evidence, add_custom_evidence, delete_custom_evidence
from backend.app.schemas import EvidenceResponse

router = APIRouter(prefix="/evidence", tags=["Evidence Vault"])

@router.get("", response_model=List[EvidenceResponse])
def list_or_search_evidence(
    q: Optional[str] = Query(None, description="Search query string"),
    source_type: Optional[str] = Query(None, description="Filter by evidence source type"),
    case_id: Optional[str] = Query(None, description="Filter by case ID")
):
    """
    Search and filter corporate evidence repository with provenance metadata.
    """
    if q and q.strip():
        # Perform semantic vector retrieval
        records = search_evidence(query=q.strip(), n_results=15, source_type=source_type, case_id=case_id)
    else:
        records = get_all_records()
        if source_type:
            records = [r for r in records if r["source_type"] == source_type]
            
    if case_id:
        records = [r for r in records if r.get("case_id") == case_id or r.get("case_id") == "general" or r.get("case_id") is None]
    # Merge SQLite custom records for metadata consistency if an older Chroma DB is in use.
        
    output = []
    for r in records:
        output.append(EvidenceResponse(
            record_id=r["record_id"],
            case_id=r.get("case_id"),
            source_type=r["source_type"],
            title=r["title"],
            timestamp=r.get("timestamp"),
            content=r["content"],
            metadata=r.get("metadata", {}),
            custom=r.get("custom", r.get("source_type") == "custom"),
            file_name=r.get("file_name") or r.get("metadata", {}).get("original_file_name"),
            added_at=r.get("added_at")
        ))
    return output

@router.get("/cases/{case_id}")
def list_case_custom_evidence(case_id: str, db: Session = Depends(get_db)):
    if not db.query(CaseModel).filter(CaseModel.id == case_id).first():
        raise HTTPException(status_code=404, detail="Investigation not found")
    rows = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id, EvidenceModel.source_type == "custom").order_by(EvidenceModel.added_at.desc()).all()
    return [_model_record(row) for row in rows]

def _model_record(row):
    try: metadata = json.loads(row.metadata_json or "{}")
    except Exception: metadata = {}
    return {"record_id": row.record_id, "case_id": row.case_id, "source_type": "custom", "title": row.title,
            "timestamp": row.timestamp, "content": row.content, "metadata": metadata,
            "file_name": row.file_name, "added_at": row.added_at}

@router.post("/cases/{case_id}")
async def upload_case_evidence(case_id: str, name: str = Form(...), description: str = Form(""), file: UploadFile = File(...), db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case: raise HTTPException(status_code=404, detail="Investigation not found")
    safe_name = Path(file.filename or "").name
    ext = Path(safe_name).suffix.lower()
    supported = {".txt", ".csv", ".json", ".log", ".md"}
    if not safe_name or ext not in supported:
        raise HTTPException(status_code=400, detail="Choose a TXT, CSV, JSON, LOG, or Markdown file.")
    if not name.strip(): raise HTTPException(status_code=400, detail="Enter an evidence name.")
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024: raise HTTPException(status_code=413, detail="Files must be 5 MB or smaller.")
    if not raw.strip(): raise HTTPException(status_code=400, detail="This file is empty.")
    digest = hashlib.sha256(raw).hexdigest()
    prior = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id, EvidenceModel.source_type == "custom", EvidenceModel.metadata_json.contains(digest)).first()
    if prior: raise HTTPException(status_code=409, detail="This file has already been added to this investigation.")
    try:
        decoded = raw.decode("utf-8-sig")
        if ext == ".json":
            parsed = json.loads(decoded)
            content = json.dumps(parsed, ensure_ascii=False, indent=2)
        elif ext == ".csv":
            rows = list(csv.DictReader(io.StringIO(decoded)))
            if not rows: raise ValueError("CSV has no data rows")
            content = "\n".join("; ".join(f"{key}: {value}" for key, value in row.items() if key) for row in rows)
        else: content = decoded
        if not content.strip(): raise ValueError("No readable text")
    except Exception:
        raise HTTPException(status_code=400, detail="Couldn't read this file. Please check that it is a supported file and try again.")
    record_id = f"USR-{uuid4().hex}"
    added = datetime.utcnow()
    metadata = {"description": description.strip(), "original_file_name": safe_name, "sha256": digest, "added_at": added.isoformat(), "source": "user_added"}
    storage_dir = Path(settings.EVIDENCE_UPLOAD_DIR).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_path = storage_dir / f"{record_id}{ext}"
    try:
        stored_path.write_bytes(raw)
        row = EvidenceModel(record_id=record_id, case_id=case_id, source_type="custom", title=name.strip()[:255],
            timestamp=added.isoformat(), content=content, metadata_json=json.dumps(metadata), file_name=safe_name, added_at=added)
        db.add(row)
        add_custom_evidence({"record_id": record_id, "case_id": case_id, "source_type": "custom", "title": name.strip(), "timestamp": added.isoformat(), "content": content, "metadata": metadata, "file_name": safe_name})
        db.commit()
    except Exception:
        db.rollback()
        delete_custom_evidence(record_id)
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Evidence could not be saved. Please try again.")
    return _model_record(row)

@router.delete("/cases/{case_id}/{record_id}")
def remove_case_evidence(case_id: str, record_id: str, db: Session = Depends(get_db)):
    row = db.query(EvidenceModel).filter(EvidenceModel.record_id == record_id, EvidenceModel.case_id == case_id, EvidenceModel.source_type == "custom").first()
    if not row: raise HTTPException(status_code=404, detail="Custom evidence not found")
    try:
        path = (Path(settings.EVIDENCE_UPLOAD_DIR) / f"{record_id}{Path(row.file_name or '').suffix.lower()}").resolve()
        if path.parent == Path(settings.EVIDENCE_UPLOAD_DIR).resolve(): path.unlink(missing_ok=True)
    except OSError: pass
    delete_custom_evidence(record_id)
    db.delete(row); db.commit()
    return {"status": "deleted", "record_id": record_id}

@router.get("/source-types")
def get_source_types():
    """Returns available source types with count of records."""
    records = get_all_records()
    type_counts = {}
    for r in records:
        st = r["source_type"]
        type_counts[st] = type_counts.get(st, 0) + 1
    return type_counts

@router.get("/{record_id}", response_model=EvidenceResponse)
def get_evidence_detail(record_id: str):
    rec = get_record_by_id(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Evidence record not found")
    return EvidenceResponse(
        record_id=rec["record_id"],
        case_id=rec.get("case_id"),
        source_type=rec["source_type"],
        title=rec["title"],
        timestamp=rec.get("timestamp"),
        content=rec["content"],
        metadata=rec.get("metadata", {}),
        custom=rec.get("custom", rec.get("source_type") == "custom"),
        file_name=rec.get("file_name") or rec.get("metadata", {}).get("original_file_name"),
        added_at=rec.get("added_at")
    )
