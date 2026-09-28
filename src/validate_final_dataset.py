import pandas as pd
from pathlib import Path


# ============================================================
# PRYVIA — FINAL DATASET INTEGRITY VALIDATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


def load_csv(filename):
    """Load a CSV file from the src directory."""
    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing required file: {path}"
        )

    return pd.read_csv(path)


def check_columns(df, required_columns, table_name):
    """Verify that all required columns exist."""
    missing = set(required_columns) - set(df.columns)

    if missing:
        raise AssertionError(
            f"{table_name}: missing columns -> {sorted(missing)}"
        )


def check_unique(df, column, table_name):
    """Verify that a column contains no duplicate values."""
    duplicate_count = df[column].duplicated().sum()

    if duplicate_count > 0:
        raise AssertionError(
            f"{table_name}: {duplicate_count:,} duplicate "
            f"values found in {column}"
        )


def check_foreign_keys(
    child_df,
    child_column,
    parent_df,
    parent_column,
    child_table,
    parent_table,
):
    """Verify that every child FK exists in the parent table."""

    child_ids = set(
        child_df[child_column].dropna()
    )

    parent_ids = set(
        parent_df[parent_column].dropna()
    )

    orphan_ids = child_ids - parent_ids

    if orphan_ids:
        raise AssertionError(
            f"{child_table}.{child_column}: "
            f"{len(orphan_ids):,} orphan IDs found "
            f"referencing {parent_table}.{parent_column}"
        )


