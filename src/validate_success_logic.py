import pandas as pd


# ============================================================
# PRYVIA — SUCCESS LOGIC VALIDATION
# ============================================================
# Purpose:
# Independently reconstruct PRYVIA's core success logic
# and verify that all generated CSV files agree.
#
# Success definition:
#   Quality Click
#       = clicked AND dwell_time >= 30 seconds
#
#   Successful Search
#       = has_quality_click AND NOT is_reformulation
#
# This script does NOT modify any dataset.
# It only validates the existing generated data.
# ============================================================


print("=" * 70)
print("PRYVIA — SUCCESS LOGIC VALIDATION")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

results_df = pd.read_csv("search_results_final.csv")

reformulation_df = pd.read_csv("searches_with_reformulation.csv")

success_df = pd.read_csv("search_success_prototype.csv")

business_events_df = pd.read_csv("business_events_prototype.csv")

searches_df = pd.read_csv("searches_prototype.csv")


print("\n[PASS] All required CSV files loaded successfully")


# ============================================================
# 2. BASIC COLUMN VALIDATION
# ============================================================

required_result_columns = {
    "search_id",
    "clicked",
    "dwell_time_seconds",
    "returned_to_search",
}

required_reformulation_columns = {
    "search_id",
    "is_reformulation",
}

required_success_columns = {
    "search_id",
    "is_reformulation",
    "quality_click_count",
    "has_quality_click",
    "successful_search",
}

required_event_columns = {
    "event_id",
    "search_id",
    "event_type",
    "event_timestamp",
}

if not required_result_columns.issubset(results_df.columns):
    missing = required_result_columns - set(results_df.columns)
    raise ValueError(f"[FAIL] Missing result columns: {missing}")

if not required_reformulation_columns.issubset(reformulation_df.columns):
    missing = required_reformulation_columns - set(reformulation_df.columns)
    raise ValueError(f"[FAIL] Missing reformulation columns: {missing}")

if not required_success_columns.issubset(success_df.columns):
    missing = required_success_columns - set(success_df.columns)
    raise ValueError(f"[FAIL] Missing success columns: {missing}")

if not required_event_columns.issubset(business_events_df.columns):
    missing = required_event_columns - set(business_events_df.columns)
    raise ValueError(f"[FAIL] Missing business event columns: {missing}")

print("[PASS] Required columns present")


# ============================================================
# 3. NORMALIZE BOOLEAN COLUMNS
# ============================================================

def normalize_bool(series):
    """
    Convert common CSV boolean representations into real booleans.
    """
    if series.dtype == bool:
        return series

    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            }
        )
    )


results_df["clicked"] = normalize_bool(results_df["clicked"])

results_df["returned_to_search"] = normalize_bool(
    results_df["returned_to_search"]
)

reformulation_df["is_reformulation"] = normalize_bool(
    reformulation_df["is_reformulation"]
)

success_df["is_reformulation"] = normalize_bool(
    success_df["is_reformulation"]
)

success_df["has_quality_click"] = normalize_bool(
    success_df["has_quality_click"]
)

success_df["successful_search"] = normalize_bool(
    success_df["successful_search"]
)


# ============================================================
# 4. CHECK REFORMULATION AND SUCCESS COVERAGE
# ============================================================

search_ids = set(searches_df["search_id"])

reformulation_ids = set(reformulation_df["search_id"])

success_ids = set(success_df["search_id"])


if search_ids != reformulation_ids:
    missing = search_ids - reformulation_ids
    extra = reformulation_ids - search_ids

    raise ValueError(
        f"[FAIL] Reformulation coverage mismatch. "
        f"Missing={len(missing)}, Extra={len(extra)}"
    )


if search_ids != success_ids:
    missing = search_ids - success_ids
    extra = success_ids - search_ids

    raise ValueError(
        f"[FAIL] Success coverage mismatch. "
        f"Missing={len(missing)}, Extra={len(extra)}"
    )


print("[PASS] Every search has reformulation + success record")


# ============================================================
# 5. INDEPENDENTLY CALCULATE QUALITY CLICKS
# ============================================================
# Quality click definition:
#
#   clicked == True
#   AND
#   dwell_time_seconds >= 30
#
# We calculate this directly from search_results_final.csv.
# ============================================================

