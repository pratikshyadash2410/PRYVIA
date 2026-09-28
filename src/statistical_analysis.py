"""
PRYVIA — Statistical Analysis

This module contains the statistical analysis layer for the PRYVIA
search-ranking A/B experiment.

Randomization unit
------------------
Users are randomly assigned to Control or Treatment and remain in that
variant throughout the experiment.

Unit of analysis
----------------
Search-level metrics are aggregated to the USER level before statistical
comparison. This prevents repeated searches from the same user from being
treated as independent observations.

This module calculates:
    - Sample Ratio Mismatch (SRM)
    - Power and sample-size requirements
    - Successful Search Rate (SSR)
    - SSR confidence interval
    - Search error rate
    - Search latency
    - Reformulation rate
    - Click-through rate (CTR)
    - Overall guardrail status

This module does NOT:
    - Render Streamlit UI
    - Make ship / don't-ship decisions
    - Contain presentation logic

The decision engine is implemented separately in:
    src/decision_engine.py
"""

import numpy as np
import pandas as pd
from scipy.stats import chisquare, mannwhitneyu, ttest_ind
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


# =============================================================================
# EXPERIMENT CONSTANTS
# =============================================================================

ALPHA = 0.05
TARGET_POWER = 0.80

N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 42

EXPECTED_ALLOCATION_RATIO = 0.50

CONTROL_VARIANT = "Control"
TREATMENT_VARIANT = "Treatment"


# =============================================================================
# PRE-REGISTERED EXPERIMENT DESIGN
# =============================================================================

# Baseline SSR and MDE are defined before evaluating experiment results.
# All four simulated experiments use the same planning assumptions.
EXPERIMENT_DESIGN = {
    1: {
        "baseline_ssr": 0.65,
        "mde_pp": 5.0,
    },
    2: {
        "baseline_ssr": 0.65,
        "mde_pp": 5.0,
    },
    3: {
        "baseline_ssr": 0.65,
        "mde_pp": 5.0,
    },
    4: {
        "baseline_ssr": 0.65,
        "mde_pp": 5.0,
    },
}

DEFAULT_EXPERIMENT_DESIGN = {
    "baseline_ssr": 0.65,
    "mde_pp": 5.0,
}


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def _require_columns(df, required_columns, dataframe_name):
    """
    Validate that a dataframe contains the columns required by the analysis.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    required_columns : iterable
        Column names required by the analysis.
    dataframe_name : str
        Human-readable dataframe name used in the error message.

    Raises
    ------
    ValueError
        If one or more required columns are missing.
    """
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataframe_name} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )


def _validate_variant_values(assignments):
    """Validate that experiment assignments use the expected variant labels."""
    valid_variants = {CONTROL_VARIANT, TREATMENT_VARIANT}

    unexpected_variants = set(assignments["variant"].dropna().unique()) - valid_variants

    if unexpected_variants:
        raise ValueError(
            "Unexpected variant values found: "
            f"{sorted(unexpected_variants)}. "
            f"Expected only '{CONTROL_VARIANT}' and '{TREATMENT_VARIANT}'."
        )


# =============================================================================
# USER-LEVEL AGGREGATION
# =============================================================================

def _user_level_proportion(df, id_col, flag_col):
    """
    Calculate each user's personal proportion.

    Example
    -------
    For SSR:

        user SSR =
            successful searches / total searches

    The returned dataframe contains one row per user and variant.

    Parameters
    ----------
    df : pandas.DataFrame
        Search- or search-level dataframe.
    id_col : str
        Observation identifier, such as search_id.
    flag_col : str
        Binary metric flag, such as successful_search.

    Returns
    -------
    pandas.DataFrame
        Columns:
            user_id
            variant
            n
            k
            rate
    """
    _require_columns(
        df,
        ["user_id", "variant", id_col, flag_col],
        "proportion dataframe",
    )

    agg = (
        df.groupby(["user_id", "variant"])
        .agg(
            n=(id_col, "count"),
            k=(flag_col, "sum"),
        )
        .reset_index()
    )

    agg["rate"] = agg["k"] / agg["n"]

    return agg


