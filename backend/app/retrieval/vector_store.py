import os
import json
import math
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from backend.app.config import settings
from backend.app.data.generator import SYNTHETIC_RECORDS, save_synthetic_data_files

import zlib

class FastLocalEmbeddingFunction(EmbeddingFunction):
    """
    High-performance, zero-external-dependency embedding function for ChromaDB.
    Uses character and word n-gram term frequency with deterministic trigonometric projection
    to generate normalized 128-dimensional dense vectors.
    Uses zlib.crc32 to ensure 100% cross-process determinism without external API keys or PyTorch.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            tokens = text.lower().split()
            vec = [0.0] * self.dim
            if not tokens:
                embeddings.append(vec)
                continue
            for i, token in enumerate(tokens):
                # Deterministic token hash via crc32
                token_hash = zlib.crc32(token.encode('utf-8'))
                idx = token_hash % self.dim
                sign = 1.0 if (token_hash % 2 == 0) else -1.0
                vec[idx] += sign * (1.0 / math.sqrt(i + 1.0))
                # Add bigram context
                if i > 0:
                    bigram_str = f"{tokens[i-1]}_{token}".encode('utf-8')
                    bigram_hash = zlib.crc32(bigram_str)
                    b_idx = bigram_hash % self.dim
                    vec[b_idx] += 0.5 * (1.0 if (bigram_hash % 2 == 0) else -1.0)
            
            # L2 normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings

_chroma_client = None
_collection = None
_embedding_fn = FastLocalEmbeddingFunction(dim=128)

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client

def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="detectiveai_corporate_evidence",
            embedding_function=_embedding_fn,
            metadata={"description": "Corporate incident evidence repository"}
        )
    return _collection

def initialize_vector_store(force_reload: bool = False):
    """Refreshes seeded records in place without disturbing user-added evidence."""
    save_synthetic_data_files()
    col = get_collection()
    count = col.count()
    
    ids = []
    documents = []
    metadatas = []
    
    for r in SYNTHETIC_RECORDS:
        ids.append(r["record_id"])
        # Rich document representation combining title, type, and content
        doc_str = f"[{r['source_type'].upper()}] {r['title']}\nTimestamp: {r.get('timestamp', 'N/A')}\n\n{r['content']}"
        documents.append(doc_str)
        meta = {
            "record_id": r["record_id"],
            "case_id": r.get("case_id") or "general",
            "source_type": r["source_type"],
            "title": r["title"],
            "timestamp": r.get("timestamp") or "",
            "raw_metadata": json.dumps(r.get("metadata", {}))
        }
        metadatas.append(meta)
        
    # Upsert known synthetic IDs so older seeded content receives current text and
    # metadata. Unrelated custom records in this shared collection are untouched.
    col.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return col.count()

def add_custom_evidence(record: Dict[str, Any]) -> None:
    """Add one persisted user-provided record to the shared evidence collection."""
    col = get_collection()
    metadata = {
        "record_id": record["record_id"], "case_id": record["case_id"],
        "source_type": record["source_type"], "title": record["title"],
        "timestamp": record.get("timestamp") or "", "custom": True,
        "file_name": record.get("file_name") or "",
        "raw_metadata": json.dumps(record.get("metadata", {}), ensure_ascii=False)
    }
    document = f"[{record['source_type'].upper()}] {record['title']}\nSource: User Added\nFile: {record.get('file_name') or 'N/A'}\n\n{record['content']}"
    col.add(ids=[record["record_id"]], documents=[document], metadatas=[metadata])

def delete_custom_evidence(record_id: str) -> None:
    """Delete only a matching custom record; never touch seeded records."""
    col = get_collection()
    found = col.get(ids=[record_id], include=["metadatas"])
    if found["ids"] and found["metadatas"][0].get("custom") is True:
        col.delete(ids=[record_id])

def search_evidence(query: str, n_results: int = 5, source_type: Optional[str] = None, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves relevant corporate evidence matching query, with optional source_type filter."""
    col = get_collection()
    if col.count() == 0:
        initialize_vector_store()
        
    where_filter = {}
    if source_type:
        where_filter["source_type"] = source_type
        
    query_kwargs: Dict[str, Any] = {
        "query_texts": [query],
        # Query broadly, then case-scope custom evidence without excluding legacy
        # synthetic records whose Chroma metadata predates the custom flag.
        "n_results": max(1, col.count())
    }
    if where_filter:
        query_kwargs["where"] = where_filter
        
    res = col.query(**query_kwargs)
    
    output = []
    if res and res["ids"] and len(res["ids"][0]) > 0:
        for i in range(len(res["ids"][0])):
            record_id = res["ids"][0][i]
            meta = res["metadatas"][0][i]
            if case_id and meta.get("custom") is True and meta.get("case_id") != case_id:
                continue
            doc = res["documents"][0][i]
            distance = res["distances"][0][i] if "distances" in res and res["distances"] else 0.0
            
            raw_meta = {}
            if "raw_metadata" in meta and meta["raw_metadata"]:
                try:
                    raw_meta = json.loads(meta["raw_metadata"])
                except Exception:
                    raw_meta = {}
                    
            output.append({
                "record_id": record_id,
                "case_id": meta.get("case_id"),
                "source_type": meta.get("source_type"),
                "title": meta.get("title"),
                "timestamp": meta.get("timestamp"),
                "content": doc,
                "metadata": raw_meta,
                "custom": meta.get("custom", False),
                "file_name": meta.get("file_name") or None,
                "relevance_score": round(max(0.0, 1.0 - (distance / 2.0)), 4)
            })
    return output[:n_results]

def get_record_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    col = get_collection()
    if col.count() == 0:
        initialize_vector_store()
    res = col.get(ids=[record_id])
    if res and res["ids"]:
        meta = res["metadatas"][0]
        raw_meta = {}
        if "raw_metadata" in meta and meta["raw_metadata"]:
            try:
                raw_meta = json.loads(meta["raw_metadata"])
            except Exception:
                pass
        return {
            "record_id": res["ids"][0],
            "case_id": meta.get("case_id"),
            "source_type": meta.get("source_type"),
            "title": meta.get("title"),
            "timestamp": meta.get("timestamp"),
            "content": res["documents"][0],
            "metadata": raw_meta,
            "custom": meta.get("custom", False),
            "file_name": meta.get("file_name") or None
        }
    return None

def get_all_records() -> List[Dict[str, Any]]:
    col = get_collection()
    if col.count() == 0:
        initialize_vector_store()
    res = col.get()
    records = []
    for i in range(len(res["ids"])):
        meta = res["metadatas"][i]
        raw_meta = {}
        if "raw_metadata" in meta and meta["raw_metadata"]:
            try:
                raw_meta = json.loads(meta["raw_metadata"])
            except Exception:
                pass
        records.append({
            "record_id": res["ids"][i],
            "case_id": meta.get("case_id"),
            "source_type": meta.get("source_type"),
            "title": meta.get("title"),
            "timestamp": meta.get("timestamp"),
            "content": res["documents"][i],
            "metadata": raw_meta,
            "custom": meta.get("custom", False),
            "file_name": meta.get("file_name") or None
        })
    return records
