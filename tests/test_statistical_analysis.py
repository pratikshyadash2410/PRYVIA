"""
Regression tests for PRYVIA statistical analysis.

These tests verify that the frozen experiment scenarios produce
the expected statistical-analysis outputs.
"""

from pathlib import Path

import pandas as pd

from src.statistical_analysis import run_statistical_analysis


# -------------------------------------------------------------------
# Project paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


# -------------------------------------------------------------------
# Load frozen PRYVIA data
# -------------------------------------------------------------------

assignments = pd.read_csv(
    SRC_DIR / "experiment_assignments_prototype.csv"
)

search_success = pd.read_csv(
    SRC_DIR / "search_success_prototype.csv"
)

sessions = pd.read_csv(
    SRC_DIR / "search_sessions_prototype.csv"
)

searches = pd.read_csv(
    SRC_DIR / "searches_prototype.csv"
)

results = pd.read_csv(
    SRC_DIR / "search_results_final.csv"
)


# -------------------------------------------------------------------
# Expected experiment scenarios
# -------------------------------------------------------------------

EXPECTED_EXPERIMENTS = [1, 2, 3, 4]


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_statistical_analysis_runs_for_all_experiments():
    """Verify statistical analysis runs successfully for all four experiments."""

    for experiment_id in EXPECTED_EXPERIMENTS:

        analysis = run_statistical_analysis(
            assignments=assignments,
            search_success=search_success,
            sessions=sessions,
            searches=searches,
            results=results,
            experiment_id=experiment_id,
        )

        assert analysis["experiment_id"] == experiment_id

        assert "srm" in analysis
        assert "power" in analysis
        assert "ssr" in analysis
        assert "error" in analysis
        assert "latency" in analysis
        assert "reformulation" in analysis
        assert "ctr" in analysis


def test_srm_passes_for_all_frozen_experiments():
    """Verify the frozen experiments pass the 50/50 SRM check."""

    for experiment_id in EXPECTED_EXPERIMENTS:

        analysis = run_statistical_analysis(
            assignments=assignments,
            search_success=search_success,
            sessions=sessions,
            searches=searches,
            results=results,
            experiment_id=experiment_id,
        )

        assert analysis["srm"]["passed"] is True


def test_experiment_2_is_underpowered():
    """Experiment 2 intentionally has insufficient sample size."""

    analysis = run_statistical_analysis(
        assignments=assignments,
        search_success=search_success,
        sessions=sessions,
        searches=searches,
        results=results,
        experiment_id=2,
    )

    assert analysis["power"]["adequate"] is False
    assert analysis["power"]["actual_users"] == 1000


def test_experiment_1_has_positive_ssr_lift():
    """Experiment 1 should show a positive SSR treatment lift."""

    analysis = run_statistical_analysis(
        assignments=assignments,
        search_success=search_success,
        sessions=sessions,
        searches=searches,
        results=results,
        experiment_id=1,
    )

    assert analysis["ssr"]["lift_pp"] > 0
    assert analysis["ssr"]["significant"] is True


def test_experiment_4_has_latency_guardrail_breach():
    """Experiment 4 intentionally violates the latency guardrail."""

    analysis = run_statistical_analysis(
        assignments=assignments,
        search_success=search_success,
        sessions=sessions,
        searches=searches,
        results=results,
        experiment_id=4,
    )

    assert analysis["latency"]["healthy"] is False