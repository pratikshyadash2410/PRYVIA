# PRYVIA

### Search-Ranking A/B Experimentation & Decision Engine

PRYVIA is a simulated product analytics platform for evaluating search ranking A/B tests using **Successful Search Rate (SSR)**, statistical inference, guardrails and an explainable decision engine.

**Stack:** Python · PostgreSQL · SQL · Streamlit · Power BI

---

## **What It Does**

- Simulates realistic user search behavior
- Measures **Successful Search Rate (SSR)** beyond CTR
- Performs user level A/B experiment analysis
- Checks SRM, statistical significance, confidence intervals and power
- Evaluates latency and error rate guardrails
- Produces deterministic experiment decisions

### **SSR**

A search is successful when:

- A result is clicked
- Dwell time is ≥ 30 seconds
- The search is not a reformulation

Reformulation: the same user performs another search within **300 seconds** in the same session.

---

## **Experiment Design**

| Parameter       | Value                                          |
|-----------------|------------------------------------------------|
| Assignment      | User-level, sticky, 50/50 Control vs Treatment |
| Baseline SSR    | 65%                                            |
| MDE             | ±5 percentage points                           |
| Target power    | 80%                                            |
| Significance    | α = 0.05                                       |
| Required sample | ≈2,752 users                                   |

Inference is performed at the **user level**, since a single user can generate multiple searches and those observations are not independent.

---

## **Decision Engine**

The engine evaluates experiment health and outcomes in a fixed order:

| Condition | Decision |
|---|---|
| SRM failed | INVESTIGATE |
| Underpowered | RUN FOLLOW-UP |
| Inconclusive | RUN FOLLOW-UP |
| Confidently null | DON'T SHIP |
| Significant negative effect | DON'T SHIP |
| Positive effect + guardrail breach | SHIP WITH CAUTION |
| Positive effect + clean guardrails | SHIP |

---

## **Dataset**

| Metric | Rows |
|---|---:|
| Users | 12,000 |
| Assignments | 10,000 |
| Sessions | 27,863 |
| Searches | 44,657 |
| Results | 223,285 |
| Business events | 121,659 |

Four simulated experiment scenarios demonstrate clear improvement, an underpowered result, a segment signal, and a guardrail violation.

---

## **Architecture**

```text
Python Simulation
       ↓
PostgreSQL
       ↓
SQL Analysis
       ↓
Python Statistical Analysis
       ↓
Decision Engine
       ↓
Streamlit
       ↓
Power BI
```

## Repository Structure

```text
PRYVIA/
├── app/           # Streamlit decision engine UI
├── docs/          # Methodology, decision framework, data dictionary
├── powerbi/       # Dashboard files & screenshots
├── sql/           # Schema, indexes, views, analysis
├── src/           # Generators, statistical analysis, decision engine
├── tests/         # Unit & regression test suite
├── requirements.txt
└── README.md
```

## Quick Start

Clone the repository:

```bash
git clone https://github.com/pratikshyadash2410/PRYVIA.git
cd PRYVIA
python -m venv .venv
.venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

## **Power BI Dashboard**

| Page | Focus |
|---|---|
| **01 — Experiment Portfolio** | Verdicts, SSR lift, p-values, and guardrails |
| **02 — Core Metrics** | Control vs Treatment SSR, error rate, and latency |
| **03 — Segmentation** | Device, activity level, and query category (exploratory) |

## Limitations

PRYVIA uses synthetic data; results do not represent real production traffic. Scenario effects are intentionally constructed to exercise different decision outcomes. Segment findings are exploratory and not causal.

## **Key Skills** 

Product Analytics · A/B Testing · SQL · Python · PostgreSQL · Statistics · Streamlit · Power BI

## Author

Pratikshya Dash