results_df["independent_quality_click"] = (
    results_df["clicked"]
    & (results_df["dwell_time_seconds"] >= 30)
)


# Count quality clicks per search

quality_click_counts = (
    results_df.groupby("search_id")["independent_quality_click"]
    .sum()
    .astype(int)
    .reset_index()
)

quality_click_counts.rename(
    columns={
        "independent_quality_click": "independent_quality_click_count"
    },
    inplace=True,
)


# ============================================================
# 6. MERGE WITH GENERATED SUCCESS DATA
# ============================================================

validation_df = success_df[
    [
        "search_id",
        "is_reformulation",
        "quality_click_count",
        "has_quality_click",
        "successful_search",
    ]
].copy()


validation_df = validation_df.merge(
    quality_click_counts,
    on="search_id",
    how="left",
)


validation_df["independent_quality_click_count"] = (
    validation_df["independent_quality_click_count"]
    .fillna(0)
    .astype(int)
)


# ============================================================
# 7. VALIDATE QUALITY CLICK COUNT
# ============================================================

quality_count_match = (
    validation_df["quality_click_count"]
    == validation_df["independent_quality_click_count"]
)


if not quality_count_match.all():

    mismatches = validation_df.loc[
        ~quality_count_match
    ]

    print(
        f"[FAIL] Quality-click count mismatch: "
        f"{len(mismatches)} searches"
    )

    print("\nFirst mismatches:")

    print(
        mismatches[
            [
                "search_id",
                "quality_click_count",
                "independent_quality_click_count",
            ]
        ].head(10)
    )

    raise ValueError(
        "Quality-click count validation failed."
    )


print("[PASS] Quality-click counts independently reconstructed")


# ============================================================
# 8. VALIDATE HAS_QUALITY_CLICK
# ============================================================

validation_df["independent_has_quality_click"] = (
    validation_df["independent_quality_click_count"] > 0
)


has_quality_match = (
    validation_df["has_quality_click"]
    == validation_df["independent_has_quality_click"]
)


if not has_quality_match.all():

    mismatches = validation_df.loc[
        ~has_quality_match
    ]

    print(
        f"[FAIL] has_quality_click mismatch: "
        f"{len(mismatches)} searches"
    )

    print("\nFirst mismatches:")

    print(
        mismatches[
            [
                "search_id",
                "has_quality_click",
                "independent_has_quality_click",
            ]
        ].head(10)
    )

    raise ValueError(
        "has_quality_click validation failed."
    )


print("[PASS] has_quality_click logic independently verified")


# ============================================================
# 9. VALIDATE REFORMULATION FLAGS
# ============================================================
# The reformulation flag in success data must agree with
# the dedicated reformulation dataset.
# ============================================================

reformulation_check = reformulation_df[
    [
        "search_id",
        "is_reformulation",
    ]
].copy()


reformulation_check.rename(
    columns={
        "is_reformulation": "source_is_reformulation"
    },
    inplace=True,
)


validation_df = validation_df.merge(
    reformulation_check,
    on="search_id",
    how="left",
)


reformulation_match = (
    validation_df["is_reformulation"]
    == validation_df["source_is_reformulation"]
)


if not reformulation_match.all():

    mismatches = validation_df.loc[
        ~reformulation_match
    ]

    print(
        f"[FAIL] Reformulation mismatch: "
        f"{len(mismatches)} searches"
    )

    print("\nFirst mismatches:")

    print(
        mismatches[
            [
                "search_id",
                "is_reformulation",
                "source_is_reformulation",
            ]
        ].head(10)
    )

    raise ValueError(
        "Reformulation validation failed."
    )


print("[PASS] Reformulation flags independently verified")


# ============================================================
# 10. INDEPENDENTLY CALCULATE SUCCESSFUL SEARCH
# ============================================================
#
# PRYVIA definition:
#
# Successful Search
# =
# has_quality_click
# AND
# NOT reformulated
#
# ============================================================

validation_df["independent_successful_search"] = (
    validation_df["independent_has_quality_click"]
    & (~validation_df["is_reformulation"])
)


