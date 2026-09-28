"""
PRYVIA Decision Engine

Takes the evidence dict from statistical_analysis.run_statistical_analysis()
and returns a verdict PLUS every piece of explanation text the UI needs.

Design rule: app.py should contain ZERO knowledge of what each rule means,
what colour it should be, or what sentence explains it.

All decision logic and explanation text lives here in one place so that
the decision framework stays consistent across the application.
"""


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

ALPHA = 0.05


# -------------------------------------------------------------------
# Decision-rule metadata
# -------------------------------------------------------------------

# Severity drives badge colour in the UI:
# negative -> red
# caution  -> amber
# neutral  -> gray
# positive -> green
#
# Rule 4 and Rule 5 are both DON'T SHIP decisions, but represent
# different findings:
# - Rule 4 = confidently null
# - Rule 5 = significant negative effect

RULES = {
    1: {
        "verdict": "INVESTIGATE",
        "label": "Randomization failure",
        "severity": "negative",
    },
    2: {
        "verdict": "RUN FOLLOW-UP",
        "label": "Underpowered",
        "severity": "caution",
    },
    3: {
        "verdict": "RUN FOLLOW-UP",
        "label": "Inconclusive",
        "severity": "caution",
    },
    4: {
        "verdict": "DON'T SHIP",
        "label": "Confidently null",
        "severity": "neutral",
    },
    5: {
        "verdict": "DON'T SHIP",
        "label": "Significant regression",
        "severity": "negative",
    },
    6: {
        "verdict": "SHIP WITH CAUTION",
        "label": "Guardrail breach",
        "severity": "caution",
    },
    7: {
        "verdict": "SHIP",
        "label": "Clean win",
        "severity": "positive",
    },
}


# -------------------------------------------------------------------
# Rule table used by the Streamlit UI
# -------------------------------------------------------------------

RULE_TABLE_FOR_DISPLAY = [
    (1, "SRM failed", "INVESTIGATE"),
    (2, "Actual users < required sample size", "RUN FOLLOW-UP"),
    (3, "Not significant + CI wider than MDE", "RUN FOLLOW-UP"),
    (4, "Not significant + entire CI within ±MDE", "DON'T SHIP"),
    (5, "Significant + negative SSR effect", "DON'T SHIP"),
    (6, "Significant + positive effect + guardrail breach", "SHIP WITH CAUTION"),
    (7, "Significant + positive effect + clean guardrails", "SHIP"),
]


# -------------------------------------------------------------------
# Determine which decision rule applies
# -------------------------------------------------------------------

def _which_rule(analysis):
    """
    Apply PRYVIA's decision framework in priority order.

    The first matching rule wins.
    """

    srm = analysis["srm"]
    power = analysis["power"]
    ssr = analysis["ssr"]

    # Rule 1: SRM failure
    if not srm["passed"]:
        return 1

    # Rule 2: insufficient sample size
    if not power["adequate"]:
        return 2

    # Values needed for Rules 3-7
    mde = power["mde_pp"]
    ci_lower = ssr["ci_lower_pp"]
    ci_upper = ssr["ci_upper_pp"]

    # Non-significant result
    if not ssr["significant"]:

        # Rule 4: confidently null
        confidently_null = (
            ci_lower >= -mde
            and ci_upper <= mde
        )

        if confidently_null:
            return 4

        # Rule 3: inconclusive
        return 3

    # Significant result from this point onward

    # Rule 5: statistically significant negative effect
    if not ssr["positive"]:
        return 5

    # Rules 6 and 7: statistically significant positive effect
    if not analysis["guardrails_healthy"]:
        return 6

    return 7


# -------------------------------------------------------------------
# Build explanation text for the selected rule
# -------------------------------------------------------------------

