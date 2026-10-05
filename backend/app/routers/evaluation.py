from fastapi import APIRouter
from backend.app.evaluation.benchmark import run_full_benchmark

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmark"])

_cached_benchmark = None

@router.get("/benchmark")
def get_benchmark_results(force_rerun: bool = False):
    """
    Returns empirical evaluation results comparing Basic RAG vs Agentic RAG
    across all synthetic benchmark cases with ground truth verification.
    """
    global _cached_benchmark
    if _cached_benchmark is None or force_rerun:
        _cached_benchmark = run_full_benchmark()
    return _cached_benchmark

@router.post("/run")
def trigger_benchmark_run():
    """Forces execution of the evaluation suite."""
    global _cached_benchmark
    _cached_benchmark = run_full_benchmark()
    return _cached_benchmark
