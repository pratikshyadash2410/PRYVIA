"""
PRYVIA — Generate Experiment Verdicts

Runs the existing statistical analysis and decision engine for
all experiments and saves one row per experiment.

Output:
    src/experiment_verdicts.csv

This script does NOT contain statistical or decision logic.
It simply connects:
    CSV data
        ↓
    statistical_analysis.py
        ↓
    decision_engine.py
        ↓
    experiment_verdicts.csv
"""

from pathlib import Path
import sys

import pandas as pd


# ===============================================================
# PROJECT PATHS
# ===============================================================

SRC_DIR = Path(__file__).resolve().parent

# Allow imports from src/
sys.path.insert(0, str(SRC_DIR))


# ===============================================================
# EXISTING PRYVIA MODULES
# ===============================================================

from statistical_analysis import run_statistical_analysis
from decision_engine import evaluate_experiment


# ===============================================================
# INPUT FILES
# ===============================================================

ASSIGNMENTS_FILE = SRC_DIR / "experiment_assignments_prototype.csv"
SEARCH_SUCCESS_FILE = SRC_DIR / "search_success_prototype.csv"
SESSIONS_FILE = SRC_DIR / "search_sessions_prototype.csv"
SEARCHES_FILE = SRC_DIR / "searches_with_reformulation.csv"
RESULTS_FILE = SRC_DIR / "search_results_final.csv"


# ===============================================================
# OUTPUT FILE
# ===============================================================

OUTPUT_FILE = SRC_DIR / "experiment_verdicts.csv"


# ===============================================================
# LOAD DATA
# ===============================================================

def load_data():
    """
    Load all datasets required by statistical_analysis.py.
    """

    assignments = pd.read_csv(ASSIGNMENTS_FILE)

    search_success = pd.read_csv(
        SEARCH_SUCCESS_FILE
    )

    sessions = pd.read_csv(
        SESSIONS_FILE
    )

    searches = pd.read_csv(
        SEARCHES_FILE
    )

    results = pd.read_csv(
        RESULTS_FILE
    )

    return (
        assignments,
        search_success,
        sessions,
        searches,
        results,
    )


# ===============================================================
# GENERATE VERDICTS
# ===============================================================

