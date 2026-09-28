# PRYVIA Methodology

## 1. Purpose

PRYVIA is a simulated product-analytics platform for evaluating
search-ranking A/B experiments.

The experiment compares a **Control** search-ranking experience with a
**Treatment** experience and evaluates whether Treatment improves
**Successful Search Rate (SSR)** without introducing statistically
significant deterioration in technical guardrails.

The workflow is:

`user assignment → search behavior → ranking → clicks → dwell → reformulation → search success → statistical analysis → decision engine`

The data is synthetic and behavior-first. It demonstrates
experimentation methodology and analytical reasoning; it is not
production customer data.

## 2. Experiment Design

### Randomization unit

The randomization unit is the **user**. Each user is assigned to exactly
one variant:

-   Control
-   Treatment

Assignment is sticky throughout the experiment.

### Allocation

The planned allocation is **50/50 Control vs Treatment**. PRYVIA checks
this with a Sample Ratio Mismatch (SRM) test.

### Why user-level randomization matters

A user can perform multiple searches, so those searches are correlated.
Treating every search as an independent observation would understate
uncertainty.

PRYVIA therefore performs statistical inference at the **user level**.

## 3. Primary Metric --- Successful Search Rate

CTR alone does not establish that a search was successful. PRYVIA
therefore uses **Successful Search Rate (SSR)** as its primary metric.

### Quality click

A search contains a quality click when:

1.  A result was clicked.
2.  The clicked result received at least **30 seconds of dwell time**.

``` text
quality_click =
    clicked = TRUE
    AND dwell_time_seconds >= 30
```

### Successful search

``` text
successful_search =
    quality_click = TRUE
    AND is_reformulation = FALSE
```

### SSR

At the descriptive search level:

``` text
SSR = successful searches / total searches
```

For statistical inference, PRYVIA first calculates one SSR value per
user:

``` text
user SSR =
    successful searches for user
    / total searches for user
```

Treatment and Control are then compared using these user-level values.

## 4. Reformulation

A reformulation represents continued searching after a previous search
within the same session.

PRYVIA uses a **300-second (5-minute)** window:

> If another search occurs within the same session within 300 seconds of
> the previous search, the later search is classified as a
> reformulation.

Reformulation is used in the SSR definition and reported as a secondary
diagnostic.

## 5. Statistical Unit of Analysis

The experiment randomizes users, so repeated searches from the same user
are correlated.

The analysis therefore follows:

``` text
Search-level behavior
        ↓
Aggregate to one row per user
        ↓
Compare randomized users
        ↓
Statistical inference
```

This applies to:

-   Successful Search Rate
-   Search Error Rate
-   Click-through Rate
-   Reformulation Rate

Latency is also summarized per user before comparison.

## 6. Sample Ratio Mismatch

SRM checks whether the observed Control/Treatment allocation is
consistent with the planned **50/50** randomization.

PRYVIA uses a **chi-square goodness-of-fit test**.

The SRM check passes when:

``` text
p >= 0.01
```

and fails when:

``` text
p < 0.01
```

A failed SRM check triggers **INVESTIGATE** because experiment
assignment integrity must be resolved before downstream evidence is
trusted.

## 7. Statistical Power and Sample Size

The current experiment design uses:

-   Baseline SSR: **65%**
-   Minimum Detectable Effect (MDE): **±5 percentage points**
-   Target statistical power: **80%**
-   Significance level: **α = 0.05**

Sample size is planned using a two-group proportion effect-size
calculation.

The MDE is a planning threshold: it represents the effect size the
experiment was designed to detect with the target power. It is not a
universal definition of business importance.

PRYVIA uses the MDE together with the confidence interval to distinguish
an inconclusive result from a result precise enough to rule out a
practically meaningful effect.

## 8. Primary Metric Hypothesis Test

The primary test compares user-level SSR between Treatment and Control.

**H0:** Treatment and Control have the same mean user-level SSR.

**H1:** Treatment and Control have different mean user-level SSR.

The test is two-sided and uses **Welch's independent-samples t-test**.

Significance level:

``` text
α = 0.05
```

A p-value below 0.05 is treated as statistically significant.

## 9. Confidence Interval

PRYVIA reports a **95% confidence interval** for:

``` text
Treatment SSR − Control SSR
```

The interval is generated using **10,000 bootstrap resamples** at the
user level, with a fixed seed for reproducibility.

Effects are reported in percentage points.

Example:

``` text
Observed lift: +4.57 pp
95% CI: [+2.80 pp, +6.36 pp]
```

## 10. Effect Size

The primary effect is the absolute percentage-point difference:

``` text
SSR lift (pp) =
    Treatment SSR − Control SSR
```

A relative lift can also be calculated:

``` text
Relative lift =
    (Treatment SSR − Control SSR)
    / Control SSR
```

