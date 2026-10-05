import pytest
from backend.app.data.generator import CASES_GROUND_TRUTH
from backend.app.evaluation.benchmark import evaluate_case

def test_compare_basic_vs_agentic_rag():
    case_1 = CASES_GROUND_TRUTH[0]
    result = evaluate_case(case_1)
    
    basic = result["basic_rag"]
    agent = result["agentic_rag"]
    
    # 1. Agentic RAG captures the governing policy
    assert agent["policy_captured"] is True
    
    # 2. Agentic RAG achieves 100% verified citations
    assert agent["citation_accuracy_pct"] == 100.0
    
    # 3. Agentic RAG detects the contradiction
    assert agent["contradiction_detected"] is True
    
    # 4. Agentic RAG scores significantly higher in ground truth alignment than Basic RAG
    assert agent["ground_truth_alignment_pct"] > basic["ground_truth_alignment_pct"]
