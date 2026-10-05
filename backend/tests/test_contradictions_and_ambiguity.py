import pytest
from backend.app.agent.graph import execute_investigation

def test_case_1_contradiction_handling():
    # In Case 1, Git commit tag says Alice Vance, but badge exit and dinner receipt prove Alice was 18 miles offsite.
    state = execute_investigation(
        case_id="INC-2024-0891",
        title="Project Aegis Core Algorithm Exfiltration",
        incident_description="On October 14, 2024, at 23:42 UTC, unauthorized data transfer of Project Aegis codebase to 198.51.100.44 was flagged. Initial git commits tagged Alice Vance."
    )
    
    hypotheses = state.get("hypotheses", [])
    # Should identify competing hypotheses
    titles = [h["title"].lower() for h in hypotheses]
    assert any("mallory" in t or "contractor" in t for t in titles)
    
    # Alice Vance hypothesis should be marked refuted or challenged due to contradictory alibi
    alice_hyp = next((h for h in hypotheses if "alice" in h["title"].lower()), None)
    if alice_hyp:
        assert alice_hyp["status"] in ["refuted", "challenged"]
        assert len(alice_hyp["contradictory_evidence"]) > 0

def test_case_2_contradiction_and_kickback():
    # In Case 2, David Chen claims to be an innocent victim of executive email spoofing,
    # but evidence contains MTG-701 (showing vendor already paid) and TRX-602 ($5000 kickback).
    state = execute_investigation(
        case_id="INC-2024-1142",
        title="Unauthorized $48,500 Wire Transfer",
        incident_description="Accounts Payable disbursed $48,500 wire transfer for invoice #INV-9921 bypassing POL-FIN-12 dual approval."
    )
    
    report = state.get("final_report", {})
    findings_text = " ".join(report.get("key_findings", [])).lower()
    assert "pol-fin-12" in findings_text or "dual" in findings_text
    assert "trx-602" in findings_text or "kickback" in findings_text or "deposit" in findings_text

def test_case_3_honest_uncertainty_handling():
    # In Case 3, audit logs are wiped for 31 minutes. The system must NOT declare a person guilty.
    state = execute_investigation(
        case_id="INC-2024-1405",
        title="Critical Production Outage and Audit Log Truncation",
        incident_description="On December 12, 2024, US-East Kubernetes cluster went down for 31 minutes while S3 audit logs were wiped. Marcus Brody was on VPN."
    )
    
    report = state.get("final_report", {})
    # Must declare uncertainty
    assert report.get("uncertainty_declaration") is not None
    assert "uncertain" in report["uncertainty_declaration"].lower() or "gap" in report["uncertainty_declaration"].lower() or "cannot" in report["uncertainty_declaration"].lower()
    
    # Must NOT conclude Marcus Brody is guilty without evidence
    hypotheses = state.get("hypotheses", [])
    brody_hyp = next((h for h in hypotheses if "brody" in h["title"].lower() or "marcus" in h["title"].lower()), None)
    if brody_hyp:
        assert brody_hyp["status"] != "supported"