The decision engine primarily uses the absolute effect and its
relationship to the predefined MDE.

## 11. Technical Guardrails

PRYVIA evaluates two technical guardrails:

### Search Error Rate

Search error rate is calculated per user and compared between variants.

The guardrail is unhealthy when Treatment produces a statistically
significant deterioration in error rate.

### Search Latency

Latency is measured using `search_latency_ms`.

For each user, PRYVIA calculates the user's median search latency.
Treatment and Control user-level medians are compared with a **two-sided
Mann-Whitney U test**.

The latency guardrail is unhealthy when Treatment produces a
statistically significant increase in latency.

**Important:** The Power BI dashboard contains a **500 ms latency
reference line** for visual interpretation. This is a dashboard
reference and is not the statistical guardrail rule used by the decision
engine.

## 12. Secondary Metrics

Secondary metrics provide behavioral context but do not independently
determine the ship decision.

### Click-through Rate

A search is counted as clicked when at least one result was clicked. CTR
is then aggregated to the user level for statistical comparison.

### Reformulation Rate

Reformulation rate measures the proportion of searches classified as
reformulations. It is a diagnostic signal rather than a technical
guardrail.

## 13. Decision Framework

The decision engine evaluates rules in priority order. The **first
matching rule determines the verdict**.

  ------------------------------------------------------------------------
                      Priority Condition             Decision
  ---------------------------- --------------------- ---------------------
                             1 SRM failed            INVESTIGATE

                             2 Actual users below    RUN FOLLOW-UP
                               required sample size  

                             3 Not significant and   RUN FOLLOW-UP
                               CI wider than MDE     

                             4 Not significant and   DON'T SHIP
                               entire CI lies within 
                               ±MDE                  

                             5 Significant and SSR   DON'T SHIP
                               effect is negative    

                             6 Significant positive  SHIP WITH CAUTION
                               SSR effect with a     
                               guardrail breach      

                             7 Significant positive  SHIP
                               SSR effect with clean 
                               guardrails            
  ------------------------------------------------------------------------

### Rule 1 --- INVESTIGATE

A failed SRM check takes priority over downstream metrics.

### Rule 2 --- RUN FOLLOW-UP

If observed users are below the required sample size, the experiment is
underpowered for the planned MDE.

### Rule 3 --- RUN FOLLOW-UP

If the SSR result is not significant and the confidence interval extends
beyond ±MDE, the experiment is too imprecise to rule out a practically
meaningful effect.

### Rule 4 --- DON'T SHIP

If the result is not significant and the entire 95% confidence interval
lies within ±MDE, the result is considered **confidently null** relative
to the predefined MDE.

### Rule 5 --- DON'T SHIP

A statistically significant negative SSR effect means Treatment
performed worse on the primary outcome.

### Rule 6 --- SHIP WITH CAUTION

A statistically significant positive SSR effect combined with a
technical guardrail breach does not receive a clean ship decision.

### Rule 7 --- SHIP

A statistically significant positive SSR effect with healthy technical
guardrails produces a clean SHIP verdict.

## 14. Exploratory Segmentation

PRYVIA includes exploratory analysis for:

-   Device type
-   Activity level
-   Query category

These results **do not feed the decision engine**.

A segment-level signal is therefore treated as a hypothesis for
follow-up investigation rather than as an override of the
experiment-level verdict.

## 15. Descriptive vs Inferential Analysis

The SQL layer is primarily descriptive. It answers questions such as:

-   How many users are in each variant?
-   How many searches occurred?
-   What is observed SSR?
-   What is observed CTR?
-   How often do users reformulate?
-   How do metrics vary by segment?

The Python statistical layer handles:

-   SRM
-   Sample-size planning
-   Achieved power
-   User-level hypothesis testing
-   Confidence intervals
-   Effect size
-   Guardrail evaluation
-   Decision-engine evidence

This separation keeps descriptive SQL transparent while ensuring
inference respects the randomization unit.

## 16. Reproducibility

Key analysis settings are fixed:

``` text
α = 0.05
Target power = 0.80
Baseline SSR = 0.65
MDE = ±5 pp
Bootstrap iterations = 10,000
Bootstrap seed = 42
SRM pass threshold = p >= 0.01
```

The decision engine contains no data loading or statistical
calculations. It receives the analysis result and applies the fixed
decision hierarchy.

## 17. Interpretation Boundaries

PRYVIA is a **simulated experimentation platform**. Its data is
intentionally generated to create distinct experiment scenarios,
including a clear positive result, an underpowered experiment, a
segment-level signal, and a positive result with a technical guardrail
issue.

The outcomes should therefore be presented as demonstrations of
experimentation methodology, not as real customer findings.

The core portfolio claim is:

> PRYVIA demonstrates how to move from user-level A/B randomization and
> behavioral event data to statistically rigorous experiment evidence
> and a deterministic product decision.
