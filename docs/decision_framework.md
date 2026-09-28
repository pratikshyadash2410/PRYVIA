# PRYVIA Decision Framework

## Purpose

The PRYVIA decision engine converts statistical experiment evidence into a deterministic experiment verdict.

It does **not** calculate metrics or load data. The statistical analysis layer produces the evidence; the decision engine evaluates that evidence in a fixed priority order.

```text
Raw experiment data
        ↓
statistical_analysis.py
        ↓
Analysis evidence
        ↓
decision_engine.py
        ↓
Final verdict
```

The first rule that matches determines the verdict.

---

## Decision Inputs

The decision engine uses:

- Sample Ratio Mismatch (SRM) result
- Actual vs required user count
- Statistical power
- SSR treatment effect
- SSR p-value / significance
- 95% confidence interval
- Predefined MDE
- Technical guardrail health

The exploratory segment analysis is intentionally excluded from the decision inputs.

---

## Rule Priority

| Priority | Condition | Verdict |
|---:|---|---|
| 1 | SRM failed | INVESTIGATE |
| 2 | Actual users < required sample size | RUN FOLLOW-UP |
| 3 | Not significant + CI wider than MDE | RUN FOLLOW-UP |
| 4 | Not significant + entire CI within ±MDE | DON'T SHIP |
| 5 | Significant + negative SSR effect | DON'T SHIP |
| 6 | Significant + positive SSR effect + guardrail breach | SHIP WITH CAUTION |
| 7 | Significant + positive SSR effect + clean guardrails | SHIP |

Rules are evaluated from 1 through 7. The first matching rule wins.

---

## Rule 1 — INVESTIGATE

### Trigger

```text
SRM failed
```

PRYVIA treats randomization integrity as the first check.

If the observed allocation is inconsistent with the planned allocation, downstream experiment evidence should not be trusted until the assignment issue is investigated.

### Verdict

```text
INVESTIGATE
```

### Why this rule has the highest priority

A statistically significant metric result cannot rescue an experiment whose randomization integrity is questionable.

---

## Rule 2 — RUN FOLLOW-UP

### Trigger

```text
Actual users < required sample size
```

The experiment is underpowered for the predefined MDE.

PRYVIA currently uses:

```text
Baseline SSR = 65%
MDE = ±5 pp
Target power = 80%
Alpha = 0.05
```

The required sample size is calculated before interpreting the result.

### Verdict

```text
RUN FOLLOW-UP
```

### Interpretation

The experiment needs additional users before an inconclusive result can be interpreted with the planned level of precision.

---

## Rule 3 — RUN FOLLOW-UP

### Trigger

The experiment has adequate sample size, but:

```text
SSR is not statistically significant
AND
95% CI extends beyond ±MDE
```

### Verdict

```text
RUN FOLLOW-UP
```

### Interpretation

The experiment is sufficiently sized, but the confidence interval is still too wide to rule out a practically meaningful effect.

This is different from proving that Treatment has no effect.

---

## Rule 4 — DON'T SHIP

### Trigger

```text
SSR is not statistically significant
AND
entire 95% CI lies within ±MDE
```

PRYVIA calls this a **confidently null** result relative to the predefined MDE.

### Verdict

```text
DON'T SHIP
```

### Interpretation

The observed evidence is precise enough that the experiment does not support an effect as large as the predefined MDE in either direction.

---

## Rule 5 — DON'T SHIP

### Trigger

```text
SSR is statistically significant
AND
Treatment SSR < Control SSR
```

### Verdict

```text
DON'T SHIP
```

### Interpretation

Treatment produced a statistically significant decrease in the primary outcome.

---

## Rule 6 — SHIP WITH CAUTION

### Trigger

```text
SSR is statistically significant
AND
Treatment SSR > Control SSR
AND
technical guardrail breach
```

Technical guardrails are:

- Search Error Rate
- Search Latency

### Verdict

```text
SHIP WITH CAUTION
```

### Interpretation

The primary metric improved, but at least one technical guardrail deteriorated enough to require caution.

---

## Rule 7 — SHIP

### Trigger

```text
SRM passed
AND
sample size is adequate
AND
SSR is statistically significant
AND
Treatment SSR > Control SSR
AND
technical guardrails are healthy
```

### Verdict

```text
SHIP
```

