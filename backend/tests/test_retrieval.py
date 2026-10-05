import pytest
from backend.app.retrieval.vector_store import initialize_vector_store, search_evidence, get_record_by_id, get_all_records
from backend.app.retrieval.tools import (
    filter_access_logs_tool,
    lookup_company_policy_tool,
    examine_transaction_records_tool,
    build_event_timeline_tool
)

@pytest.fixture(scope="module", autouse=True)
def setup_vector_store():
    initialize_vector_store()

def test_vector_store_initialization():
    records = get_all_records()
    assert len(records) >= 30

def test_search_evidence():
    results = search_evidence("Alice Vance Project Aegis source code exfiltration", n_results=5)
    assert len(results) > 0
    top_ids = [r["record_id"] for r in results]
    assert any(rid in top_ids for rid in ["LOG-202", "LOG-203", "ACC-101", "EMP-001"])

def test_get_record_by_id():
    rec = get_record_by_id("POL-SEC-04")
    assert rec is not None
    assert rec["source_type"] == "policy"
    assert "Section 4.2" in rec["content"]

def test_filter_access_logs_tool():
    logs = filter_access_logs_tool(user_or_ip="alice")
    assert len(logs) >= 1
    record_ids = [l["record_id"] for l in logs]
    assert "ACC-101" in record_ids

def test_lookup_company_policy_tool():
    policies = lookup_company_policy_tool("POL-FIN-12")
    assert len(policies) >= 1
    assert policies[0]["record_id"] == "POL-FIN-12"
    assert "₹8,50,000" in policies[0]["content"]

def test_examine_transaction_records_tool():
    txs = examine_transaction_records_tool(min_amount=40000.0)
    assert len(txs) >= 1
    amounts = [tx["metadata"].get("amount") for tx in txs]
    assert any(a >= 40000.0 for a in amounts)

def test_build_event_timeline_tool():
    sample_ids = ["ACC-101", "LOG-202", "LOG-203"]
    timeline = build_event_timeline_tool(sample_ids)
    assert len(timeline) == 3
    # Check chronological ordering
    for i in range(len(timeline) - 1):
        assert timeline[i]["timestamp"] <= timeline[i+1]["timestamp"]