def _user_level_median(df, value_col):
    """
    Calculate one median value per user.

    Used for latency because each user may generate multiple searches.

    Parameters
    ----------
    df : pandas.DataFrame
        Search-level dataframe.
    value_col : str
        Numeric value to aggregate.

    Returns
    -------
    pandas.DataFrame
        One row per user and variant with the user's median value.
    """
    _require_columns(
        df,
        ["user_id", "variant", value_col],
        "median dataframe",
    )

    agg = (
        df.groupby(["user_id", "variant"])[value_col]
        .median()
        .reset_index()
        .rename(columns={value_col: "value"})
    )

    return agg


# =============================================================================
# STATISTICAL COMPARISONS
# =============================================================================

def _compare_rate(agg, higher_is_better):
    """
    Compare user-level rates using Welch's independent-samples t-test.

    The comparison is performed on one rate per user rather than on pooled
    search-level observations.

    Parameters
    ----------
    agg : pandas.DataFrame
        User-level rate dataframe.
    higher_is_better : bool
        Whether an increase in the metric is considered favorable.

    Returns
    -------
    dict
        Control/treatment rates, difference, p-value, test statistic,
        significance, and guardrail health.
    """
    control = agg.loc[
        agg["variant"] == CONTROL_VARIANT,
        "rate",
    ]

    treatment = agg.loc[
        agg["variant"] == TREATMENT_VARIANT,
        "rate",
    ]

    if control.empty or treatment.empty:
        raise ValueError(
            "Both Control and Treatment must contain at least one user."
        )

    stat, p_value = ttest_ind(
        treatment,
        control,
        equal_var=False,
    )

    control_value = float(control.mean())
    treatment_value = float(treatment.mean())
    difference = treatment_value - control_value

    if higher_is_better:
        healthy = not (
            treatment_value < control_value
            and p_value < ALPHA
        )
    else:
        healthy = not (
            treatment_value > control_value
            and p_value < ALPHA
        )

    return {
        "control": control_value,
        "treatment": treatment_value,
        "difference_pp": difference * 100,
        "p_value": float(p_value),
        "t_stat": float(stat),
        "healthy": bool(healthy),
        "significant": bool(p_value < ALPHA),
        "n_control_users": int(len(control)),
        "n_treatment_users": int(len(treatment)),
    }


def _compare_median(agg, higher_is_better):
    """
    Compare user-level medians using a two-sided Mann-Whitney U test.

    Parameters
    ----------
    agg : pandas.DataFrame
        User-level median dataframe.
    higher_is_better : bool
        Whether an increase in the metric is considered favorable.

    Returns
    -------
    dict
        Control/treatment medians, difference, p-value, test statistic,
        significance, and guardrail health.
    """
    control = agg.loc[
        agg["variant"] == CONTROL_VARIANT,
        "value",
    ]

    treatment = agg.loc[
        agg["variant"] == TREATMENT_VARIANT,
        "value",
    ]

    if control.empty or treatment.empty:
        raise ValueError(
            "Both Control and Treatment must contain at least one user."
        )

    stat, p_value = mannwhitneyu(
        treatment,
        control,
        alternative="two-sided",
    )

    control_value = float(control.median())
    treatment_value = float(treatment.median())
    difference = treatment_value - control_value

    if higher_is_better:
        healthy = not (
            treatment_value < control_value
            and p_value < ALPHA
        )
    else:
        healthy = not (
            treatment_value > control_value
            and p_value < ALPHA
        )

    return {
        "control": control_value,
        "treatment": treatment_value,
        "difference": difference,
        "p_value": float(p_value),
        "u_stat": float(stat),
        "healthy": bool(healthy),
        "significant": bool(p_value < ALPHA),
    }


# =============================================================================
# BOOTSTRAP CONFIDENCE INTERVAL
# =============================================================================