def main():

    print("=" * 70)
    print("PRYVIA — FINAL DATASET INTEGRITY VALIDATION")
    print("=" * 70)

    # ========================================================
    # 1. LOAD ALL SOURCE-OF-TRUTH CSV FILES
    # ========================================================

    users = load_csv(
        "users_prototype.csv"
    )

    assignments = load_csv(
        "experiment_assignments_prototype.csv"
    )

    sessions = load_csv(
        "search_sessions_prototype.csv"
    )

    searches = load_csv(
        "searches_prototype.csv"
    )

    results = load_csv(
        "search_results_final.csv"
    )

    reformulations = load_csv(
        "searches_with_reformulation.csv"
    )

    success = load_csv(
        "search_success_prototype.csv"
    )

    events = load_csv(
        "business_events_prototype.csv"
    )

    print("\n[PASS] All CSV files loaded successfully")

    # ========================================================
    # 2. REQUIRED COLUMN VALIDATION
    # ========================================================

    check_columns(
        users,
        [
            "user_id",
            "user_type",
            "device_type",
            "activity_level",
        ],
        "users",
    )

    check_columns(
        assignments,
        [
            "experiment_id",
            "user_id",
            "variant",
        ],
        "experiment_assignments",
    )

    check_columns(
        sessions,
        [
            "session_id",
            "user_id",
        ],
        "search_sessions",
    )

    check_columns(
        searches,
        [
            "search_id",
            "session_id",
            "query_text",
            "query_category",
            "search_timestamp",
            "search_latency_ms",
            "search_error",
        ],
        "searches",
    )

    check_columns(
        results,
        [
            "result_id",
            "search_id",
            "rank_position",
            "result_type",
            "relevance_score",
            "clicked",
            "dwell_time_seconds",
            "returned_to_search",
        ],
        "search_results",
    )

    check_columns(
        reformulations,
        [
            "search_id",
            "session_id",
            "query_text",
            "query_category",
            "search_timestamp",
            "search_latency_ms",
            "search_error",
            "is_reformulation",
        ],
        "searches_with_reformulation",
    )

    check_columns(
        success,
        [
            "search_id",
            "session_id",
            "query_text",
            "query_category",
            "search_timestamp",
            "is_reformulation",
            "quality_click_count",
            "has_quality_click",
            "successful_search",
        ],
        "search_success",
    )

    check_columns(
        events,
        [
            "event_id",
            "search_id",
            "event_type",
            "event_timestamp",
        ],
        "business_events",
    )

    print("[PASS] Required columns present")

    # ========================================================
    # 3. PRIMARY KEY UNIQUENESS
    # ========================================================

    check_unique(
        users,
        "user_id",
        "users",
    )

    check_unique(
        sessions,
        "session_id",
        "search_sessions",
    )

    check_unique(
        searches,
        "search_id",
        "searches",
    )

    check_unique(
        results,
        "result_id",
        "search_results",
    )

    check_unique(
        events,
        "event_id",
        "business_events",
    )

    print("[PASS] Primary-key uniqueness")

    # ========================================================
    # 4. ASSIGNMENT UNIQUENESS
    # ========================================================
    # A user can participate in multiple experiments,
    # but can have only one variant within each experiment.

    duplicate_assignments = assignments[
        [
            "experiment_id",
            "user_id",
        ]
    ].duplicated().sum()

    if duplicate_assignments > 0:
        raise AssertionError(
            f"experiment_assignments: "
            f"{duplicate_assignments:,} duplicate "
            f"(experiment_id, user_id) pairs"
        )

    print(
        "[PASS] One assignment per experiment-user pair"
    )

    # ========================================================
    # 5. VALID EXPERIMENT IDs AND VARIANTS
    # ========================================================

    valid_experiment_ids = {
        1,
        2,
        3,
        4,
    }

    actual_experiment_ids = set(
        assignments["experiment_id"].unique()
    )

    invalid_experiment_ids = (
        actual_experiment_ids
        - valid_experiment_ids
    )

    if invalid_experiment_ids:
        raise AssertionError(
            f"Unexpected experiment IDs: "
            f"{invalid_experiment_ids}"
        )

    # Actual frozen dataset uses capitalized variant names.
    valid_variants = {
        "Control",
        "Treatment",
    }

    actual_variants = set(
        assignments["variant"].unique()
    )

    invalid_variants = (
        actual_variants
        - valid_variants
    )

    if invalid_variants:
        raise AssertionError(
            f"Unexpected variants: "
            f"{invalid_variants}"
        )

    print(
        "[PASS] Experiment IDs and variants valid"
    )

    # ========================================================
    # 6. FOREIGN KEY INTEGRITY
    # ========================================================

    check_foreign_keys(
        assignments,
        "user_id",
        users,
        "user_id",
        "experiment_assignments",
        "users",
    )

    check_foreign_keys(
        sessions,
        "user_id",
        users,
        "user_id",
        "search_sessions",
        "users",
    )

    check_foreign_keys(
        searches,
        "session_id",
        sessions,
        "session_id",
        "searches",
        "search_sessions",
    )

    check_foreign_keys(
        results,
        "search_id",
        searches,
        "search_id",
        "search_results",
        "searches",
    )

    check_foreign_keys(
        events,
        "search_id",
        searches,
        "search_id",
        "business_events",
        "searches",
    )

    print("[PASS] Foreign-key integrity")

    # ========================================================
    # 7. EXACTLY 5 RESULTS PER SEARCH
    # ========================================================

    results_per_search = (
        results
        .groupby("search_id")
        .size()
    )

    invalid_result_counts = (
        results_per_search[
            results_per_search != 5
        ]
    )

    if len(invalid_result_counts) > 0:
        raise AssertionError(
            f"{len(invalid_result_counts):,} searches "
            f"do not have exactly 5 results"
        )

    missing_result_searches = (
        set(searches["search_id"])
        - set(results["search_id"])
    )

    if missing_result_searches:
        raise AssertionError(
            f"{len(missing_result_searches):,} searches "
            f"have no results"
        )

    print(
        "[PASS] Exactly 5 ranked results per search"
    )

    # ========================================================
    # 8. RANK INTEGRITY
    # ========================================================

    valid_ranks = {
        1,
        2,
        3,
        4,
        5,
    }

    actual_ranks = set(
        results["rank_position"].unique()
    )

    invalid_ranks = (
        actual_ranks
        - valid_ranks
    )

    if invalid_ranks:
        raise AssertionError(
            f"Invalid result ranks: "
            f"{invalid_ranks}"
        )

    rank_counts = (
        results
        .groupby("search_id")["rank_position"]
        .nunique()
    )

    invalid_rank_counts = (
        rank_counts[
            rank_counts != 5
        ]
    )

    if len(invalid_rank_counts) > 0:
        raise AssertionError(
            "Some searches do not contain "
            "all 5 unique ranks"
        )

    print("[PASS] Rank integrity")

    # ========================================================
    # 9. REFORMULATION COVERAGE
    # ========================================================

    if len(reformulations) != len(searches):
        raise AssertionError(
            "Reformulation row count does not "
            "match search row count"
        )

    search_ids = set(
        searches["search_id"]
    )

    reformulation_search_ids = set(
        reformulations["search_id"]
    )

    if reformulation_search_ids != search_ids:
        raise AssertionError(
            "Reformulation search IDs do not "
            "exactly match search IDs"
        )

    print("[PASS] Reformulation coverage")

    # ========================================================
    # 10. SUCCESS COVERAGE
    # ========================================================

    if len(success) != len(searches):
        raise AssertionError(
            "Success row count does not "
            "match search row count"
        )

    success_search_ids = set(
        success["search_id"]
    )

    if success_search_ids != search_ids:
        raise AssertionError(
            "Success search IDs do not "
            "exactly match search IDs"
        )

    print("[PASS] Success coverage")

    # ========================================================
    # 11. SUCCESS FLAG INTEGRITY
    # ========================================================

    valid_success_values = {
        True,
        False,
        0,
        1,
    }

    actual_success_values = set(
        success["successful_search"]
        .dropna()
        .unique()
    )

    invalid_success_values = (
        actual_success_values
        - valid_success_values
    )

    if invalid_success_values:
        raise AssertionError(
            f"Unexpected successful_search values: "
            f"{invalid_success_values}"
        )

    print("[PASS] Success flag integrity")

    # ========================================================
    # 12. BUSINESS EVENT TYPES
    # ========================================================

    valid_event_types = {
        "click",
        "dwell",
        "reformulation",
        "success",
    }

    actual_event_types = set(
        events["event_type"].unique()
    )

    invalid_event_types = (
        actual_event_types
        - valid_event_types
    )

    if invalid_event_types:
        raise AssertionError(
            f"Unexpected event types: "
            f"{invalid_event_types}"
        )

    print("[PASS] Business event types valid")

    # ========================================================
    # 13. BUSINESS EVENT TIMESTAMP VALIDATION
    # ========================================================

    missing_event_timestamps = (
        events["event_timestamp"]
        .isna()
        .sum()
    )

    if missing_event_timestamps > 0:
        raise AssertionError(
            f"{missing_event_timestamps:,} business events "
            f"have missing event_timestamp values"
        )

    print("[PASS] Business-event timestamps")

    # ========================================================
    # 14. BUSINESS EVENT FOREIGN KEYS
    # ========================================================

    check_foreign_keys(
        events,
        "search_id",
        searches,
        "search_id",
        "business_events",
        "searches",
    )

    print("[PASS] Business-event foreign keys")

    # ========================================================
    # 15. COUNT RECONCILIATION
    # ========================================================

    print("\n" + "-" * 70)
    print("FINAL DATASET COUNTS")
    print("-" * 70)

    print(
        f"Users                 : {len(users):,}"
    )

    print(
        f"Assignments           : {len(assignments):,}"
    )

    print(
        f"Sessions              : {len(sessions):,}"
    )

    print(
        f"Searches              : {len(searches):,}"
    )

    print(
        f"Search results        : {len(results):,}"
    )

    print(
        f"Reformulation rows    : {len(reformulations):,}"
    )

    print(
        f"Success rows          : {len(success):,}"
    )

    print(
        f"Business events       : {len(events):,}"
    )

    expected_results = (
        len(searches) * 5
    )

    if len(results) != expected_results:
        raise AssertionError(
            f"Expected {expected_results:,} results, "
            f"found {len(results):,}"
        )

    if len(reformulations) != len(searches):
        raise AssertionError(
            "Reformulation count does not "
            "match search count"
        )

    if len(success) != len(searches):
        raise AssertionError(
            "Success count does not "
            "match search count"
        )

    print("[PASS] Count reconciliation")

    # ========================================================
    # 16. EXPERIMENT SANITY CHECK
    # ========================================================

    print("\n" + "-" * 70)
    print("EXPERIMENT SANITY CHECK")
    print("-" * 70)

    for experiment_id in sorted(
        assignments["experiment_id"].unique()
    ):

        experiment_assignments = assignments[
            assignments["experiment_id"] == experiment_id
        ]

        # IMPORTANT:
        # The dataset uses "Control" and "Treatment"
        # with capital C and T.

        control_users = (
            experiment_assignments["variant"]
            == "Control"
        ).sum()

        treatment_users = (
            experiment_assignments["variant"]
            == "Treatment"
        ).sum()

        total_users = len(
            experiment_assignments
        )

        print(
            f"Experiment {experiment_id}: "
            f"control={control_users:,}, "
            f"treatment={treatment_users:,}, "
            f"total={total_users:,}"
        )

        if control_users == 0:
            raise AssertionError(
                f"Experiment {experiment_id} "
                f"has no control users"
            )

        if treatment_users == 0:
            raise AssertionError(
                f"Experiment {experiment_id} "
                f"has no treatment users"
            )

    print(
        "[PASS] All experiments contain "
        "Control + Treatment"
    )

    # ========================================================
    # 17. FINAL RESULT
    # ========================================================

    print("\n" + "=" * 70)
    print("FINAL VALIDATION PASSED")
    print("=" * 70)

    print(
        "\nDataset is structurally ready "
        "for PostgreSQL import."
    )


if __name__ == "__main__":
    main()