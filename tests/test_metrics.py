"""
Unit tests for Quantitative Evaluation Suite.
"""

import os
from src.evaluation.benchmark import HandoverBenchmark


def test_benchmark_execution():
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "synthetic_clients.json"
    )
    benchmark = HandoverBenchmark(data_path)
    results = benchmark.run_benchmark()

    assert "summary_metrics" in results
    b_metrics = results["summary_metrics"]["baseline"]
    p_metrics = results["summary_metrics"]["prototype"]

    # Prototype repetition avoidance score must be higher than baseline
    assert p_metrics["repetition_avoidance"] > b_metrics["repetition_avoidance"]

    # Prototype guardrail compliance must be significantly higher
    assert p_metrics["guardrail_compliance"] > b_metrics["guardrail_compliance"]

    # Error analysis entries present
    assert len(results["error_analysis"]) > 0