def _bootstrap_ci(
    control_array,
    treatment_array,
    n_boot=N_BOOTSTRAP,
    seed=BOOTSTRAP_SEED,
):
    """
    Estimate a 95% bootstrap confidence interval for:

        Treatment mean user-level rate
        minus
        Control mean user-level rate

    Parameters
    ----------
    control_array : array-like
        User-level Control rates.
    treatment_array : array-like
        User-level Treatment rates.
    n_boot : int
        Number of bootstrap resamples.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    tuple[float, float]
        Lower and upper bounds of the 95% confidence interval.
    """
    control_array = np.asarray(control_array, dtype=float)
    treatment_array = np.asarray(treatment_array, dtype=float)

    if len(control_array) == 0 or len(treatment_array) == 0:
        raise ValueError(
            "Both Control and Treatment must contain observations "
            "for bootstrap confidence intervals."
        )

    rng = np.random.default_rng(seed)

    control_samples = rng.choice(
        control_array,
        size=(n_boot, len(control_array)),
        replace=True,
    )

    treatment_samples = rng.choice(
        treatment_array,
        size=(n_boot, len(treatment_array)),
        replace=True,
    )

    differences = (
        treatment_samples.mean(axis=1)
        - control_samples.mean(axis=1)
    )

    lower = np.percentile(differences, 2.5)
    upper = np.percentile(differences, 97.5)

    return float(lower), float(upper)


# =============================================================================
# CTR PREPARATION
# =============================================================================

