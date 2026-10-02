PRYVIA

Search-Ranking A/B Experimentation & Decision Engine

PRYVIA is a simulated product-analytics platform for evaluating search-ranking experiments. It combines behavior-first data simulation, PostgreSQL analysis, user-level statistical inference, guardrail monitoring, and a rule-based experiment decision engine.

Core question: Did the new search-ranking experience improve search success enough to justify shipping it?

Stack: Python · PostgreSQL · SQL · Streamlit · Power BI

Executive Overview

PRYVIA evaluates search-ranking experiments using Successful Search Rate (SSR) instead of relying on CTR alone.

The project covers the complete experimentation workflow:

Behavior-first synthetic data generation

User-level A/B assignment

Search-quality and SSR measurement

SQL-based descriptive analysis

SRM and statistical analysis

Confidence intervals and effect size

Latency and error guardrails

Rule-based ship / follow-up decisions

Streamlit decision interface

Power BI reporting

Core Methodology

Successful Search Rate (SSR)

SSR = Successful searches / Total searches

A search is successful when:

A result is clicked

The clicked result has at least 30 seconds dwell time

The search is not classified as a reformulation

Reformulation

A search is classified as a reformulation when the same user issues another search within 300 seconds (5 minutes) in the same session.

Reformulation is also used as a behavioral diagnostic. For SSR, a search is successful only when it has a quality click and is not classified as a reformulation.

Experiment Design

Randomization unit: User

Assignment: Sticky user-level assignment

Allocation target: 50/50 Control vs Treatment

Baseline SSR for power planning: 65%

MDE: ±5 percentage points

Power: 80%

Significance level: α = 0.05

Planned sample size: ~2,752 users total

SRM threshold: p < 0.01 = fail

Statistical Inference

Because users can generate multiple searches, inference is performed at the user level rather than treating every search as an independent observation.

User-level SSR aggregation

Welch's t-test for treatment effect

95% bootstrap confidence interval

10,000 bootstrap resamples

Fixed random seed for reproducibility

Guardrails: search error rate and latency
Secondary diagnostics: CTR and reformulation rate

Decision Framework

The decision engine evaluates rules in order:

Rule

Condition

Decision

1

SRM failed

INVESTIGATE

2

Actual users < required sample

RUN FOLLOW-UP

3

Not significant + CI wider than MDE

RUN FOLLOW-UP

4

Not significant + entire CI within ±MDE

DON'T SHIP

5

Significant + negative SSR effect

DON'T SHIP

6

Significant + positive effect + guardrail breach

SHIP WITH CAUTION

7

Significant + positive effect + clean guardrails

SHIP

This makes the final decision deterministic and explainable rather than based on a single p-value.

Frozen Experiment Results

Experiment

Scenario

Control SSR

Treatment SSR

Lift

p-value

Guardrails

Decision

Exp 1

Clear winner

66.29%

70.87%

+4.57 pp

<0.001

Healthy

SHIP

Exp 2

Inconclusive / underpowered

67.29%

69.45%

+2.16 pp

0.159

Healthy

RUN FOLLOW-UP

Exp 3

Segment signal

66.65%

68.85%

+2.19 pp

0.017

Healthy

SHIP

Exp 4

Guardrail violation

66.61%

69.02%

+2.41 pp

0.008

Latency breach

SHIP WITH CAUTION

Exp 2 intentionally exposes only 1,000 users, making it underpowered for the planned sample size.

Exp 4 increases treatment median latency by approximately 90 ms versus Control.

Architecture

Synthetic User Behaviour
        ↓
Python Data Generator
        ↓
PostgreSQL
        ↓
SQL Analysis
        ↓
Python Statistical Analysis
        ↓
Decision Engine
        ↓
Streamlit Decision App
        ↓
Power BI Dashboard

Data Model

PRYVIA uses seven core PostgreSQL tables:

users
experiments
experiment_assignments
search_sessions
searches
search_results
business_events

The main relationships follow:

users
  ↓
experiment_assignments
  ↓
search_sessions
  ↓
searches
  ↓
search_results
  ↓
business_events

Dataset

The frozen dataset contains:

Entity

Rows

Users

12,000

Experiment assignments

10,000

Search sessions

27,863

Searches

44,657

Search results

223,285

Business events

121,659

Every search returns 5 results.

Overall descriptive SSR across the frozen dataset: 63.45%.

Project Structure

PRYVIA/
├── app/
│   └── app.py
├── docs/
│   ├── data_dictionary.md
│   ├── decision_framework.md
│   └── methodology.md
├── powerbi/
│   └── screenshots/
├── sql/
│   ├── analysis.sql
│   ├── indexes.sql
│   ├── schema.sql
│   └── vw_search_success.sql
├── src/
│   ├── calculate_success.py
│   ├── decision_engine.py
│   ├── detect_reformulation.py
│   ├── generate_experiment_scenarios.py
│   ├── generate_experiment_verdicts.py
│   ├── statistical_analysis.py
│   └── validation scripts
├── tests/
│   ├── test_decision_engine.py
│   └── test_statistical_analysis.py
├── .gitignore
├── .gitattributes
├── LICENSE
├── pytest.ini
├── requirements.txt
└── README.md

Quick Start

1. Clone

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PRYVIA

2. Create environment

python -m venv .venv

Windows:

.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Run the Streamlit app

streamlit run app/app.py

The app uses the frozen CSV outputs for reproducible analysis.

SQL & Python Analysis

SQL handles descriptive and analytical work:

Joins and CTEs

Search-level SSR

CTR

Reformulation

Dwell time

Error rate

Latency

Session and cohort analysis

Window functions

Python handles statistical inference:

SRM testing

Power and sample-size analysis

User-level hypothesis testing

Confidence intervals

Effect size

Guardrail evaluation

Decision logic

This separation keeps descriptive analytics and statistical inference explicit.

Power BI

The dashboard contains three pages:

Experiment Portfolio — experiment-level decisions and key evidence

Core Metrics — SSR, error rate, and latency

Segmentation & Exploration — device, activity, and query-category analysis

Segment results are exploratory and are not used by the decision engine.

Testing

The project includes automated tests for:

Decision-engine rule selection

Statistical-analysis outputs

Experiment scenario validation

Dataset integrity

Run:

pytest -q

Documentation

Methodology

Decision Framework

Data Dictionary

Key Design Choices

SSR over CTR: measures whether a search actually succeeds, not only whether a result was clicked.

User-level inference: avoids treating repeated searches from the same user as independent observations.

Behavior-first simulation: clicks, dwell, reformulation, and success emerge from simulated search behavior.

Guardrails: prevents an SSR improvement from being interpreted without considering latency and errors.

Deterministic decision engine: converts statistical evidence into a transparent, repeatable decision.

Lean architecture: PostgreSQL + Python + SQL + Streamlit + Power BI.

Scope & Limitations

PRYVIA is a simulated experimentation platform. The data is synthetic and the experiment scenarios are intentionally constructed to demonstrate different analytical outcomes. Results should therefore be interpreted as a demonstration of experimentation methodology, not as real product evidence.

Author

Pratikshya Dash

Data Analytics · Product Analytics · SQL · Python · Power BI · PostgreSQL

LinkedIn · GitHub