def generate_verdicts():

    (
        assignments,
        search_success,
        sessions,
        searches,
        results,
    ) = load_data()

    verdict_rows = []

    # Find all experiments present in the assignment data.
    experiment_ids = sorted(
        assignments["experiment_id"].unique()
    )

    # -----------------------------------------------------------
    # Run analysis experiment-by-experiment
    # -----------------------------------------------------------

    for experiment_id in experiment_ids:

        print(
            f"Analyzing Experiment {experiment_id}..."
        )

        # -------------------------------------------------------
        # Statistical analysis
        # -------------------------------------------------------

        analysis = run_statistical_analysis(
            assignments=assignments,
            search_success=search_success,
            sessions=sessions,
            searches=searches,
            results=results,
            experiment_id=int(experiment_id),
        )

        # -------------------------------------------------------
        # Decision engine
        # -------------------------------------------------------

        decision = evaluate_experiment(
            analysis
        )

        # -------------------------------------------------------
        # Extract evidence for Power BI
        # -------------------------------------------------------

        srm = analysis["srm"]
        power = analysis["power"]
        ssr = analysis["ssr"]
        error = analysis["error"]
        latency = analysis["latency"]
        reformulation = analysis["reformulation"]
        ctr = analysis["ctr"]

        # -------------------------------------------------------
        # One row = one experiment
        # -------------------------------------------------------

        row = {

            # ===================================================
            # EXPERIMENT
            # ===================================================

            "experiment_id": int(
                experiment_id
            ),

            # ===================================================
            # FINAL DECISION
            # ===================================================

            "verdict": decision["verdict"],

            "rule_triggered": decision[
                "rule_triggered"
            ],

            "rule_label": decision[
                "rule_label"
            ],

            "severity": decision[
                "severity"
            ],

            # ===================================================
            # SAMPLE / SRM
            # ===================================================

            "control_users": srm[
                "control_users"
            ],

            "treatment_users": srm[
                "treatment_users"
            ],

            "total_users": srm[
                "total_users"
            ],

            "srm_p_value": srm[
                "p_value"
            ],

            "srm_passed": srm[
                "passed"
            ],

            # ===================================================
            # POWER / SAMPLE SIZE
            # ===================================================

            "baseline_ssr": power[
                "baseline_ssr"
            ],

            "target_ssr": power[
                "target_ssr"
            ],

            "mde_pp": power[
                "mde_pp"
            ],

            "required_per_group": power[
                "required_per_group"
            ],

            "required_total": power[
                "required_total"
            ],

            "actual_users": power[
                "actual_users"
            ],

            "achieved_power": power[
                "achieved_power"
            ],

            "power_adequate": power[
                "adequate"
            ],

            # ===================================================
            # PRIMARY METRIC — SSR
            # ===================================================

            "control_ssr": ssr[
                "control_rate"
            ],

            "treatment_ssr": ssr[
                "treatment_rate"
            ],

            "lift_pp": ssr[
                "lift_pp"
            ],

            "relative_lift_pct": ssr[
                "relative_lift_pct"
            ],

            "ssr_p_value": ssr[
                "p_value"
            ],

            "ssr_significant": ssr[
                "significant"
            ],

            "ssr_positive": ssr[
                "positive"
            ],

            # ===================================================
            # SSR CONFIDENCE INTERVAL
            # ===================================================

            "ci_lower_pp": ssr[
                "ci_lower_pp"
            ],

            "ci_upper_pp": ssr[
                "ci_upper_pp"
            ],

            # ===================================================
            # TECHNICAL GUARDRAIL — ERROR RATE
            # ===================================================

            "control_error_rate": error[
                "control_rate"
            ],

            "treatment_error_rate": error[
                "treatment_rate"
            ],

            "error_difference_pp": error[
                "difference_pp"
            ],

            "error_p_value": error[
                "p_value"
            ],

            "error_guardrail_healthy": error[
                "healthy"
            ],

            # ===================================================
            # TECHNICAL GUARDRAIL — LATENCY
            # ===================================================

            "control_median_latency_ms": latency[
                "control_median_ms"
            ],

            "treatment_median_latency_ms": latency[
                "treatment_median_ms"
            ],

            "latency_difference_ms": latency[
                "difference_ms"
            ],

            "latency_p_value": latency[
                "p_value"
            ],

            "latency_guardrail_healthy": latency[
                "healthy"
            ],

            # ===================================================
            # OVERALL GUARDRAILS
            # ===================================================

            "guardrails_healthy": analysis[
                "guardrails_healthy"
            ],

            # ===================================================
            # SECONDARY — CTR
            # ===================================================

            "control_ctr": ctr[
                "control_rate"
            ],

            "treatment_ctr": ctr[
                "treatment_rate"
            ],

            "ctr_difference_pp": ctr[
                "difference_pp"
            ],

            "ctr_p_value": ctr[
                "p_value"
            ],

            "ctr_significant": ctr[
                "significant"
            ],

            # ===================================================
            # SECONDARY — REFORMULATION
            # ===================================================

            "control_reformulation_rate": reformulation[
                "control_rate"
            ],

            "treatment_reformulation_rate": reformulation[
                "treatment_rate"
            ],

            "reformulation_difference_pp": reformulation[
                "difference_pp"
            ],

            "reformulation_p_value": reformulation[
                "p_value"
            ],

            "reformulation_significant": reformulation[
                "significant"
            ],
        }

        verdict_rows.append(row)

    # ===========================================================
    # CREATE FINAL DATAFRAME
    # ===========================================================

    verdicts_df = pd.DataFrame(
        verdict_rows
    )

    verdicts_df = verdicts_df.sort_values(
        "experiment_id"
    ).reset_index(
        drop=True
    )

    # ===========================================================
    # SAVE CSV
    # ===========================================================

    verdicts_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ===========================================================
    # PRINT SUMMARY
    # ===========================================================

    print()
    print("=" * 70)
    print("PRYVIA EXPERIMENT VERDICTS GENERATED")
    print("=" * 70)

    print(
        f"Experiments analyzed : {len(verdicts_df)}"
    )

    print(
        f"Output file          : {OUTPUT_FILE}"
    )

    print()

    print(
        verdicts_df[
            [
                "experiment_id",
                "verdict",
                "rule_triggered",
                "control_ssr",
                "treatment_ssr",
                "lift_pp",
                "ssr_p_value",
                "srm_passed",
                "guardrails_healthy",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("Done.")


# ===============================================================
# SCRIPT ENTRY POINT
# ===============================================================

if __name__ == "__main__":
    generate_verdicts()