def _build_search_level_ctr(searches_with_variant, results_with_variant):
    """
    Build one row per search for CTR analysis.

    CTR definition:
        searches with at least one clicked result
        divided by
        total searches

    Result-level rows are first collapsed to the search level so that a
    search with multiple clicked results is still counted once.
    """
    _require_columns(
        searches_with_variant,
        ["search_id", "user_id", "variant"],
        "searches_with_variant",
    )

    _require_columns(
        results_with_variant,
        ["search_id", "user_id", "variant", "clicked"],
        "results_with_variant",
    )

    click_by_search = (
        results_with_variant
        .groupby(
            ["search_id", "user_id", "variant"]
        )
        .agg(
            was_clicked=("clicked", "max")
        )
        .reset_index()
    )

    ctr_searches = (
        searches_with_variant[
            ["search_id", "user_id", "variant"]
        ]
        .drop_duplicates()
        .merge(
            click_by_search,
            on=["search_id", "user_id", "variant"],
            how="left",
        )
    )

    ctr_searches["was_clicked"] = (
        ctr_searches["was_clicked"]
        .fillna(False)
        .astype(int)
    )

    return ctr_searches


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_statistical_analysis(
    assignments,
    search_success,
    sessions,
    searches,
    results,
    experiment_id,
):
    """
    Run the complete statistical analysis for one PRYVIA experiment.

    The experiment is first scoped through user assignments. All downstream
    session, search, and result data is then restricted to those users.

    Parameters
    ----------
    assignments : pandas.DataFrame
        Experiment assignment data.
    search_success : pandas.DataFrame
        Search-level data containing successful_search.
    sessions : pandas.DataFrame
        Search-session data.
    searches : pandas.DataFrame
        Search-level operational data.
    results : pandas.DataFrame
        Search-result data.
    experiment_id : int
        Experiment to analyze.

    Returns
    -------
    dict
        Structured statistical evidence consumed by the PRYVIA decision engine
        and Streamlit application.
    """

    # -------------------------------------------------------------------------
    # Validate inputs
    # -------------------------------------------------------------------------

    _require_columns(
        assignments,
        ["experiment_id", "user_id", "variant"],
        "assignments",
    )

    _require_columns(
        search_success,
        ["search_id", "session_id", "successful_search", "is_reformulation"],
        "search_success",
    )

    _require_columns(
        sessions,
        ["session_id", "user_id"],
        "sessions",
    )

    _require_columns(
        searches,
        [
            "search_id",
            "session_id",
            "search_latency_ms",
            "search_error",
        ],
        "searches",
    )

    _require_columns(
        results,
        ["search_id", "clicked"],
        "results",
    )

    # -------------------------------------------------------------------------
    # Experiment design assumptions
    # -------------------------------------------------------------------------

    design = EXPERIMENT_DESIGN.get(
        experiment_id,
        DEFAULT_EXPERIMENT_DESIGN,
    )

    baseline_ssr = design["baseline_ssr"]
    mde_pp = design["mde_pp"]
    mde = mde_pp / 100

    # -------------------------------------------------------------------------
    # Scope all data to the selected experiment
    # -------------------------------------------------------------------------

    assignments = assignments.loc[
        assignments["experiment_id"] == experiment_id
    ].copy()

    # Support the historical A/B labels used by earlier generated datasets.
    assignments["variant"] = assignments["variant"].replace(
        {
            "A": CONTROL_VARIANT,
            "B": TREATMENT_VARIANT,
        }
    )

    if assignments.empty:
        raise ValueError(
            f"No assignments found for experiment_id={experiment_id}."
        )

    _validate_variant_values(assignments)

    experiment_user_ids = set(
        assignments["user_id"].unique()
    )

    sessions = sessions.loc[
        sessions["user_id"].isin(experiment_user_ids)
    ].copy()

    experiment_session_ids = set(
        sessions["session_id"].unique()
    )

    searches = searches.loc[
        searches["session_id"].isin(experiment_session_ids)
    ].copy()

    # -------------------------------------------------------------------------
    # SRM CHECK
    # -------------------------------------------------------------------------

    observed = (
        assignments["variant"]
        .value_counts()
        .reindex(
            [CONTROL_VARIANT, TREATMENT_VARIANT]
        )
        .fillna(0)
    )

    total_users = int(observed.sum())

    expected = np.array(
        [
            total_users * EXPECTED_ALLOCATION_RATIO,
            total_users * (1 - EXPECTED_ALLOCATION_RATIO),
        ]
    )

    srm_chi2, srm_p = chisquare(
        f_obs=observed.values,
        f_exp=expected,
    )

    srm_passed = bool(srm_p >= ALPHA)

    control_users = int(observed[CONTROL_VARIANT])
    treatment_users = int(observed[TREATMENT_VARIANT])

    # -------------------------------------------------------------------------
    # POWER / SAMPLE-SIZE CALCULATION
    # -------------------------------------------------------------------------

    target_ssr = baseline_ssr + mde

    required_effect = proportion_effectsize(
        baseline_ssr,
        target_ssr,
    )

    power_model = NormalIndPower()

    required_per_group = int(
        np.ceil(
            power_model.solve_power(
                effect_size=required_effect,
                power=TARGET_POWER,
                alpha=ALPHA,
                ratio=1.0,
                alternative="two-sided",
            )
        )
    )

    required_total = required_per_group * 2

    achieved_power = float(
        power_model.power(
            effect_size=required_effect,
            nobs1=float(control_users)
            if control_users > 0
            else 1.0,
            alpha=ALPHA,
            ratio=(
                treatment_users / control_users
                if control_users > 0
                else 1.0
            ),
            alternative="two-sided",
        )
    )

    # -------------------------------------------------------------------------
    # BUILD USER → SESSION → SEARCH DATASETS
    # -------------------------------------------------------------------------

    user_variant = assignments[
        ["user_id", "variant"]
    ]

    session_user = sessions[
        ["session_id", "user_id"]
    ]

    user_searches = (
        search_success
        .merge(
            session_user,
            on="session_id",
            how="inner",
        )
        .merge(
            user_variant,
            on="user_id",
            how="inner",
        )
    )

    searches_with_variant = (
        searches
        .merge(
            session_user,
            on="session_id",
            how="inner",
        )
        .merge(
            user_variant,
            on="user_id",
            how="inner",
        )
    )

    results_with_variant = (
        results
        .merge(
            searches_with_variant[
                ["search_id", "user_id", "variant"]
            ],
            on="search_id",
            how="inner",
        )
    )

    # -------------------------------------------------------------------------
    # PRIMARY METRIC — SUCCESSFUL SEARCH RATE
    # -------------------------------------------------------------------------

    ssr_agg = _user_level_proportion(
        user_searches,
        id_col="search_id",
        flag_col="successful_search",
    )

    ssr_result = _compare_rate(
        ssr_agg,
        higher_is_better=True,
    )

    control_array = ssr_agg.loc[
        ssr_agg["variant"] == CONTROL_VARIANT,
        "rate",
    ].to_numpy()

    treatment_array = ssr_agg.loc[
        ssr_agg["variant"] == TREATMENT_VARIANT,
        "rate",
    ].to_numpy()

    ci_lower, ci_upper = _bootstrap_ci(
        control_array,
        treatment_array,
    )

    relative_lift_pct = (
        (
            ssr_result["treatment"]
            - ssr_result["control"]
        )
        / ssr_result["control"]
        * 100
        if ssr_result["control"] != 0
        else 0.0
    )

    # -------------------------------------------------------------------------
    # GUARDRAIL — SEARCH ERROR RATE
    # -------------------------------------------------------------------------

    error_agg = _user_level_proportion(
        searches_with_variant,
        id_col="search_id",
        flag_col="search_error",
    )

    error_result = _compare_rate(
        error_agg,
        higher_is_better=False,
    )

    # -------------------------------------------------------------------------
    # GUARDRAIL — SEARCH LATENCY
    # -------------------------------------------------------------------------

    latency_data = searches_with_variant.dropna(
        subset=["search_latency_ms"]
    )

    latency_agg = _user_level_median(
        latency_data,
        value_col="search_latency_ms",
    )

    latency_result = _compare_median(
        latency_agg,
        higher_is_better=False,
    )

    # -------------------------------------------------------------------------
    # SECONDARY METRIC — REFORMULATION
    # -------------------------------------------------------------------------

    reform_agg = _user_level_proportion(
        user_searches,
        id_col="search_id",
        flag_col="is_reformulation",
    )

    reform_result = _compare_rate(
        reform_agg,
        higher_is_better=False,
    )

    # -------------------------------------------------------------------------
    # SECONDARY METRIC — CTR
    # -------------------------------------------------------------------------

    ctr_searches = _build_search_level_ctr(
        searches_with_variant,
        results_with_variant,
    )

    ctr_agg = _user_level_proportion(
        ctr_searches,
        id_col="search_id",
        flag_col="was_clicked",
    )

    ctr_result = _compare_rate(
        ctr_agg,
        higher_is_better=True,
    )

    # -------------------------------------------------------------------------
    # OVERALL GUARDRAIL STATUS
    # -------------------------------------------------------------------------

    guardrails_healthy = bool(
        error_result["healthy"]
        and latency_result["healthy"]
    )

    # -------------------------------------------------------------------------
    # RETURN STRUCTURED EVIDENCE
    # -------------------------------------------------------------------------

    return {
        "experiment_id": experiment_id,

        "srm": {
            "passed": srm_passed,
            "chi2": float(srm_chi2),
            "p_value": float(srm_p),
            "control_users": control_users,
            "treatment_users": treatment_users,
            "total_users": total_users,
        },

        "power": {
            "baseline_ssr": baseline_ssr,
            "target_ssr": target_ssr,
            "mde_pp": mde_pp,
            "required_per_group": required_per_group,
            "required_total": required_total,
            "actual_users": total_users,
            "achieved_power": achieved_power,
            "adequate": total_users >= required_total,
        },

        "ssr": {
            "control_rate": ssr_result["control"],
            "treatment_rate": ssr_result["treatment"],
            "lift_pp": ssr_result["difference_pp"],
            "relative_lift_pct": relative_lift_pct,
            "p_value": ssr_result["p_value"],
            "t_stat": ssr_result["t_stat"],
            "ci_lower_pp": ci_lower * 100,
            "ci_upper_pp": ci_upper * 100,
            "significant": ssr_result["significant"],
            "positive": ssr_result["difference_pp"] > 0,
            "n_control_users": ssr_result["n_control_users"],
            "n_treatment_users": ssr_result["n_treatment_users"],
        },

        "error": {
            "control_rate": error_result["control"],
            "treatment_rate": error_result["treatment"],
            "difference_pp": error_result["difference_pp"],
            "p_value": error_result["p_value"],
            "healthy": error_result["healthy"],
        },

        "latency": {
            "control_median_ms": latency_result["control"],
            "treatment_median_ms": latency_result["treatment"],
            "difference_ms": latency_result["difference"],
            "p_value": latency_result["p_value"],
            "healthy": latency_result["healthy"],
        },

        "reformulation": {
            "control_rate": reform_result["control"],
            "treatment_rate": reform_result["treatment"],
            "difference_pp": reform_result["difference_pp"],
            "p_value": reform_result["p_value"],
            "significant": reform_result["significant"],
        },

        "ctr": {
            "control_rate": ctr_result["control"],
            "treatment_rate": ctr_result["treatment"],
            "difference_pp": ctr_result["difference_pp"],
            "p_value": ctr_result["p_value"],
            "significant": ctr_result["significant"],
        },

        "guardrails_healthy": guardrails_healthy,

        # Used by the Streamlit app for exploratory segment analysis.
        "user_level_ssr": ssr_agg,
    }