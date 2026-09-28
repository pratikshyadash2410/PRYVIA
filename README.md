# PRYVIA

### Search-Ranking A/B Experimentation & Decision Engine

<p align="left">

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=flat-square&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)

</p>

An end-to-end product analytics and experimentation platform that simulates search-ranking A/B testing — from behavioral data synthesis and PostgreSQL schema design to user-level statistical inference, guardrail checks, and deterministic product decisions.

---

## Executive Overview

Search evaluation can over-index on Click-Through Rate (CTR), even when clicks do not translate into useful search outcomes. PRYVIA introduces **Successful Search Rate (SSR)** as the core outcome metric.

$$
\text{SSR} =
\frac{\text{searches with a quality click and no reformulation}}
{\text{total searches}}
$$

Where:

- **Quality click** — a clicked result with ≥ 30 seconds of dwell time
- **Reformulation** — a follow-up search within 300 seconds in the same session

```text
Behavior
    ↓
PostgreSQL Model
    ↓
SQL Analysis
    ↓
Statistical Evidence
    ↓
Decision Engine
    ↓
Business Action

[!IMPORTANT]
PRYVIA separates measurement, statistical inference, and product decision logic. A statistically significant result does not automatically mean "ship."

Core Methodology
Metric / Check	Purpose	Statistical Standard
Primary outcome — SSR	Successful search completion	User-level Welch's t-test + bootstrap 95% CI
SRM	Randomization health check	χ² goodness-of-fit; p < 0.01 → FAIL
Power & MDE	Experiment sensitivity	Target power 80% · Baseline SSR 65% · MDE ±5 pp
Technical guardrails	System integrity	Search error rate + median latency
Secondary diagnostics	Behavioral context	CTR + reformulation rate

[!NOTE]
Why user-level inference?

Randomization happens at the user level with sticky assignment, while measurement occurs at the search level. Repeated searches from the same user can be correlated, so inference is aggregated to the user grain rather than treating every search as independent.

Design Parameters
Parameter	Value
Randomization unit	User
Assignment	Sticky Control / Treatment
Planned allocation	50 / 50
Significance level	α = 0.05
Required sample size	≈ 2,752 total users (≈ 1,376 per group)
Bootstrap	10,000 iterations, seed = 42
Deterministic Decision Engine

PRYVIA uses a strict hierarchical rule engine. The first matching rule wins.

Decision Rules
Rule	Evidence Condition	Verdict
1	SRM failed	INVESTIGATE
2	Actual users < required sample size	RUN FOLLOW-UP
3	Not significant + CI wider than MDE	RUN FOLLOW-UP
4	Not significant + CI entirely within ±MDE	DON'T SHIP
5	Significant + negative SSR effect	DON'T SHIP
6	Significant + positive SSR effect + guardrail breach	SHIP WITH CAUTION
7	Significant + positive SSR effect + clean guardrails	SHIP

Statistical significance alone does not automatically produce a clean ship decision.

Frozen Experiment Scenarios

The simulated dataset contains four deliberately different experiment situations:

Experiment	Scenario	SSR Lift	p-value	Power	Guardrails	Verdict	Rule
1	Clear winner	+4.57 pp	< 0.001	Adequate	Healthy	SHIP	7
2	Inconclusive / underpowered	+2.16 pp	0.1590	Inadequate	Healthy	RUN FOLLOW-UP	2
3	Segment signal	+2.19 pp	0.0167	Adequate	Healthy	SHIP	7
4	Guardrail violation	+2.41 pp	0.0080	Adequate	Latency breach	SHIP WITH CAUTION	6

[!NOTE]
Experiment 2 has 1,000 exposed users (507 Control / 493 Treatment) against a required sample of ≈ 2,752, giving achieved power of ≈ 39.3%. It therefore triggers the underpowered rule before significance is considered. The observed +2.16 pp lift with p = 0.159 is not treated as evidence of an effect.

Architecture & Tech Stack
Layer	Technology
Database	PostgreSQL
Data generation	Python behavioral simulation
Analytics	PostgreSQL SQL, Pandas, NumPy
Statistics	SciPy, Statsmodels
Application	Streamlit, Matplotlib
BI	Power BI
Behavioral Simulation
Users
  ↓
Sessions
  ↓
Searches
  ↓
Ranking / Relevance
  ↓
Clicks
  ↓
Dwell Time
  ↓
Reformulation
  ↓
Successful Search
  ↓
Business Events
Data Model

Seven PostgreSQL tables:

users
experiments
experiment_assignments
search_sessions
searches
search_results
business_events

A derived view, vw_search_success, centralizes the search-success definition for SQL analysis.

Frozen Dataset
Entity	Rows
Users generated	12,000
Experiment assignments	10,000
Search sessions	27,863
Searches	44,657
Search results	223,285
Business events	121,659

Every search has five ranked results.

Overall generated SSR: 63.45%.

Of the 12,000 generated users, 10,000 are enrolled across the four experiments.

Repository Structure
PRYVIA/
│
├── README.md
├── .gitignore
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
│       ├── 01_experiment_portfolio.png
│       ├── 02_core_metrics.png
│       └── 03_segmentation.png
│
├── sql/
│   ├── analysis.sql
│   ├── indexes.sql
│   ├── schema.sql
│   └── vw_search_success.sql
│
├── src/
│   ├── __init__.py
│   ├── decision_engine.py
│   ├── experiment_assignments_prototype.csv
│   ├── experiment_verdicts.csv
│   ├── generate_experiment_scenarios.py
│   ├── generate_experiment_verdicts.py
│   ├── import_to_postgres.py
│   ├── searches_prototype.csv
│   ├── searches_with_reformulation.csv
│   ├── search_results_final.csv
│   ├── search_sessions_prototype.csv
│   ├── search_success_prototype.csv
│   ├── statistical_analysis.py
│   ├── users_prototype.csv
│   ├── validate_experiment_scenarios.py
│   ├── validate_final_dataset.py
│   ├── validate_segment_signal.py
│   └── validate_success_logic.py
│
└── tests/
    ├── test_decision_engine.py
    └── test_statistical_analysis.py
Quick Start
1. Clone the repository
git clone https://github.com/pratikshyadash2410/PRYVIA.git
cd PRYVIA
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\activate
macOS / Linux
python -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Launch the Streamlit app

No PostgreSQL setup is required to explore the decision engine. The app reads the frozen experiment CSVs in src/.

streamlit run app/app.py
5. Run the test suite
pytest -q

Expected result:

10 passed
Streamlit Decision Engine
Frozen Data
     ↓
statistical_analysis.py
     ↓
decision_engine.py
     ↓
app.py
     ↓
Streamlit UI

The application presents evidence in this order:

Final verdict → Experiment health → Primary SSR metric → Confidence interval → Technical guardrails → Secondary diagnostics → Decision explanation → Exploratory segments

The app does not contain a second implementation of the decision rules. Computation, decision logic, and presentation remain separated.

Decision Philosophy

The decision engine evaluates:

Experiment validity
Statistical power
Practical significance relative to the MDE
Direction of the effect
Technical guardrails

This makes the final verdict deterministic and auditable.

Power BI Dashboard

The Power BI report contains three pages:

Page	Question	Focus
01 — Experiment Portfolio	What is happening?	Verdicts, SSR lift, p-values, SRM, guardrails, portfolio KPIs
02 — Core Metrics	Why?	Control vs Treatment SSR, error rate, latency
03 — Segmentation & Exploration	Where?	Device, activity level, query category
Dashboard Screenshots
Experiment Portfolio

Core Metrics

Segmentation & Exploration

[!NOTE]
Segment analysis is exploratory only and does not feed the ship decision.

SQL & Statistical Separation

PRYVIA deliberately separates descriptive SQL analysis from user-level statistical inference.

PostgreSQL / SQL
        ↓
Descriptive search-level analysis
        ↓
Python
        ↓
User-level statistical inference
        ↓
Decision Engine
        ↓
Verdict
SQL Layer

The SQL layer covers:

Relational joins
CTEs
Aggregations
Window functions
Reformulation detection
Session analysis
Cohort analysis
Search-level SSR
CTR
Search errors
Search latency
Dwell behavior
Exploratory segmentation
Python Statistical Layer

The Python layer covers:

SRM testing
Power analysis
Sample-size planning
User-level SSR inference
Confidence intervals
Effect size
Guardrail evaluation
Deterministic decision logic
Testing

PRYVIA includes regression tests for the statistical analysis and decision engine.

The frozen scenario tests verify:

Experiment	Expected Verdict	Rule
1	SHIP	7
2	RUN FOLLOW-UP	2
3	SHIP	7
4	SHIP WITH CAUTION	6

Current test result:

10 passed
Documentation
docs/methodology.md — experiment design, metric definitions, and statistical methodology
docs/decision_framework.md — deterministic decision rules
docs/data_dictionary.md — schema, columns, relationships, and table grain
Key Analytical Design Choices
<details> <summary><strong>Why user-level inference?</strong></summary>

The experiment randomizes users, while SSR is measured from searches.

Multiple searches from one user are not independent, so PRYVIA uses:

Searches as the measurement grain
Users as the inference grain

This avoids incorrectly treating repeated searches from the same user as independent observations.

</details> <details> <summary><strong>Why SSR instead of CTR?</strong></summary>

CTR captures clicks.

SSR captures a more meaningful successful-search outcome by combining quality engagement with the absence of a follow-up reformulation.

</details> <details> <summary><strong>Why separate guardrails from diagnostics?</strong></summary>

Error rate and latency can change the final decision.

CTR and reformulation are secondary diagnostics and do not override the decision engine on their own.

</details> <details> <summary><strong>Why a deterministic decision engine?</strong></summary>

The same evidence should always produce the same verdict.

Explicit rules make the framework testable, explainable, and easy to audit.

</details>
Project Scope

PRYVIA prioritizes analytical depth over technology breadth.

Included
Product analytics
A/B experimentation
Behavioral data generation
PostgreSQL modeling
SQL analytics
Statistical inference
Power analysis
Confidence intervals
SRM checks
Technical guardrails
Deterministic decision framework
Streamlit
Power BI
Regression testing
Technical documentation
Intentionally Excluded
Kafka
Spark
Airflow
Kubernetes
AI / LLM features

The project is deliberately lean and focused on product analytics and experimentation rather than infrastructure breadth.

Limitations

PRYVIA uses synthetic data and intentionally constructed experiment scenarios.

Results do not represent real production traffic or real customer findings.
Scenario effects are designed for analytical demonstration.
Segment findings are exploratory and should not be interpreted as causal subgroup effects without follow-up analysis.
The search-ranking system itself is simulated; PRYVIA evaluates the experimental evidence rather than implementing a production search engine.

The portfolio value is in the complete workflow:

behavior → measurement → experimentation → statistical evidence → product decision

Author

Pratikshya Dash
B.Tech in Computer Science & Engineering

Focus: Product Analytics · Experimentation · Data Modeling · SQL · Decision Systems

LinkedIn · GitHub


### One important thing

This is the version I recommend you put in GitHub **instead of the old README currently there**.

After replacing it locally:

1. Save `README.md`
2. Open GitHub Desktop
3. You should see `README.md` under **Changes**
4. Commit message:
   ```text
   Update README for final repository structure
