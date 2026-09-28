"""
PRYVIA - Experiment Scenario Validation
Validates Experiments 1-4 using the current statistical analysis
and decision engine.

Run from src/:
    python validate_experiment_scenarios.py
"""

from pathlib import Path
import sys

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from statistical_analysis import run_statistical_analysis
from decision_engine import evaluate_experiment


def load_data():
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

    return (
        assignments,
        search_success,
        sessions,
        searches,
        results,
    )


def pct(value):
    return f"{value:.2%}"


def print_experiment_result(experiment_id, analysis, decision):
    srm = analysis["srm"]
    power = analysis["power"]
    ssr = analysis["ssr"]
    error = analysis["error"]
    latency = analysis["latency"]
    reformulation = analysis["reformulation"]
    ctr = analysis["ctr"]

    print("\n" + "=" * 75)
    print(f"EXPERIMENT {experiment_id}")
    print("=" * 75)

    print(f"\nFINAL DECISION: {decision['verdict']}")
    print(
        f"Rule {decision['rule_triggered']}: "
        f"{decision['rule_label']}"
    )
    print(f"Reason: {decision['reason']}")

    print("\nEXPERIMENT HEALTH")
    print(
        f"SRM:              "
        f"{'PASS' if srm['passed'] else 'FAIL'} "
        f"(Control {srm['control_users']:,} | "
        f"Treatment {srm['treatment_users']:,})"
    )

    print(
        f"Power:             "
        f"{'ADEQUATE' if power['adequate'] else 'UNDERPOWERED'} "
        f"(Required total {power['required_total']:,} | "
        f"Actual {power['actual_users']:,} | "
        f"Achieved {pct(power['achieved_power'])})"
    )

    print(
        f"Guardrails:        "
        f"{'HEALTHY' if analysis['guardrails_healthy'] else 'BREACH'}"
    )

    print("\nPRIMARY METRIC — SSR")
    print(f"Control SSR:       {pct(ssr['control_rate'])}")
    print(f"Treatment SSR:     {pct(ssr['treatment_rate'])}")
    print(f"Lift:              {ssr['lift_pp']:+.2f} pp")
    print(f"Relative lift:     {ssr['relative_lift_pct']:+.2f}%")
    print(
        f"95% CI:            "
        f"[{ssr['ci_lower_pp']:+.2f}, "
        f"{ssr['ci_upper_pp']:+.2f}] pp"
    )
    print(f"p-value:           {ssr['p_value']:.6f}")
    print(f"Significant:       {ssr['significant']}")

    print("\nGUARDRAILS")
    print(
        f"Error rate:        "
        f"Control {pct(error['control_rate'])} | "
        f"Treatment {pct(error['treatment_rate'])} | "
        f"Δ {error['difference_pp']:+.2f} pp | "
        f"{'HEALTHY' if error['healthy'] else 'BREACH'}"
    )

    print(
        f"Latency median:    "
        f"Control {latency['control_median_ms']:.1f} ms | "
        f"Treatment {latency['treatment_median_ms']:.1f} ms | "
        f"Δ {latency['difference_ms']:+.1f} ms | "
        f"{'HEALTHY' if latency['healthy'] else 'BREACH'}"
    )

    print("\nSECONDARY DIAGNOSTICS")
    print(
        f"CTR:               "
        f"Control {pct(ctr['control_rate'])} | "
        f"Treatment {pct(ctr['treatment_rate'])} | "
        f"Δ {ctr['difference_pp']:+.2f} pp | "
        f"p={ctr['p_value']:.6f}"
    )

    print(
        f"Reformulation:     "
        f"Control {pct(reformulation['control_rate'])} | "
        f"Treatment {pct(reformulation['treatment_rate'])} | "
        f"Δ {reformulation['difference_pp']:+.2f} pp | "
        f"p={reformulation['p_value']:.6f}"
    )


def main():
    (
        assignments,
        search_success,
        sessions,
        searches,
        results,
    ) = load_data()

    print("\nPRYVIA — FOUR EXPERIMENT VALIDATION")
    print("-----------------------------------")
    print(f"Assignments: {len(assignments):,}")
    print(f"Users:       {assignments['user_id'].nunique():,}")
    print(f"Sessions:    {len(sessions):,}")
    print(f"Searches:    {len(searches):,}")
    print(f"Results:     {len(results):,}")

    decisions = {}

    for experiment_id in [1, 2, 3, 4]:
        analysis = run_statistical_analysis(
            experiment_id=experiment_id,
            assignments=assignments,
            search_success=search_success,
            sessions=sessions,
            searches=searches,
            results=results,
        )

        decision = evaluate_experiment(analysis)

        decisions[experiment_id] = decision["verdict"]

        print_experiment_result(
            experiment_id,
            analysis,
            decision,
        )

    print("\n" + "=" * 75)
    print("SCENARIO VALIDATION SUMMARY")
    print("=" * 75)

    for experiment_id, verdict in decisions.items():
        print(
            f"Experiment {experiment_id}: "
            f"{verdict}"
        )

    print("\nExpected scenario intent:")
    print("Experiment 1 → SHIP")
    print("Experiment 2 → RUN FOLLOW-UP")
    print("Experiment 3 → exploratory segment signal")
    print("Experiment 4 → SHIP WITH CAUTION")

    print(
        "\nNOTE: Experiment 3 is intentionally exploratory. "
        "Its segment signal is not used by the decision engine."
    )


if __name__ == "__main__":
    main()