successful_match = (
    validation_df["successful_search"]
    == validation_df["independent_successful_search"]
)


if not successful_match.all():

    mismatches = validation_df.loc[
        ~successful_match
    ]

    print(
        f"[FAIL] Successful-search mismatch: "
        f"{len(mismatches)} searches"
    )

    print("\nFirst mismatches:")

    print(
        mismatches[
            [
                "search_id",
                "has_quality_click",
                "is_reformulation",
                "successful_search",
                "independent_successful_search",
            ]
        ].head(10)
    )

    raise ValueError(
        "Successful-search logic validation failed."
    )


print("[PASS] Successful-search logic independently reconstructed")


# ============================================================
# 11. CALCULATE SSR INDEPENDENTLY
# ============================================================

total_searches = len(validation_df)

successful_searches = int(
    validation_df["independent_successful_search"].sum()
)


independent_ssr = (
    successful_searches / total_searches
)


generated_ssr = (
    validation_df["successful_search"].sum()
    / total_searches
)


print("\n" + "-" * 70)
print("SSR VALIDATION")
print("-" * 70)

print(f"Total searches       : {total_searches:,}")
print(f"Successful searches  : {successful_searches:,}")
print(f"Independent SSR      : {independent_ssr:.4%}")
print(f"Generated SSR        : {generated_ssr:.4%}")


if abs(independent_ssr - generated_ssr) > 1e-12:
    raise ValueError(
        "[FAIL] Independent SSR does not match generated SSR."
    )


print("[PASS] SSR independently reconstructed")


# ============================================================
# 12. BUSINESS EVENT VALIDATION
# ============================================================
# Expected events:
#
# click          = clicked result rows
# dwell          = rows with dwell > 0
# reformulation  = reformulated searches
# success        = successful searches
# ============================================================

expected_click_events = int(
    results_df["clicked"].sum()
)

expected_dwell_events = int(
    (results_df["dwell_time_seconds"] > 0).sum()
)

expected_reformulation_events = int(
    reformulation_df["is_reformulation"].sum()
)

expected_success_events = int(
    validation_df["independent_successful_search"].sum()
)


actual_event_counts = (
    business_events_df["event_type"]
    .value_counts()
)


actual_click_events = int(
    actual_event_counts.get("click", 0)
)

actual_dwell_events = int(
    actual_event_counts.get("dwell", 0)
)

actual_reformulation_events = int(
    actual_event_counts.get("reformulation", 0)
)

actual_success_events = int(
    actual_event_counts.get("success", 0)
)


print("\n" + "-" * 70)
print("BUSINESS EVENT VALIDATION")
print("-" * 70)

print(
    f"Click events         : "
    f"expected={expected_click_events:,}, "
    f"actual={actual_click_events:,}"
)

print(
    f"Dwell events         : "
    f"expected={expected_dwell_events:,}, "
    f"actual={actual_dwell_events:,}"
)

print(
    f"Reformulation events : "
    f"expected={expected_reformulation_events:,}, "
    f"actual={actual_reformulation_events:,}"
)

print(
    f"Success events       : "
    f"expected={expected_success_events:,}, "
    f"actual={actual_success_events:,}"
)


if expected_click_events != actual_click_events:
    raise ValueError("[FAIL] Click event count mismatch.")

if expected_dwell_events != actual_dwell_events:
    raise ValueError("[FAIL] Dwell event count mismatch.")

if expected_reformulation_events != actual_reformulation_events:
    raise ValueError(
        "[FAIL] Reformulation event count mismatch."
    )

if expected_success_events != actual_success_events:
    raise ValueError("[FAIL] Success event count mismatch.")


print("[PASS] Business event counts reconcile with source data")


# ============================================================
# 13. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL SUCCESS LOGIC VALIDATION PASSED")
print("=" * 70)

print(
    "\nPRYVIA's core metric logic is internally consistent:"
)

print(
    "  Click"
    " → Quality Click"
    " → Has Quality Click"
    " → Not Reformulated"
    " → Successful Search"
    " → SSR"
)

print(
    "\nThe dataset is ready for the PostgreSQL import stage."
)