This is the clean positive path through the decision engine.

---

## Why the Order Matters

The rules are deliberately hierarchical.

For example, suppose an experiment has:

```text
Positive SSR lift
Statistically significant
Guardrail breach
Underpowered
```

It does **not** reach Rule 6 because Rule 2 is evaluated first.

Likewise, if SRM fails, the engine stops at Rule 1 rather than allowing a strong SSR result to produce a ship decision.

This prevents downstream evidence from overriding a higher-priority experiment-health issue.

---

## Four PRYVIA Scenarios

The frozen PRYVIA dataset intentionally contains four different experiment situations.

| Experiment | Scenario | Observed SSR effect | Statistical status | Guardrails | Verdict |
|---:|---|---:|---|---|---|
| 1 | Clear winner | +4.57 pp | Significant | Healthy | SHIP |
| 2 | Inconclusive / underpowered | +2.16 pp | Not significant | Healthy | RUN FOLLOW-UP |
| 3 | Segment signal | +2.19 pp | Significant | Healthy | SHIP |
| 4 | Guardrail violation | +2.41 pp | Significant | Breach | SHIP WITH CAUTION |

### Experiment 1

The experiment has adequate sample size, a statistically significant positive SSR effect, and healthy technical guardrails.

```text
Rule 7 → SHIP
```

### Experiment 2

The observed effect is positive, but only 1,000 users are available against approximately 2,752 required for the planned MDE.

```text
Rule 2 → RUN FOLLOW-UP
```

The underpowered rule takes priority over the inconclusive metric result.

### Experiment 3

The overall experiment has a statistically significant positive SSR effect and healthy guardrails.

The segment analysis identifies additional behavioral differences, but those findings do not alter the experiment-level decision.

```text
Rule 7 → SHIP
```

### Experiment 4

The experiment has a statistically significant positive SSR effect, but Treatment also increases median latency substantially.

```text
Rule 6 → SHIP WITH CAUTION
```

The positive primary metric therefore does not receive a clean ship verdict.

---

## Decision Engine Architecture

The decision engine is intentionally separated from the statistical analysis layer.

### `src/statistical_analysis.py`

Responsible for:

- SRM
- Power
- SSR
- Confidence interval
- Effect size
- Error rate
- Latency
- CTR
- Reformulation
- Guardrail health

### `src/decision_engine.py`

Responsible only for:

- Selecting the first matching rule
- Producing the verdict
- Producing the rule label
- Producing the explanation
- Producing structured decision output

### `app/app.py`

Responsible for presentation:

- Experiment selection
- Verdict display
- Evidence display
- Charts
- Tables
- Methodology
- Exploratory segmentation

The Streamlit app does not contain independent decision logic.

---

## Structured Decision Output

The decision engine returns a structured object containing:

```python
{
    "verdict": "...",
    "rule_triggered": 7,
    "rule_label": "...",
    "severity": "...",
    "reason": "...",
    "explanation_bullets": [...],
    "explanation_markdown": "..."
}
```

This allows the same decision result to be consumed by the Streamlit UI, tests, CSV exports, or future reporting without duplicating decision logic.

---

## What Does Not Affect the Verdict

The following are intentionally excluded from the ship decision:

- Device-level segment results
- Activity-level segment results
- Query-category segment results
- CTR
- Reformulation rate

These metrics provide context and can identify follow-up questions, but they do not override the primary decision framework.

---

## Testing the Decision Engine

The decision engine is covered by a regression test that verifies the expected rule and verdict for all four frozen scenarios.

Expected outputs:

```text
Experiment 1 → Rule 7 → SHIP
Experiment 2 → Rule 2 → RUN FOLLOW-UP
Experiment 3 → Rule 7 → SHIP
Experiment 4 → Rule 6 → SHIP WITH CAUTION
```

This protects the decision hierarchy from accidental changes during future refactoring.

---

## Design Principle

PRYVIA deliberately separates:

```text
Evidence
   ↓
Interpretation
   ↓
Decision
```

The statistical layer answers:

> **What does the experiment evidence show?**

The decision engine answers:

> **Given the predefined rules, what verdict follows from that evidence?**

The Streamlit layer answers:

> **How should that evidence and verdict be presented clearly to a product stakeholder?**

This separation makes the project easier to test, explain, and maintain.
