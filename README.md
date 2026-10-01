PRYVIA

Search-Ranking A/B Experimentation & Decision Engine






A product analytics portfolio project for evaluating search-ranking experiments using Successful Search Rate (SSR), experiment health, statistical inference, guardrails, and a deterministic ship decision engine.

Executive Overview

PRYVIA simulates a user-level A/B experiment for a search-ranking system.

Instead of optimizing only for clicks, the project evaluates whether a search actually succeeds. The primary metric is Successful Search Rate (SSR), supported by experiment-health checks, statistical inference, and technical guardrails.

The platform is designed around one practical product question:

Should the new search-ranking experience be shipped?

PRYVIA answers that question through a deterministic decision engine using SRM, sample-size sufficiency, SSR effect size, confidence intervals, statistical significance, and guardrail health.

Core Methodology

Primary Metric — Successful Search Rate

A search is considered successful when:

A result is clicked.

The clicked result has at least 30 seconds of dwell time.

The search is not a reformulation.

Therefore:

SSR = Successful Searches / Total Searches

Unit of Randomization vs Unit of Inference

Users are randomly assigned to Control or Treatment, and the assignment is sticky.

Searches are the grain at which SSR is measured, but statistical inference is performed at the user level to account for repeated searches from the same user.

This avoids treating correlated searches from the same user as independent observations.

Reformulation

A search is classified as a reformulation when another search from the same user occurs within 300 seconds (5 minutes).

Guardrails

Technical guardrails include:

Search error rate

Search latency

Secondary/diagnostic metrics include:

CTR

Reformulation rate

Dwell time

Decision Engine

PRYVIA uses a deterministic first-match decision hierarchy.

Rule

Condition

Decision

1

SRM failure

INVESTIGATE

2

Actual users below required sample size

RUN FOLLOW-UP

3

Not significant and CI wider than MDE

RUN FOLLOW-UP

4

Not significant and entire CI lies within ±MDE

DON'T SHIP

5

Statistically significant negative SSR effect

DON'T SHIP

6

Statistically significant positive SSR effect + guardrail breach

SHIP WITH CAUTION

7

Statistically significant positive SSR effect + clean guardrails

SHIP

The engine returns a structured result containing:

Verdict

Triggered rule

Rule label

Severity

Reason

Explanation bullets

Explanation markdown

No AI/LLM is used in the decision process.

Frozen Experiment Scenarios

The dataset contains four intentionally designed experiment scenarios.

Experiment

Scenario

Intended analytical behavior

Exp 1

Clear winner

Positive SSR lift with clean guardrails

Exp 2

Inconclusive / underpowered

Small effect with insufficient sample

Exp 3

Segment signal

Overall positive effect with segment-level differences

Exp 4

Guardrail violation

Positive SSR effect with latency deterioration

Frozen Results

Experiment

Control SSR

Treatment SSR

Lift

p-value

Decision

Exp 1

66.29%

70.87%

+4.57 pp

<0.001

SHIP

Exp 2

67.29%

69.45%

+2.16 pp

0.159

RUN FOLLOW-UP

Exp 3

66.65%

68.85%

+2.19 pp

0.017

SHIP

Exp 4

66.61%

69.02%

+2.41 pp

0.008

SHIP WITH CAUTION

Exp 2 is intentionally underpowered. The required total sample is approximately 2,752 users, while the experiment exposes only 1,000 assigned users.

Exp 4 demonstrates why a statistically positive primary metric does not automatically imply a clean launch: its treatment latency increases by approximately 90 ms versus Control.

Architecture

                 ┌──────────────────────┐
                 │ Behaviour Simulation  │
                 │ Python               │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ PostgreSQL           │
                 │ 7-table data model   │
                 └──────────┬───────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────────┐           ┌───────────────┐
       │ SQL Analysis │           │ Python Stats  │
       │ Descriptive  │           │ Inference     │
       └──────────────┘           └───────┬───────┘
                                         │
                                         ▼
                               ┌────────────────────┐
                               │ Decision Engine     │
                               │ SHIP / DON'T SHIP   │
                               └─────────┬──────────┘
                                         │
                         ┌───────────────┴──────────────┐
                         ▼                              ▼
                 ┌──────────────┐              ┌──────────────┐
                 │ Streamlit    │              │ Power BI     │
                 │ Decision App │              │ Dashboard    │
                 └──────────────┘              └──────────────┘

