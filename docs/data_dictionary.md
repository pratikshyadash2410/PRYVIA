# PRYVIA Data Dictionary

## Database

**Database:** `pryvia_analytics`  
**Database engine:** PostgreSQL

PRYVIA uses seven core tables to represent the complete search-experiment flow:

```text
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
```

The `experiments` table defines the experiment itself and connects to user assignments.

---

# 1. `users`

## Purpose

Stores one record for each simulated user.

Users are the population from which experiment participants are assigned to Control or Treatment.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `user_id` | bigint | Primary Key | Unique identifier for the user |
| `user_type` | varchar(20) | NOT NULL | User classification |
| `device_type` | varchar(20) | — | Device used by the user |
| `country` | varchar(50) | — | User country |
| `activity_level` | varchar(20) | — | User activity classification |
| `signup_date` | date | — | Date the user signed up |

### Important analytical fields

- `device_type` is used for exploratory segmentation.
- `activity_level` is used for exploratory segmentation.
- `user_id` is the experiment's randomization-unit identifier.

---

# 2. `experiments`

## Purpose

Stores the experiment definitions.

Each experiment represents a search-ranking A/B test scenario.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `experiment_id` | integer | Primary Key | Unique experiment identifier |
| `experiment_name` | varchar(100) | — | Human-readable experiment name |
| `start_date` | date | — | Experiment start date |
| `end_date` | date | — | Experiment end date; nullable |
| `allocation_ratio` | numeric(5,4) | — | Planned allocation ratio |
| `primary_metric` | varchar(50) | — | Primary experiment metric |

### Current primary metric

```text
Successful Search Rate (SSR)
```

---

# 3. `experiment_assignments`

## Purpose

Stores the assignment of users to experiment variants.

This table establishes the experiment's randomization.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `assignment_id` | bigint | Primary Key, identity | Unique assignment record |
| `experiment_id` | integer | Foreign Key | Experiment receiving the assignment |
| `user_id` | bigint | Foreign Key | User receiving the assignment |
| `variant` | varchar(20) | — | Assigned experiment variant |

### Variants

PRYVIA currently uses:

```text
Control
Treatment
```

### Important constraint

The combination:

```text
(experiment_id, user_id)
```

is unique.

This ensures that a user cannot receive multiple assignments within the same experiment.

### Relationship

```text
experiments.experiment_id
        ↓
experiment_assignments.experiment_id

users.user_id
        ↓
experiment_assignments.user_id
```

---

# 4. `search_sessions`

## Purpose

Represents a user's search session.

A session groups searches performed by the same user during a browsing session.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `session_id` | bigint | Primary Key | Unique session identifier |
| `user_id` | bigint | Foreign Key | User who owns the session |
| `session_start` | timestamp | — | Session start time |
| `session_end` | timestamp | — | Session end time; nullable |

### Relationship

```text
users.user_id
        ↓
search_sessions.user_id
```

One user can have multiple sessions.

---

# 5. `searches`

## Purpose

Stores individual search events.

This is the central behavioral table for search-level analysis.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `search_id` | bigint | Primary Key | Unique search identifier |
| `session_id` | bigint | Foreign Key | Session containing the search |
| `query_text` | text | — | Search query |
| `query_category` | varchar(30) | — | Search category |
| `search_timestamp` | timestamp | — | Time of the search |
| `search_latency_ms` | integer | — | Search response latency in milliseconds |
| `search_error` | boolean | Default FALSE | Whether the search produced an error |
| `is_reformulation` | boolean | — | Whether the search is classified as a reformulation |

### Important analytical fields

#### `search_latency_ms`

Used for the technical latency guardrail.

#### `search_error`

Used for the technical search-error guardrail.

#### `is_reformulation`

Used in the SSR definition and reformulation-rate analysis.

PRYVIA uses a 300-second window when identifying reformulations.

### Relationship

```text
search_sessions.session_id
        ↓
searches.session_id
```

One session can contain multiple searches.

---

# 6. `search_results`

## Purpose

Stores the results returned for each search.

Each search currently contains five result rows.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `result_id` | bigint | Primary Key | Unique result record |
| `search_id` | bigint | Foreign Key | Search that produced the result |
| `rank_position` | integer | — | Position of the result in the ranking |
| `result_type` | varchar(30) | — | Type/category of result |
| `relevance_score` | numeric(5,4) | — | Simulated relevance score |
| `clicked` | boolean | Default FALSE | Whether the result was clicked |
| `dwell_time_seconds` | numeric(8,2) | — | Time spent on the clicked result |
| `returned_to_search` | boolean | — | Whether the user returned to the search |

### Important analytical fields

#### `rank_position`

Represents where a result appeared in the ranking.

#### `relevance_score`

Represents the simulated relevance of the result.

#### `clicked`

Used to calculate click behavior and CTR.

#### `dwell_time_seconds`

Used to identify a quality click.

The PRYVIA quality-click rule is:

```text
clicked = TRUE
AND dwell_time_seconds >= 30
```

### Relationship

```text
searches.search_id
        ↓
search_results.search_id
```

One search can have multiple results.

---

# 7. `business_events`

## Purpose

Stores event-level records derived from search behavior.

This provides an event stream representation of important user actions without introducing an external streaming technology.

