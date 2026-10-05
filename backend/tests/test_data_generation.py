import pytest
from backend.app.data.generator import CASES_GROUND_TRUTH, SYNTHETIC_RECORDS

def test_ground_truth_cases_count_and_structure():
    assert len(CASES_GROUND_TRUTH) >= 3
    case_ids = {c["id"] for c in CASES_GROUND_TRUTH}
    assert "INC-2024-0891" in case_ids
    assert "INC-2024-1142" in case_ids
    assert "INC-2024-1405" in case_ids
    
    for case in CASES_GROUND_TRUTH:
        assert "title" in case
        assert "incident_description" in case
        assert "ground_truth" in case
        gt = case["ground_truth"]
        assert "primary_responsible_party" in gt
        assert "verdict_type" in gt

def test_ground_truth_separated_from_records():
    # Ground truth summaries should not be present as searchable record titles or content
    gt_parties = {c["ground_truth"]["primary_responsible_party"] for c in CASES_GROUND_TRUTH}
    record_ids = {r["record_id"] for r in SYNTHETIC_RECORDS}
    
    for r in SYNTHETIC_RECORDS:
        # Records must not have ground_truth field
        assert "ground_truth" not in r
        assert r["record_id"] in record_ids

def test_synthetic_evidence_coverage():
    assert len(SYNTHETIC_RECORDS) >= 20
    source_types = {r["source_type"] for r in SYNTHETIC_RECORDS}
    required_types = {"email", "access_log", "employee_record", "transaction", "internal_message", "meeting_note", "policy"}
    for st in required_types:
        assert st in source_types, f"Missing required evidence type: {st}"

def test_insufficient_evidence_case_exists():
    ambiguous_cases = [c for c in CASES_GROUND_TRUTH if c["ground_truth"]["verdict_type"] == "insufficient_evidence"]
    assert len(ambiguous_cases) >= 1
    assert ambiguous_cases[0]["id"] == "INC-2024-1405"
