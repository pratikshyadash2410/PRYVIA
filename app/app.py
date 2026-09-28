"""
PRYVIA — Experiment Decision Engine (Streamlit UI)
====================================================

Phase 5 of the PRYVIA project: this file is the presentation layer.
It renders and decides nothing; the only computation here is a light,
display-only aggregation for the exploratory segment view.

    src/statistical_analysis.py  -> computes the evidence (SRM, power,
                                     SSR, guardrails, diagnostics)
    src/decision_engine.py       -> turns that evidence into a verdict
                                     and every piece of explanation text
    app/app.py (this file)       -> renders both, with zero experiment
                                     decision logic of its own

That separation is deliberate: swap this file for a different UI
tomorrow (Power BI, a CLI report, another framework) and the evidence
and the verdict would not change, because neither lives here.

Run with:
    streamlit run app/app.py

Expects the frozen experiment CSVs in src/:
    experiment_assignments_prototype.csv
    search_success_prototype.csv
    search_sessions_prototype.csv
    searches_prototype.csv
    search_results_final.csv
    users_prototype.csv
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================================================
# PATHS
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

# Make the project root importable so that src.* works
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT MODULES
# ============================================================

from src.statistical_analysis import run_statistical_analysis
from src.decision_engine import (
    evaluate_experiment,
    RULE_TABLE_FOR_DISPLAY,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="PRYVIA — Experiment Decision Engine",
    page_icon="◆",
    layout="wide",
)


# ============================================================
# CUSTOM CSS
#
# The verdict card is colour-coded by severity, not just by verdict
# text: a "confidently null" DON'T SHIP and a "significant regression"
# DON'T SHIP are very different findings and shouldn't read the same
# way at a glance. severity ("positive" / "negative" / "caution" /
# "neutral") comes straight from decision_engine.py, so the mapping
# below is the only place that severity's colour is decided.
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        .pryvia-brand {
            font-size: 1.65rem;
            font-weight: 900;
            letter-spacing: 0.34em;
            margin-bottom: 0.15rem;
        }

        .subtitle {
            color: #777;
            font-size: 0.95rem;
            margin-bottom: 1.8rem;
        }

        .hero-title {
            font-size: 2.25rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .hero-description {
            color: #777;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .verdict-card {
            border: 1px solid #d9d9d9;
            border-radius: 14px;
            padding: 1.4rem 1.5rem;
            margin: 1rem 0 1.5rem 0;
            background: #fafafa;
        }

        .verdict-card.severity-positive {
            border-color: #1D9E75;
            background: #F0FBF7;
        }

        .verdict-card.severity-negative {
            border-color: #E24B4A;
            background: #FDF2F2;
        }

        .verdict-card.severity-caution {
            border-color: #BA7517;
            background: #FDF8EF;
        }

        .verdict-card.severity-neutral {
            border-color: #9A9992;
            background: #FAFAFA;
        }

        .verdict-card.severity-positive .verdict-title {
            color: #1D9E75;
        }

        .verdict-card.severity-negative .verdict-title {
            color: #E24B4A;
        }

        .verdict-card.severity-caution .verdict-title {
            color: #BA7517;
        }

        .verdict-card.severity-neutral .verdict-title {
            color: #5F5E5A;
        }

        .verdict-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #777;
        }

        .verdict-title {
            font-size: 2rem;
            font-weight: 850;
            margin-top: 0.25rem;
        }

        .verdict-sublabel {
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0.75;
            margin-top: 0.15rem;
        }

        .verdict-reason {
            margin-top: 0.65rem;
            font-size: 1rem;
            color: #444;
        }

        .metric-card {
            border: 1px solid #dedede;
            border-radius: 12px;
            padding: 1rem;
            min-height: 125px;
        }

        .metric-label {
            color: #777;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .metric-value {
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }

        .metric-sub {
            color: #777;
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 800;
            margin-top: 1.7rem;
            margin-bottom: 0.7rem;
        }

        .explanation-box {
            border-left: 4px solid #555;
            padding: 0.8rem 1rem;
            background: #fafafa;
            border-radius: 0 8px 8px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
#
# One export per table, cached so Streamlit doesn't re-read six CSVs
# from disk on every rerun (every widget interaction reruns the whole
# script top to bottom).
# ============================================================

@st.cache_data
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

    users = pd.read_csv(
        SRC_DIR / "users_prototype.csv"
    )

    return (
        assignments,
        search_success,
        sessions,
        searches,
        results,
        users,
    )


(
    assignments,
    search_success,
    sessions,
    searches,
    results,
    users,
) = load_data()


# ============================================================
# CACHED ANALYSIS
#
# Without this, Streamlit re-runs the full statistical analysis --
# including the 10,000-sample bootstrap -- on every single widget
# interaction (e.g. every time the segment radio button below is
# clicked), since Streamlit reruns the whole script top-to-bottom
# on any interaction. Caching on experiment_id keeps that instant.
# ============================================================

@st.cache_data(show_spinner="Running statistical analysis...")
def get_analysis(
    experiment_id,
    assignments,
    search_success,
    sessions,
    searches,
    results,
):
    return run_statistical_analysis(
        experiment_id=experiment_id,
        assignments=assignments,
        search_success=search_success,
        sessions=sessions,
        searches=searches,
        results=results,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="pryvia-brand">PRYVIA</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Product Analytics · Search Ranking Experimentation</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero-title">Experiment Decision Engine</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero-description">'
    'Evaluate search-ranking experiments using statistical evidence, '
    'guardrails, and predefined shipping rules.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# EXPERIMENT SELECTOR
# ============================================================

experiment_labels = {
    1: "Experiment 1 — Clear winner",
    2: "Experiment 2 — Inconclusive / underpowered",
    3: "Experiment 3 — Segment signal",
    4: "Experiment 4 — Guardrail violation",
}

selected_label = st.selectbox(
    "Explore experiment",
    options=list(experiment_labels.values()),
    index=0,
)

experiment_id = next(
    exp_id
    for exp_id, label in experiment_labels.items()
    if label == selected_label
)


# ============================================================
# RUN STATISTICAL ANALYSIS (cached)
# ============================================================

analysis = get_analysis(
    experiment_id,
    assignments,
    search_success,
    sessions,
    searches,
    results,
)


# ============================================================
# DECISION ENGINE
# ============================================================

decision = evaluate_experiment(analysis)

verdict = decision["verdict"]
reason = decision["reason"]
rule_triggered = decision["rule_triggered"]
severity = decision["severity"]


# ============================================================
# VERDICT
# ============================================================

st.markdown(
    f"""
    <div class="verdict-card severity-{severity}">
        <div class="verdict-label">Final recommendation</div>
        <div class="verdict-title">{verdict}</div>
        <div class="verdict-sublabel">
            Rule {rule_triggered} · {decision["rule_label"]}
        </div>
        <div class="verdict-reason">{reason}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# EXPERIMENT HEALTH