Click Commit to main
Click Push origin

Then the GitHub README will match the repository we actually built.

keep it in a file n send

Done — I kept the final README in a file.

Download PRYVIA_README_FINAL.md

PRYVIA_README_FINAL.md
Document

Library
/
PRYVIA
/
PRYVIA_README_FINAL.md
PRYVIA — Search Ranking A/B Experimentation Platform

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

Rule	Condition	Decision
1	SRM failure	INVESTIGATE
2	Actual users below required sample size	RUN FOLLOW-UP
3	Not significant and CI wider than MDE	RUN FOLLOW-UP
4	Not significant and entire CI lies within ±MDE	DON'T SHIP
5	Statistically significant negative SSR effect	DON'T SHIP
6	Statistically significant positive SSR effect + guardrail breach	SHIP WITH CAUTION
7	Statistically significant positive SSR effect + clean guardrails	SHIP

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

Experiment	Scenario	Intended analytical behavior
Exp 1	Clear winner	Positive SSR lift with clean guardrails
Exp 2	Inconclusive / underpowered	Small effect with insufficient sample
Exp 3	Segment signal	Overall positive effect with segment-level differences
Exp 4	Guardrail violation	Positive SSR effect with latency deterioration
Frozen Results
Experiment	Control SSR	Treatment SSR	Lift	p-value	Decision
Exp 1	66.29%	70.87%	+4.57 pp	<0.001	SHIP
Exp 2	67.29%	69.45%	+2.16 pp	0.159	RUN FOLLOW-UP
Exp 3	66.65%	68.85%	+2.19 pp	0.017	SHIP
Exp 4	66.61%	69.02%	+2.41 pp	0.008	SHIP WITH CAUTION

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
│   └── frozen CSV datasets
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

Entity	Rows
Users	12,000
Experiment assignments	10,000
Sessions	27,863
Searches	44,657
Search results	223,285
Business events	121,659

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
