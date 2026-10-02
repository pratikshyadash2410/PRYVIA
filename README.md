# PRYVIA

### Search-Ranking A/B Experimentation & Decision Engine

PRYVIA is a simulated product-analytics platform for evaluating search-ranking A/B tests using **Successful Search Rate (SSR)**, statistical inference, guardrails, and an explainable decision engine.

**Stack:** Python · PostgreSQL · SQL · Streamlit · Power BI

---

## **What It Does**

- Simulates realistic user search behavior
- Measures **Successful Search Rate (SSR)** beyond CTR
- Performs user-level A/B experiment analysis
- Checks SRM, statistical significance, confidence intervals, and power
- Evaluates latency and error-rate guardrails
- Produces deterministic experiment decisions

### **SSR**

A search is successful when:

- A result is clicked
- Dwell time is ≥ 30 seconds
- The search is not a reformulation

Reformulation: the same user performs another search within **300 seconds** in the same session.

---

## **Experiment Design**

- User-level sticky assignment
- 50/50 Control vs Treatment
- Baseline SSR: 65%
- MDE: ±5 percentage points
- Power: 80%
- α = 0.05
- Planned sample: ~2,752 users

Statistical inference is performed at the **user level** because users can generate multiple searches.

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

PRYVIA/
├── app/
├── docs/
├── powerbi/
├── sql/
├── src/
├── tests/
├── requirements.txt
└── README.md

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PRYVIA

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run app/app.py

Key Skills

Product Analytics · A/B Testing · SQL · Python · PostgreSQL · Statistics · Streamlit · Power BI

Author

Pratikshya Dash