| Column | Type | Key / Constraint | Description |
|---|---|---|---|
| `event_id` | bigint | Primary Key | Unique business event identifier |
| `search_id` | bigint | Foreign Key | Search associated with the event |
| `event_type` | varchar(30) | — | Type of business event |
| `event_timestamp` | timestamp | — | Time the event occurred |

### Current event types

PRYVIA generates events for:

```text
click
dwell
reformulation
success
```

### Relationship

```text
searches.search_id
        ↓
business_events.search_id
```

Multiple business events can belong to the same search.

---

# Relationship Overview

The seven core tables form the following analytical path:

```text
                         ┌────────────────┐
                         │   experiments   │
                         └───────┬────────┘
                                 │
                                 │ experiment_id
                                 ↓
┌────────────┐             ┌───────────────────────┐
│   users    │────────────→│ experiment_assignments│
└─────┬──────┘             └───────────────────────┘
      │
      │ user_id
      ↓
┌─────────────────┐
│ search_sessions │
└────────┬────────┘
         │
         │ session_id
         ↓
┌────────────┐
│  searches  │
└─────┬──────┘
      │
      ├───────────────────────┐
      │                       │
      │ search_id             │ search_id
      ↓                       ↓
┌───────────────┐      ┌────────────────┐
│ search_results│      │ business_events│
└───────────────┘      └────────────────┘
```

---

# Foreign-Key Relationships

| Parent | Child | Relationship |
|---|---|---|
| `users.user_id` | `experiment_assignments.user_id` | User → experiment assignment |
| `experiments.experiment_id` | `experiment_assignments.experiment_id` | Experiment → assignments |
| `users.user_id` | `search_sessions.user_id` | User → sessions |
| `search_sessions.session_id` | `searches.session_id` | Session → searches |
| `searches.search_id` | `search_results.search_id` | Search → results |
| `searches.search_id` | `business_events.search_id` | Search → business events |

---

# Grain of Each Table

Understanding table grain is critical for PRYVIA because the experiment contains repeated observations at different levels.

| Table | Grain |
|---|---|
| `users` | One row per user |
| `experiments` | One row per experiment |
| `experiment_assignments` | One row per user × experiment |
| `search_sessions` | One row per session |
| `searches` | One row per search |
| `search_results` | One row per result |
| `business_events` | One row per business event |

### Why grain matters

A single user can generate:

```text
1 user
  → multiple sessions
    → multiple searches
      → multiple results
        → multiple business events
```

Therefore, search-level and result-level rows cannot automatically be treated as independent statistical observations.

PRYVIA's statistical analysis aggregates the behavioral data back to the **user level** before inference.

---

# Derived Analytical Concepts

Some important PRYVIA metrics are not stored as a single column. They are derived from the raw tables.

## Quality Click

Derived from `search_results`:

```text
clicked = TRUE
AND dwell_time_seconds >= 30
```

## Successful Search

Derived from `search_results` + `searches`:

```text
quality_click = TRUE
AND is_reformulation = FALSE
```

## Successful Search Rate

At search level:

```text
successful searches / total searches
```

For inference:

```text
user SSR =
successful searches / total searches
```

followed by a Treatment vs Control comparison across users.

## CTR

A search is counted as clicked when at least one result for that search has:

```text
clicked = TRUE
```

## Reformulation Rate

```text
reformulated searches / total searches
```

## Search Error Rate

```text
searches with search_error = TRUE
--------------------------------
total searches
```

## Median Search Latency

For each user:

```text
median(search_latency_ms)
```

The resulting user-level medians are compared between variants.

---

# Analytical Views

PRYVIA also creates a derived SQL view:

```text
vw_search_success
```

This is **not one of the seven core tables**.

It combines:

- `searches`
- `search_sessions`
- `users`
- `experiment_assignments`
- `search_results`

to expose search-level success information for descriptive analysis.

Its purpose is to make the SSR definition reusable and transparent without duplicating the quality-click logic across multiple SQL queries.

---

# Design Notes

### Why `experiment_assignments` is separate

Experiment assignment is kept separate from user attributes because assignment is an experiment-level fact, while user attributes describe the user.

This also allows the same user population to participate in different experiments with separate assignments.

### Why `business_events` exists

The table provides an event-level representation of important business actions such as clicks, dwell, reformulation, and success.

It allows PRYVIA to demonstrate event-based analytical modeling while keeping the architecture entirely PostgreSQL + Python.

### Why `search_results` is separate from `searches`

A single search can return multiple ranked results.

Keeping results at their own grain makes it possible to analyze:

- ranking position
- relevance
- clicks
- dwell
- return behavior

without flattening multiple results into a single search row.

---

# Core Data Flow

The complete PRYVIA data model can be understood as:

```text
USER
  ↓
EXPERIMENT ASSIGNMENT
  ↓
SEARCH SESSION
  ↓
SEARCH
  ↓
RANKED RESULTS
  ↓
CLICK / DWELL / REFORMULATION / SUCCESS
  ↓
ANALYTICAL METRICS
  ↓
STATISTICAL EVIDENCE
  ↓
EXPERIMENT DECISION
```

This data model supports the complete PRYVIA experimentation workflow while keeping each table at a clear and explainable grain.