Tech Stack

PostgreSQL

Python

Pandas

NumPy

SciPy

Statsmodels

Streamlit

Power BI

SQL

Git / GitHub

The project deliberately avoids unnecessary infrastructure such as Kafka, Spark, Airflow, Kubernetes, or AI/LLM features.

Repository Structure

PRYVIA/
│
├── README.md
├── .gitignore
├── .gitattributes
├── pytest.ini
├── requirements.txt
│
├── app/
│   └── app.py
│
├── docs/
│   ├── data_dictionary.md
│   ├── decision_framework.md
│   └── methodology.md
│
├── powerbi/
│   └── screenshots/
│
├── sql/
│   ├── analysis.sql
│   ├── indexes.sql
│   ├── schema.sql
│   └── vw_search_success.sql
│
├── src/
│   ├── __init__.py
│   ├── generate_experiment_scenarios.py
│   ├── generate_experiment_verdicts.py
│   ├── statistical_analysis.py
│   ├── decision_engine.py
│   ├── import_to_postgres.py
│   ├── validate_final_dataset.py
│   ├── validate_success_logic.py
│   ├── validate_experiment_scenarios.py
│   ├── validate_segment_signal.py
│   ├── users_prototype.csv
│   ├── experiment_assignments_prototype.csv
│   ├── search_sessions_prototype.csv
│   ├── searches_prototype.csv
│   ├── searches_with_reformulation.csv
│   ├── search_results_prototype.csv
│   ├── search_results_final.csv
│   ├── search_success_prototype.csv
│   ├── business_events_prototype.csv
│   └── experiment_verdicts.csv
│
├── tests/
│   ├── test_decision_engine.py
│   └── test_statistical_analysis.py
│
├── .gitignore
├── requirements.txt
└── README.md

Data Model

PRYVIA uses seven core PostgreSQL tables:

users

experiments

experiment_assignments

search_sessions

searches

search_results

business_events

The model captures the full behavioral chain:

User
  ↓
Experiment Assignment
  ↓
Search Session
  ↓
Search
  ↓
Search Results
  ↓
Click
  ↓
Dwell
  ↓
Reformulation / Success

Frozen Dataset Scale

The current frozen dataset contains approximately:

Entity

Rows

Users

12,000

Experiment assignments

10,000

Sessions

27,863

Searches

44,657

Search results

223,285

Business events

121,659

Every search has five ranked results.

The generated behavior is downstream-driven: ranking influences relevance, relevance influences clicks, clicks influence dwell, and those behaviors influence reformulation and successful search.

Quick Start

1. Clone the repository

git clone <your-repository-url>
cd PRYVIA

2. Create a virtual environment

Windows:

python -m venv .venv
.venv\\Scripts\\activate

3. Install dependencies

pip install -r requirements.txt

4. Run the tests

pytest -q

Expected result:

10 passed

5. Generate the frozen simulation

Run:

python src/generate_experiment_scenarios.py

This generates the behavior-driven experiment dataset.

6. Load PostgreSQL

Create a PostgreSQL database named:

pryvia_analytics

Then execute:

sql/schema.sql
sql/indexes.sql

Import the generated CSV data using the provided PostgreSQL import workflow.

7. Create the analytical view

Run:

sql/vw_search_success.sql

The view produces the search-level analytical dataset used by SQL and downstream analysis.

Streamlit Decision Engine

Run:

streamlit run app/app.py

The application presents:

Experiment verdict

Experiment health

Primary SSR metric

Confidence interval

Guardrails

Secondary metrics

Decision explanation

Exploratory segment analysis

The Streamlit layer is intentionally a presentation layer.

Statistical calculations live in:

src/statistical_analysis.py

Decision logic lives in:

src/decision_engine.py

Power BI Dashboard

The Power BI report contains three pages.

Page 1 — Experiment Portfolio / Executive Overview

Shows:

Total experiments

Top SSR lift

Guardrail health

Average treatment median latency

Experiment verdict table

Evidence summary



Page 2 — Core Metrics

Shows:

SSR by experiment and variant

Error rate

Median latency

Guardrail reference



Page 3 — Segmentation & Exploration

