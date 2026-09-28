"""
Regression tests for the PRYVIA decision engine.

The tests verify that the four frozen experiment scenarios
produce their intended deterministic verdicts.
"""

from pathlib import Path

import pandas as pd

from src.statistical_analysis import run_statistical_analysis
from src.decision_engine import evaluate_experiment


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
# Expected decisions for frozen scenarios
# -------------------------------------------------------------------

EXPECTED_DECISIONS = {
    1: {
        "verdict": "SHIP",
        "rule_triggered": 7,
    },
    2: {
        "verdict": "RUN FOLLOW-UP",
        "rule_triggered": 2,
    },
    3: {
        "verdict": "SHIP",
        "rule_triggered": 7,
    },
    4: {
        "verdict": "SHIP WITH CAUTION",
        "rule_triggered": 6,
    },
}


# -------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------

def get_decision(experiment_id):
    """Run statistical analysis and the decision engine for one experiment."""

    analysis = run_statistical_analysis(
        assignments=assignments,
        search_success=search_success,
        sessions=sessions,
        searches=searches,
        results=results,
        experiment_id=experiment_id,
    )

    return evaluate_experiment(analysis)


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_experiment_1_ships():
    """Experiment 1 should trigger the clean-win rule."""

    decision = get_decision(1)

    assert decision["verdict"] == "SHIP"
    assert decision["rule_triggered"] == 7


def test_experiment_2_runs_follow_up():
    """Experiment 2 should trigger the underpowered rule."""

    decision = get_decision(2)

    assert decision["verdict"] == "RUN FOLLOW-UP"
    assert decision["rule_triggered"] == 2


def test_experiment_3_ships():
    """Experiment 3 should trigger the clean-win rule."""

    decision = get_decision(3)

    assert decision["verdict"] == "SHIP"
    assert decision["rule_triggered"] == 7


def test_experiment_4_ships_with_caution():
    """Experiment 4 should trigger the guardrail-breach rule."""

    decision = get_decision(4)

    assert decision["verdict"] == "SHIP WITH CAUTION"
    assert decision["rule_triggered"] == 6


def test_all_frozen_experiment_decisions():
    """Verify every frozen experiment against the expected decision table."""

    for experiment_id, expected in EXPECTED_DECISIONS.items():

        decision = get_decision(experiment_id)

        assert decision["verdict"] == expected["verdict"]
        assert decision["rule_triggered"] == expected["rule_triggered"]