# ============================================================

st.markdown(
    '<div class="section-title">Experiment health</div>',
    unsafe_allow_html=True,
)

health_col1, health_col2, health_col3 = st.columns(3)


# SRM
srm = analysis["srm"]

with health_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">SRM check</div>
            <div class="metric-value">
                {"PASS" if srm["passed"] else "FAIL"}
            </div>
            <div class="metric-sub">
                Control: {srm["control_users"]:,} ·
                Treatment: {srm["treatment_users"]:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Power
power = analysis["power"]

with health_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Statistical power</div>
            <div class="metric-value">
                {"ADEQUATE" if power["adequate"] else "UNDERPOWERED"}
            </div>
            <div class="metric-sub">
                Required total: {power["required_total"]:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Guardrails
with health_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Guardrails</div>
            <div class="metric-value">
                {"HEALTHY" if analysis["guardrails_healthy"] else "BREACH"}
            </div>
            <div class="metric-sub">
                Error rate + latency
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PRIMARY METRIC — SSR
# ============================================================

st.markdown(
    '<div class="section-title">Primary metric — Successful Search Rate</div>',
    unsafe_allow_html=True,
)

ssr = analysis["ssr"]

ssr_col1, ssr_col2, ssr_col3 = st.columns(3)

with ssr_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Control SSR</div>
            <div class="metric-value">{ssr["control_rate"]:.2%}</div>
            <div class="metric-sub">User-level mean</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with ssr_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Treatment SSR</div>
            <div class="metric-value">{ssr["treatment_rate"]:.2%}</div>
            <div class="metric-sub">User-level mean</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with ssr_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Lift</div>
            <div class="metric-value">
                {ssr["lift_pp"]:+.2f} pp
            </div>
            <div class="metric-sub">
                95% CI: {ssr["ci_lower_pp"]:+.2f} to
                {ssr["ci_upper_pp"]:+.2f} pp
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SSR CONFIDENCE INTERVAL
# ============================================================

st.markdown(
    '<div class="section-title">SSR treatment effect</div>',
    unsafe_allow_html=True,
)

fig, ax = plt.subplots(figsize=(10, 2.8))

effect = ssr["lift_pp"]
ci_lower = ssr["ci_lower_pp"]
ci_upper = ssr["ci_upper_pp"]
mde = power["mde_pp"]


# Dynamic axis so a wide CI never clips
axis_max = max(
    mde,
    abs(ci_lower),
    abs(ci_upper),
) * 1.2


# Zero-effect reference line
ax.axvline(
    0,
    linewidth=1.5,
    linestyle="--",
)


# MDE boundaries
ax.axvline(
    mde,
    linewidth=1,
    linestyle=":",
)

ax.axvline(
    -mde,
    linewidth=1,
    linestyle=":",
)


# Point estimate with 95% CI error bar
ax.errorbar(
    effect,
    0,
    xerr=[
        [effect - ci_lower],
        [ci_upper - effect],
    ],
    fmt="o",
    markersize=8,
    capsize=7,
    linewidth=2,
)

ax.set_xlim(-axis_max, axis_max)
ax.set_yticks([])
ax.set_xlabel("Treatment effect on SSR (percentage points)")

ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)

st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.caption(
    f"MDE = ±{mde:.2f} percentage points. "
    "Dashed line = no effect. Dotted lines = MDE boundaries."
)


# ============================================================
# GUARDRAILS
#
# Only these two feed the decision engine (see decision_engine.py,
# rule 6). CTR and reformulation below are diagnostic context only.
# ============================================================

st.markdown(
    '<div class="section-title">Guardrails</div>',
    unsafe_allow_html=True,
)

guard_col1, guard_col2 = st.columns(2)


# Error rate
error = analysis["error"]

with guard_col1:
    error_status = "HEALTHY" if error["healthy"] else "BREACH"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Search error rate</div>
            <div class="metric-value">{error_status}</div>
            <div class="metric-sub">
                Control: {error["control_rate"]:.2%}
                · Treatment: {error["treatment_rate"]:.2%}
                · Δ {error["difference_pp"]:+.2f} pp
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Latency
latency = analysis["latency"]

with guard_col2:
    latency_status = "HEALTHY" if latency["healthy"] else "BREACH"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Search latency</div>
            <div class="metric-value">{latency_status}</div>
            <div class="metric-sub">
                Control median: {latency["control_median_ms"]:.1f} ms
                · Treatment median: {latency["treatment_median_ms"]:.1f} ms
                · Δ {latency["difference_ms"]:+.1f} ms
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SECONDARY DIAGNOSTICS
# ============================================================

st.markdown(
    '<div class="section-title">Secondary diagnostics</div>',
    unsafe_allow_html=True,
)

diag_col1, diag_col2 = st.columns(2)


# Reformulation
reformulation = analysis["reformulation"]

with diag_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reformulation rate</div>
            <div class="metric-value">
                {reformulation["treatment_rate"]:.2%}
            </div>
            <div class="metric-sub">
                Control: {reformulation["control_rate"]:.2%}
                · Δ {reformulation["difference_pp"]:+.2f} pp
                <br>
                Reformulation = another search within 300 seconds (5 minutes)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# CTR
ctr = analysis["ctr"]

with diag_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Click-through rate</div>
            <div class="metric-value">
                {ctr["treatment_rate"]:.2%}
            </div>
            <div class="metric-sub">
                Control: {ctr["control_rate"]:.2%}
                · Δ {ctr["difference_pp"]:+.2f} pp
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.caption(
    "CTR and reformulation are secondary diagnostic metrics. "
    "They do not override the primary SSR decision."
)


# ============================================================
# DECISION EXPLANATION
#
# Every string here comes from decision_engine.py -- this file has
# no per-rule if/elif chain of its own to keep in sync.
# ============================================================

st.markdown(
    '<div class="section-title">Why this decision?</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="explanation-box">
        <strong>Rule {rule_triggered}: {decision["rule_label"]}</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

for bullet in decision["explanation_bullets"]:
    st.markdown(f"- {bullet}")


# ============================================================
# DECISION RULES
# ============================================================

with st.expander("Decision rules", expanded=False):

    rules_df = pd.DataFrame(
        RULE_TABLE_FOR_DISPLAY,
        columns=["Priority", "Condition", "Decision"],
    )

    st.dataframe(
        rules_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# METHODOLOGY
# ============================================================

with st.expander("Methodology", expanded=False):

    st.markdown(
        """
### Randomization

Users are randomly assigned to Control or Treatment and remain
sticky to that variant throughout the experiment.

### Primary metric

**Successful Search Rate (SSR)** is calculated at search level:

A search is successful when it produces a quality click and does not
require reformulation.

A quality click requires:

- A result click
- At least 30 seconds of dwell time

### Statistical unit

Because randomization occurs at the **user level**, rate metrics are
aggregated to the user level before treatment comparison.

This avoids incorrectly treating repeated searches from the same user
as independent observations.

### Confidence interval

SSR treatment effect is estimated as:

**Treatment SSR − Control SSR**

The confidence interval is obtained using bootstrap resampling at the
user level.

### SRM

Sample Ratio Mismatch checks whether the observed Control/Treatment
allocation is consistent with the expected 50/50 randomization.

### Guardrails

Two technical guardrails are evaluated:

- Search error rate
- Search latency

A positive SSR result with a guardrail breach does not receive a clean
SHIP decision.

### Reformulation

A reformulation is detected when another search occurs within the same
session within **300 seconds (5 minutes)** of the previous search.

### Decision hierarchy

The decision engine evaluates evidence in a fixed order:

1. SRM failure
2. Underpowered experiment
3. Inconclusive result
4. Confidently null result
5. Significant negative effect
6. Positive effect with guardrail breach
7. Positive effect with clean guardrails
        """
    )


# ============================================================
# EXPLORATORY SEGMENT ANALYSIS
#
# This is where Scenario 3's segment-level signal is surfaced.
# Segment analysis is exploratory by design: it never feeds the
# decision engine, so a segment finding should become its own
# follow-up investigation rather than silently overriding the verdict.
# ============================================================

def calculate_segment_ssr(
    analysis_result,
    users_df,
    segment_column,
):
    """
    Calculate user-level SSR by segment and experiment variant.

    This is exploratory analysis only.
    Segment results do NOT feed the decision engine.
    """

    user_level_ssr = analysis_result["user_level_ssr"].copy()

    required_user_columns = [
        "user_id",
        segment_column,
    ]

    missing_columns = [
        column
        for column in required_user_columns
        if column not in users_df.columns
    ]

    if missing_columns:
        return None

    segment_users = users_df[
        required_user_columns
    ].drop_duplicates("user_id")

    segment_data = user_level_ssr.merge(
        segment_users,
        on="user_id",
        how="inner",
    )

    if segment_data.empty:
        return None

    result = (
        segment_data
        .groupby(
            [segment_column, "variant"],
            as_index=False,
        )
        .agg(
            users=("user_id", "nunique"),
            # Source column is "rate" from statistical_analysis.py's
            # _user_level_proportion output. It is named "ssr" here
            # for the pivot/output columns below.
            ssr=("rate", "mean"),
        )
    )

    pivot = result.pivot(
        index=segment_column,
        columns="variant",
        values="ssr",
    ).reset_index()

    pivot.columns.name = None

    if "Control" not in pivot.columns:
        pivot["Control"] = pd.NA

    if "Treatment" not in pivot.columns:
        pivot["Treatment"] = pd.NA

    pivot["Lift (pp)"] = (
        pivot["Treatment"] - pivot["Control"]
    ) * 100

    control_users = (
        result[result["variant"] == "Control"]
        .groupby(segment_column)["users"]
        .sum()
        .rename("Control users")
    )

    treatment_users = (
        result[result["variant"] == "Treatment"]
        .groupby(segment_column)["users"]
        .sum()
        .rename("Treatment users")
    )

    pivot = pivot.merge(
        control_users,
        on=segment_column,
        how="left",
    )

    pivot = pivot.merge(
        treatment_users,
        on=segment_column,
        how="left",
    )

    output = pivot[
        [
            segment_column,
            "Control users",
            "Treatment users",
            "Control",
            "Treatment",
            "Lift (pp)",
        ]
    ].copy()

    output["Control"] = (
        output["Control"] * 100
    ).round(2)

    output["Treatment"] = (
        output["Treatment"] * 100
    ).round(2)

    output["Lift (pp)"] = output["Lift (pp)"].round(2)

    return output


with st.expander(
    "Segment breakdown (exploratory — not used in the ship decision)",
    expanded=False,
):

    st.info(
        "Segment analysis is exploratory only. "
        "It does not change the final SHIP / DON'T SHIP decision."
    )

    segment_choice = st.radio(
        "View SSR by:",
        options=[
            "Device type",
            "Activity level",
        ],
        horizontal=True,
    )

    segment_column_map = {
        "Device type": "device_type",
        # Phase 2 schema calls this column "activity_level" -- keep
        # this mapping in sync with users_prototype.csv's real column
        # names, or this silently falls into the "not found" warning.
        "Activity level": "activity_level",
    }

    selected_segment_column = segment_column_map[
        segment_choice
    ]

    segment_table = calculate_segment_ssr(
        analysis_result=analysis,
        users_df=users,
        segment_column=selected_segment_column,
    )

    if segment_table is None:
        st.warning(
            f"Required user-level fields for "
            f"'{segment_choice}' were not found."
        )

    elif segment_table.empty:
        st.info(
            "No segment-level observations are available "
            "for this experiment."
        )

    else:
        display_table = segment_table.rename(
            columns={
                selected_segment_column: segment_choice,
                "Control": "Control SSR",
                "Treatment": "Treatment SSR",
            }
        )

        st.dataframe(
            display_table,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Control/Treatment SSR and lift are calculated from "
            "user-level SSR within each segment. "
            "Small segment-level differences should be treated "
            "as exploratory rather than confirmatory evidence."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "PRYVIA · Search-ranking experimentation · "
    "Decision engine uses predefined statistical rules."
)