Shows exploratory SSR differences by:

Device type

Activity level

Query category



Segment analysis is explicitly exploratory and does not feed the ship decision.

SQL vs Python Statistical Analysis

PRYVIA intentionally separates descriptive SQL analysis from statistical inference.

SQL

SQL is used for:

Joins

CTEs

Window functions

Search/session analysis

Reformulation detection

Search-level SSR

CTR

Dwell

Error rate

Latency

Segmentation

Python

Python is used for:

SRM testing

Power/sample-size analysis

User-level inference

Confidence intervals

Effect size

Guardrail evaluation

Decision engine inputs

This separation keeps the analytical workflow explainable and avoids treating repeated searches from the same user as independent statistical observations.

Statistical Design

SRM

The experiment expects approximately 50/50 assignment.

SRM is checked before interpreting experiment results.

Power

Sample-size planning uses the baseline rate, minimum detectable effect, significance level, and target power.

The frozen configuration requires approximately:

2,752 total users
≈ 1,376 users per variant

for the configured planning assumptions.

Confidence Intervals

PRYVIA uses user-level bootstrap confidence intervals for the SSR difference.

The bootstrap configuration uses:

10,000 resamples
Random seed = 42

Statistical Unit

Users are the unit of inference because users can generate multiple searches.

Testing

The project includes automated tests for both statistical analysis and the decision engine.

Current test coverage verifies:

Statistical analysis runs for all frozen experiments

SRM passes

Exp 2 is identified as underpowered

Exp 1 has positive SSR lift

Exp 4 detects the latency guardrail breach

Exp 1 → SHIP

Exp 2 → RUN FOLLOW-UP

Exp 3 → SHIP

Exp 4 → SHIP WITH CAUTION

Frozen experiment decisions remain stable

Run:

pytest -q

Documentation

Supporting documentation is available in:

docs/
├── data_dictionary.md
├── decision_framework.md
└── methodology.md

These documents explain the dataset, analytical methodology, and deterministic decision framework.

Key Analytical Design Choices

1. User-level randomization

Assignment is performed once per user and remains sticky.

2. User-level inference

Repeated searches from the same user are correlated, so statistical inference is aggregated at the user level.

3. SSR instead of CTR alone

A click does not necessarily indicate a successful search. PRYVIA requires meaningful dwell time and no reformulation.

4. Guardrails

A positive primary metric can still require caution if technical experience deteriorates.

5. Deterministic decisions

The decision engine uses explicit rules rather than subjective interpretation.

6. Behavior-first simulation

Metrics are not manually assigned at the end of the simulation. They emerge from the simulated user journey.

Project Scope

PRYVIA intentionally focuses on depth rather than infrastructure breadth.

Included:

Behavioral simulation

PostgreSQL data modeling

SQL analytics

A/B testing methodology

SRM

Power analysis

Confidence intervals

Effect size

Guardrails

Deterministic decision engine

Streamlit application

Power BI dashboard

Automated tests

Not included:

AI/LLM features

Kafka

Spark

Airflow

Kubernetes

Production deployment infrastructure

This keeps the project focused on product analytics, experimentation, statistical reasoning, and data engineering fundamentals.

Limitations

PRYVIA is a simulated experimentation platform rather than a production experimentation system.

Important limitations include:

User behavior is simulated rather than observed from real production traffic.

Experiment scenarios are intentionally designed to demonstrate different analytical outcomes.

Search ranking and relevance are simplified representations of real ranking systems.

Guardrail thresholds and planning assumptions are project-specific.

The dataset is frozen for reproducibility.

The goal is not to claim production-scale experimentation experience, but to demonstrate an end-to-end understanding of how an experimentation analytics workflow can be designed, validated, analyzed, and communicated.

Final Portfolio Outcome

PRYVIA demonstrates an end-to-end product analytics workflow:

Behavior Simulation
        ↓
PostgreSQL Data Model
        ↓
SQL Analytics
        ↓
Statistical Experiment Analysis
        ↓
Guardrail Evaluation
        ↓
Deterministic Decision Engine
        ↓
Streamlit Decision App
        ↓
Power BI Executive Dashboard

The central product question remains simple:

Did the new search-ranking experience improve successful search without introducing unacceptable technical regressions?