def _build_explanation(rule, analysis):

    ssr = analysis["ssr"]
    power = analysis["power"]

    lift = ssr["lift_pp"]
    ci_lower = ssr["ci_lower_pp"]
    ci_upper = ssr["ci_upper_pp"]
    mde = power["mde_pp"]

    # ---------------------------------------------------------------
    # Rule 1 — INVESTIGATE
    # ---------------------------------------------------------------

    if rule == 1:

        reason = (
            "Randomization health failed. "
            "The evidence below cannot be trusted until this is fixed."
        )

        bullets = [
            "The sample ratio mismatch (SRM) check failed.",
            (
                f"SRM p-value = {analysis['srm']['p_value']:.4f} "
                "(threshold: p ≥ 0.01 to pass)."
            ),
            (
                "Because randomization may be broken, "
                "downstream metrics are not reliable."
            ),
        ]

        markdown = (
            "**Why INVESTIGATE?**\n\n"
            "The sample ratio mismatch check failed. Because randomization "
            "may have been compromised, downstream experiment evidence "
            "should not be trusted until the assignment mechanism is fixed.\n\n"
            "**Decision: INVESTIGATE — Rule 1.**"
        )

    # ---------------------------------------------------------------
    # Rule 2 — RUN FOLLOW-UP
    # ---------------------------------------------------------------

    elif rule == 2:

        reason = (
            f"Underpowered for the planned ±{mde:.1f} pp MDE."
        )

        bullets = [
            (
                f"{power['actual_users']:,} users observed vs "
                f"{power['required_total']:,} required."
            ),
            (
                f"Planned minimum detectable effect: ±{mde:.1f} pp."
            ),
            (
                "A null or inconclusive result here can't be trusted -- "
                "there weren't enough users to detect the effect size "
                "that was planned for."
            ),
        ]

        markdown = (
            "**Why RUN FOLLOW-UP?**\n\n"
            f"The experiment contains **{power['actual_users']:,} users**, "
            f"while approximately **{power['required_total']:,} users** "
            f"are required for the planned **±{mde:.1f} pp MDE**.\n\n"
            "**Decision: RUN FOLLOW-UP — Rule 2.**"
        )

    # ---------------------------------------------------------------
    # Rule 3 — RUN FOLLOW-UP
    # ---------------------------------------------------------------

    elif rule == 3:

        reason = (
            "Not significant, and the confidence interval is too wide "
            "to rule out a meaningful effect."
        )

        bullets = [
            "Experiment passed SRM and power checks.",
            (
                f"SSR effect: {lift:+.2f} pp, "
                f"p = {ssr['p_value']:.4f} (not significant)."
            ),
            (
                f"95% CI [{ci_lower:+.2f}, {ci_upper:+.2f}] pp "
                f"extends beyond the ±{mde:.1f} pp MDE."
            ),
        ]

        markdown = (
            "**Why RUN FOLLOW-UP?**\n\n"
            "The SSR result is not statistically significant, but the "
            "95% confidence interval is too wide to confidently rule out "
            "a practically meaningful effect.\n\n"
            f"Observed effect: **{lift:+.2f} pp**\n\n"
            f"95% CI: **[{ci_lower:+.2f}, {ci_upper:+.2f}] pp**\n\n"
            "**Decision: RUN FOLLOW-UP — Rule 3.**"
        )

    # ---------------------------------------------------------------
    # Rule 4 — DON'T SHIP
    # ---------------------------------------------------------------

    elif rule == 4:

        reason = (
            f"SSR effect was {lift:+.2f} pp; entire CI sits inside "
            f"the ±{mde:.1f} pp MDE."
        )

        bullets = [
            "Experiment passed SRM and power checks.",
            f"SSR effect was {lift:+.2f} pp.",
            (
                f"p-value = {ssr['p_value']:.4f} "
                "→ not statistically significant."
            ),
            (
                f"CI [{ci_lower:+.2f}, {ci_upper:+.2f}] pp remains "
                f"inside the ±{mde:.1f} pp MDE."
            ),
        ]

        markdown = (
            "**Why DON'T SHIP?**\n\n"
            "The experiment passed the SRM check and is adequately powered.\n\n"
            f"Treatment SSR is **{ssr['treatment_rate']:.2%}** versus "
            f"**{ssr['control_rate']:.2%}** for Control. "
            f"The observed treatment effect is **{lift:+.2f} pp**, "
            f"with a 95% confidence interval of "
            f"**[{ci_lower:+.2f}, {ci_upper:+.2f}] pp**.\n\n"
            "Because the entire confidence interval lies inside the planned "
            f"**±{mde:.1f} pp MDE**, the experiment provides evidence that "
            "there is no practically meaningful SSR improvement -- "
            "a clean, informative null result, not a failed experiment.\n\n"
            "**Decision: DON'T SHIP — Rule 4.**"
        )

    # ---------------------------------------------------------------
    # Rule 5 — DON'T SHIP
    # ---------------------------------------------------------------

    elif rule == 5:

        reason = (
            f"SSR decreased by {abs(lift):.2f} pp, "
            "and the effect is statistically significant."
        )

        bullets = [
            f"SSR decreased by {abs(lift):.2f} pp.",
            (
                f"p-value = {ssr['p_value']:.4f} "
                "→ statistically significant."
            ),
            (
                "Treatment produced a statistically significant "
                "decrease in the primary outcome."
            ),
        ]

        markdown = (
            "**Why DON'T SHIP?**\n\n"
            f"Treatment reduced SSR by **{abs(lift):.2f} pp**, "
            "and the effect is statistically significant. "
            "Treatment therefore performed worse on the primary "
            "SSR metric.\n\n"
            "**Decision: DON'T SHIP — Rule 5.**"
        )

    # ---------------------------------------------------------------
    # Rule 6 — SHIP WITH CAUTION
    # ---------------------------------------------------------------

    elif rule == 6:

        reason = (
            f"SSR improved {lift:+.2f} pp, "
            "but a technical guardrail breached."
        )

        bullets = [
            (
                f"SSR improved by {lift:+.2f} pp "
                f"(p = {ssr['p_value']:.4f}, significant)."
            ),
            (
                "At least one technical guardrail "
                "(error rate or latency) breached."
            ),
            (
                "Rollout requires caution -- fix the guardrail "
                "regression before shipping broadly."
            ),
        ]

        markdown = (
            "**Why SHIP WITH CAUTION?**\n\n"
            f"Treatment improved SSR by **{lift:+.2f} pp**, "
            "but at least one technical guardrail breached. "
            "The product impact therefore requires caution before "
            "a full rollout.\n\n"
            "**Decision: SHIP WITH CAUTION — Rule 6.**"
        )

    # ---------------------------------------------------------------
    # Rule 7 — SHIP
    # ---------------------------------------------------------------

    else:

        reason = (
            f"SSR improved {lift:+.2f} pp, statistically significant, "
            "guardrails clean."
        )

        bullets = [
            (
                f"SSR improved by {lift:+.2f} pp "
                f"(p = {ssr['p_value']:.4f}, significant)."
            ),
            "Both technical guardrails (error rate, latency) are healthy.",
            "No evidence of harm elsewhere in the funnel.",
        ]

        markdown = (
            "**Why SHIP?**\n\n"
            f"Treatment improved SSR by **{lift:+.2f} pp**, "
            "the effect is statistically significant, and both "
            "technical guardrails are healthy.\n\n"
            "**Decision: SHIP — Rule 7.**"
        )

    return reason, bullets, markdown


# -------------------------------------------------------------------
# Public decision-engine function
# -------------------------------------------------------------------

def evaluate_experiment(analysis):
    """
    Evaluate an experiment using PRYVIA's decision framework.

    Parameters
    ----------
    analysis : dict
        Full evidence dictionary returned by
        statistical_analysis.run_statistical_analysis().

    Returns
    -------
    dict
        Structured decision output containing:

        verdict
        rule_triggered
        rule_label
        severity
        reason
        explanation_bullets
        explanation_markdown
    """

    rule = _which_rule(analysis)

    meta = RULES[rule]

    reason, bullets, markdown = _build_explanation(
        rule,
        analysis,
    )

    return {
        "verdict": meta["verdict"],
        "rule_triggered": rule,
        "rule_label": meta["label"],
        "severity": meta["severity"],
        "reason": reason,
        "explanation_bullets": bullets,
        "explanation_markdown": markdown,
    }