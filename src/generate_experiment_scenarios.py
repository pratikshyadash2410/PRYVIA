"""
PRYVIA - Scenario-Aware Experiment Generator
Phase 3.x

Generates four behaviour-first A/B experiment scenarios.

Important:
- Randomization is at USER level and is sticky.
- SSR is generated from actual simulated behaviour.
- Ranking quality affects which relevance values reach high ranks.
- Click -> dwell -> reformulation -> success are downstream behaviours.
- No final metric is manually overwritten.
- Experiment 2 intentionally has a smaller exposed sample so that
  the existing statistical-analysis layer can correctly identify it
  as underpowered and recommend RUN FOLLOW-UP.

Experiments:
    1. Clear winner
    2. Inconclusive / underpowered
    3. Segment signal
    4. SSR improvement with latency guardrail breach
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

USERS_PER_EXPERIMENT = 3000
RESULTS_PER_SEARCH = 5

# Experiment 2 deliberately exposes fewer users.
# The remaining users exist in the cohort but are not assigned
# to the experiment, so they do not contribute to experiment metrics.
EXPERIMENT_2_EXPOSED_USERS = 1000

EXPERIMENT_START = datetime(2026, 9, 1)
EXPERIMENT_END = datetime(2026, 9, 30)

REFORMULATION_WINDOW_SECONDS = 300
MIN_SUCCESS_DWELL_SECONDS = 30

OUTPUT_DIR = Path(__file__).resolve().parent


# ============================================================
# EXPERIMENT SCENARIOS
# ============================================================

SCENARIOS = {
    # ========================================================
    # EXPERIMENT 1 ΓÇö CLEAR WINNER
    # ========================================================
    1: {
        "name": "Clear winner",

        # Imperfect baseline ranking.
        # A large amount of ranking noise means relevant results
        # are sometimes pushed below less relevant results.
        "control_relevance_weight": 0.20,
        "control_quality_weight": 0.20,
        "control_noise_weight": 0.60,

        # Treatment strongly prioritizes actual relevance.
        # This is a genuine ranking intervention that should
        # improve downstream user behaviour.
        "treatment_relevance_weight": 0.95,
        "treatment_quality_weight": 0.04,
        "treatment_noise_weight": 0.01,

        "mobile_treatment_relevance_weight": None,
        "desktop_treatment_relevance_weight": None,

        "latency_add_ms": 0,
    },


    # ========================================================
    # EXPERIMENT 2 ΓÇö INCONCLUSIVE / UNDERPOWERED
    # ========================================================
    2: {
        "name": "Inconclusive / underpowered",

        # Almost identical ranking algorithms.
        # Any observed difference should therefore be small.
        "control_relevance_weight": 0.60,
        "control_quality_weight": 0.25,
        "control_noise_weight": 0.15,

        "treatment_relevance_weight": 0.62,
        "treatment_quality_weight": 0.24,
        "treatment_noise_weight": 0.14,

        "mobile_treatment_relevance_weight": None,
        "desktop_treatment_relevance_weight": None,

        "latency_add_ms": 0,
    },


   # ========================================================
    # EXPERIMENT 3 ΓÇö SEGMENT SIGNAL
    # ========================================================
    3: {
        "name": "Segment signal",

        # ----------------------------------------------------
        # CONTROL
        # ----------------------------------------------------
        # Same baseline ranking for everyone.
        "control_relevance_weight": 0.45,
        "control_quality_weight": 0.05,
        "control_noise_weight": 0.50,

        # ----------------------------------------------------
        # TREATMENT BASELINE
        # ----------------------------------------------------
        # IMPORTANT:
        # Treatment is IDENTICAL to Control for Desktop.
        #
        # Therefore Desktop should have approximately:
        #
        #     Treatment Γëê Control
        #
        # This isolates the experiment effect to Mobile.
        # ----------------------------------------------------
        "treatment_relevance_weight": 0.45,
        "treatment_quality_weight": 0.05,
        "treatment_noise_weight": 0.50,

        # ----------------------------------------------------
        # MOBILE TREATMENT
        # ----------------------------------------------------
        # Mobile gets the genuinely improved ranking:
        #
        #     rank primarily by relevance
        #
        # This should create the segment signal.
        # ----------------------------------------------------
        "mobile_treatment_relevance_weight": 1.00,

        # No extra quality/noise for the Mobile override.
        #
        # NOTE:
        # generate_results() currently only overrides the
        # relevance weight for Mobile. Therefore the base
        # treatment quality/noise values remain active.
        #
        # To make Mobile truly pure-relevance, we need the
        # generator itself to support the Mobile quality/noise
        # override.
        #
        # We handle that below with values that make the
        # remaining terms negligible.
        "treatment_quality_weight": 0.00,
        "treatment_noise_weight": 0.00,

        # Desktop must stay identical to Control.
        "desktop_treatment_relevance_weight": 0.45,

        "latency_add_ms": 0,
    },


    # ========================================================
    # EXPERIMENT 4 ΓÇö GUARDRAIL VIOLATION
    # ========================================================
    4: {
        "name": "Guardrail violation",

        # ----------------------------------------------------
        # Make Control deliberately noisy.
        #
        # This creates a strong enough ranking-quality gap so
        # Treatment produces a statistically significant SSR win.
        # ----------------------------------------------------
        "control_relevance_weight": 0.10,
        "control_quality_weight": 0.10,
        "control_noise_weight": 0.80,

        # Strong relevance-based Treatment ranking.
        "treatment_relevance_weight": 1.10,
        "treatment_quality_weight": 0.00,
        "treatment_noise_weight": 0.00,

        "mobile_treatment_relevance_weight": None,
        "desktop_treatment_relevance_weight": None,

        # Genuine technical cost.
        # This must remain in the search-generation layer.
        "latency_add_ms": 90,
    },
}

# ============================================================
# RANDOMNESS
# ============================================================

def seeded_rng(seed: int) -> random.Random:
    """Create a deterministic Python RNG."""
    return random.Random(seed)


# ============================================================
# USERS
# ============================================================

def generate_users(experiment_id: int) -> pd.DataFrame:
    """Generate an independent 3,000-user cohort."""

    rng = seeded_rng(RANDOM_SEED + experiment_id)

    start_id = (
        100001
        + (experiment_id - 1) * USERS_PER_EXPERIMENT
    )

    rows = []

    for user_id in range(
        start_id,
        start_id + USERS_PER_EXPERIMENT,
    ):

        user_type = rng.choices(
            ["New", "Returning"],
            weights=[30, 70],
            k=1,
        )[0]

        device_type = rng.choices(
            ["Mobile", "Desktop"],
            weights=[65, 35],
            k=1,
        )[0]

        country = rng.choices(
            [
                "India",
                "United States",
                "United Kingdom",
                "Canada",
                "Australia",
            ],
            weights=[70, 10, 8, 6, 6],
            k=1,
        )[0]

        activity_level = rng.choices(
            ["Low", "Medium", "High"],
            weights=[40, 40, 20],
            k=1,
        )[0]

        signup_date = (
            EXPERIMENT_START.date()
            - timedelta(
                days=rng.randint(0, 180)
            )
        )

        rows.append(
            {
                "user_id": user_id,
                "user_type": user_type,
                "device_type": device_type,
                "country": country,
                "activity_level": activity_level,
                "signup_date": signup_date,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# ASSIGNMENTS
# ============================================================

def generate_assignments(
    users: pd.DataFrame,
    experiment_id: int,
) -> pd.DataFrame:
    """
    Sticky user-level randomization.

    Experiment 2 intentionally exposes only 1,000 users.
    This allows the existing power-analysis code to identify
    the experiment as underpowered.
    """

    rng = seeded_rng(
        RANDOM_SEED + 100 + experiment_id
    )

    users_for_experiment = users.copy()

    if experiment_id == 2:

        # Deterministically select the exposed population.
        exposed_users = users.sample(
            n=EXPERIMENT_2_EXPOSED_USERS,
            random_state=RANDOM_SEED + 2000,
        )

        users_for_experiment = (
            exposed_users
            .sort_values("user_id")
            .reset_index(drop=True)
        )

    rows = []

    for user_id in users_for_experiment["user_id"]:

        rows.append(
            {
                "assignment_id": len(rows) + 1,
                "experiment_id": experiment_id,
                "user_id": int(user_id),
                "variant": rng.choice(
                    ["Control", "Treatment"]
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# SESSIONS
# ============================================================

def generate_sessions(
    users: pd.DataFrame,
    assignments: pd.DataFrame,
    experiment_id: int,
) -> pd.DataFrame:
    """
    Generate sessions only for users exposed to the experiment.

    This is important for Experiment 2:
    unassigned cohort users do not generate experiment traffic.
    """

    rng = seeded_rng(
        RANDOM_SEED + 200 + experiment_id
    )

    exposed_user_ids = set(
        assignments["user_id"].astype(int)
    )

    exposed_users = users[
        users["user_id"].isin(exposed_user_ids)
    ].copy()

    sessions_by_activity = {
        "Low": (1, 2),
        "Medium": (2, 4),
        "High": (4, 6),
    }

    session_id = (
        100001
        + (experiment_id - 1) * 100000
    )

    rows = []

    for _, user in exposed_users.iterrows():

        min_sessions, max_sessions = (
            sessions_by_activity[
                user["activity_level"]
            ]
        )

        number_of_sessions = rng.randint(
            min_sessions,
            max_sessions,
        )

        for _ in range(number_of_sessions):

            days_from_start = rng.randint(
                0,
                (
                    EXPERIMENT_END
                    - EXPERIMENT_START
                ).days,
            )

            session_date = (
                EXPERIMENT_START
                + timedelta(
                    days=days_from_start
                )
            )

            session_start = session_date.replace(
                hour=rng.randint(8, 22),
                minute=rng.randint(0, 59),
                second=rng.randint(0, 59),
            )

            session_end = (
                session_start
                + timedelta(
                    minutes=rng.randint(2, 20)
                )
            )

            rows.append(
                {
                    "session_id": session_id,
                    "user_id": int(user["user_id"]),
                    "session_start": session_start,
                    "session_end": session_end,
                }
            )

            session_id += 1

    return pd.DataFrame(rows)


# ============================================================
# QUERY DATA
# ============================================================

QUERY_CATEGORIES = {

    "Electronics": [
        "wireless headphones",
        "gaming laptop",
        "bluetooth speaker",
        "smart watch",
        "phone charger",
    ],

    "Fashion": [
        "running shoes",
        "black dress",
        "men's jacket",
        "summer shirt",
        "casual sneakers",
    ],

    "Home": [
        "office chair",
        "table lamp",
        "kitchen storage",
        "bedroom curtains",
        "coffee table",
    ],

    "Beauty": [
        "face moisturizer",
        "sunscreen",
        "shampoo",
        "lip balm",
        "face wash",
    ],
}


# ============================================================
# SEARCHES
# ============================================================

def generate_searches(
    sessions: pd.DataFrame,
    assignments: pd.DataFrame,
    scenario: dict,
    experiment_id: int,
) -> pd.DataFrame:
    """Generate searches and realistic latency/error behaviour."""

    rng = seeded_rng(
        RANDOM_SEED + 300 + experiment_id
    )

    user_variant = (
        assignments
        .set_index("user_id")["variant"]
        .to_dict()
    )

    search_id = (
        100001
        + (experiment_id - 1) * 100000
    )

    rows = []

    for _, session in sessions.iterrows():

        number_of_searches = rng.choices(
            [1, 2, 3],
            weights=[55, 30, 15],
            k=1,
        )[0]

        session_seconds = int(
            (
                session["session_end"]
                - session["session_start"]
            ).total_seconds()
        )

        user_id = int(session["user_id"])
        variant = user_variant[user_id]

        for _ in range(number_of_searches):

            category = rng.choice(
                list(QUERY_CATEGORIES.keys())
            )

            query_text = rng.choice(
                QUERY_CATEGORIES[category]
            )

            offset_seconds = (
                0
                if number_of_searches == 1
                else rng.randint(
                    0,
                    max(1, session_seconds),
                )
            )

            timestamp = (
                session["session_start"]
                + timedelta(
                    seconds=offset_seconds
                )
            )

            # Deterministic common latency.
            # Treatment gets the scenario-specific penalty.
            base_latency = (
                390
                + ((int(search_id) * 37) % 121)
            )

            latency = (
                base_latency
                + (
                    scenario["latency_add_ms"]
                    if variant == "Treatment"
                    else 0
                )
            )

            search_error = (
                rng.random() < 0.03
            )

            rows.append(
                {
                    "search_id": search_id,
                    "session_id": int(
                        session["session_id"]
                    ),
                    "query_text": query_text,
                    "query_category": category,
                    "search_timestamp": timestamp,
                    "search_latency_ms": max(
                        100,
                        latency,
                    ),
                    "search_error": search_error,
                }
            )

            search_id += 1

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "session_id",
                "search_timestamp",
                "search_id",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# RANKING
# ============================================================

# src/generate_experiment_scenarios.py

def generate_results(
    searches: pd.DataFrame,
    sessions: pd.DataFrame,
    assignments: pd.DataFrame,
    users: pd.DataFrame,
    scenario: dict,
    experiment_id: int,
) -> pd.DataFrame:
    """
    Generate five ranked results per search.

    Experiment 3 is deliberately heterogeneous:

        Mobile:
            Control   = baseline ranking
            Treatment = relevance-first ranking

        Desktop:
            Control   = baseline ranking
            Treatment = EXACTLY the same baseline ranking

    Therefore:
        Mobile should show a treatment improvement.
        Desktop should remain approximately unchanged.
    """

    rng = seeded_rng(
        RANDOM_SEED + 400 + experiment_id
    )

    # --------------------------------------------------------
    # Lookup maps
    # --------------------------------------------------------

    session_user = (
        sessions
        .set_index("session_id")["user_id"]
        .to_dict()
    )

    user_variant = (
        assignments
        .set_index("user_id")["variant"]
        .to_dict()
    )

    user_device = (
        users
        .set_index("user_id")["device_type"]
        .to_dict()
    )

    result_id = (
        100001
        + (experiment_id - 1) * 100000
    )

    rows = []

    # ========================================================
    # GENERATE RESULTS FOR EACH SEARCH
    # ========================================================

    for _, search in searches.iterrows():

        user_id = int(
            session_user[
                int(search["session_id"])
            ]
        )

        variant = user_variant[user_id]
        device = user_device[user_id]

        candidates = []

        # ----------------------------------------------------
        # Generate 5 candidate products.
        # ----------------------------------------------------

        for _ in range(RESULTS_PER_SEARCH):

            # Intrinsic relevance of the candidate.
            relevance = round(
                rng.betavariate(5, 2),
                3,
            )

            # Historical quality is a secondary ranking signal.
            historical_quality = (
                rng.betavariate(5, 2)
            )

            # Random ranking noise represents imperfections
            # in the ranking system.
            random_noise = rng.gauss(
                0,
                1,
            )

            candidates.append(
                {
                    "result_id": result_id,

                    "search_id": int(
                        search["search_id"]
                    ),

                    "relevance_score": relevance,

                    "historical_quality":
                        historical_quality,

                    "ranking_noise":
                        random_noise,
                }
            )

            result_id += 1

        # ====================================================
        # DEFAULT RANKING = CONTROL
        # ====================================================

        relevance_weight = (
            scenario[
                "control_relevance_weight"
            ]
        )

        quality_weight = (
            scenario[
                "control_quality_weight"
            ]
        )

        noise_weight = (
            scenario[
                "control_noise_weight"
            ]
        )

        # ====================================================
        # NORMAL TREATMENT RANKING
        # ====================================================

        if variant == "Treatment":

            relevance_weight = (
                scenario[
                    "treatment_relevance_weight"
                ]
            )

            quality_weight = (
                scenario[
                    "treatment_quality_weight"
                ]
            )

            noise_weight = (
                scenario[
                    "treatment_noise_weight"
                ]
            )

        # ====================================================
        # EXPERIMENT 3 ΓÇö SEGMENT-SPECIFIC INTERVENTION
        # ====================================================

        if experiment_id == 3:

            # ------------------------------------------------
            # DESKTOP
            # ------------------------------------------------
            #
            # Treatment is EXACTLY the same as Control.
            #
            # This is intentional.
            # ------------------------------------------------

            if device == "Desktop":

                relevance_weight = (
                    scenario[
                        "control_relevance_weight"
                    ]
                )

                quality_weight = (
                    scenario[
                        "control_quality_weight"
                    ]
                )

                noise_weight = (
                    scenario[
                        "control_noise_weight"
                    ]
                )

            # ------------------------------------------------
            # MOBILE TREATMENT
            # ------------------------------------------------
            #
            # Only Mobile Treatment receives the improved
            # relevance-first ranking algorithm.
            # ------------------------------------------------

            elif (
                device == "Mobile"
                and variant == "Treatment"
            ):

                relevance_weight = 1.00
                quality_weight = 0.00
                noise_weight = 0.00

        # ====================================================
        # CALCULATE RANKING SCORE
        # ====================================================

        for candidate in candidates:

            candidate["ranking_score"] = (
                relevance_weight
                * candidate[
                    "relevance_score"
                ]

                + quality_weight
                * candidate[
                    "historical_quality"
                ]

                + noise_weight
                * candidate[
                    "ranking_noise"
                ]
            )

        # ====================================================
        # RANK RESULTS
        # ====================================================

        candidates.sort(
            key=lambda x: x[
                "ranking_score"
            ],
            reverse=True,
        )

        # ====================================================
        # SAVE DISPLAYED RESULTS
        # ====================================================

        for rank_position, candidate in enumerate(
            candidates,
            start=1,
        ):

            rows.append(
                {
                    "result_id": candidate[
                        "result_id"
                    ],

                    "search_id": candidate[
                        "search_id"
                    ],

                    "rank_position":
                        rank_position,

                    "result_type":
                        "product",

                    "relevance_score":
                        candidate[
                            "relevance_score"
                        ],
                }
            )

    return pd.DataFrame(rows)




# ============================================================
# CLICK SIMULATION
# ============================================================

def simulate_clicks(
    results: pd.DataFrame,
    experiment_id: int,
) -> pd.DataFrame:
    """
    Simulate zero-or-one click per search.

    IMPORTANT:
    Click propensity is based on the ACTUAL TOP RESULT after
    ranking, not on an arbitrary pre-ranking row.

    This makes ranking quality causally matter.
    """

    rng = seeded_rng(
        RANDOM_SEED + 500 + experiment_id
    )

    results = results.copy()

    results["clicked"] = False

    for search_id, group in results.groupby(
        "search_id",
        sort=False,
    ):

        # Sort by actual displayed rank.
        group = group.sort_values(
            "rank_position"
        )

        top_relevance = float(
            group.iloc[0]["relevance_score"]
        )

        # Search-level probability of clicking something.
        #
        # Better top result -> higher probability of engagement.
        click_propensity = min(
            0.95,
            max(
                0.55,
                0.62
                + 0.35 * top_relevance,
            ),
        )

        if rng.random() >= click_propensity:
            continue

        # Once the user decides to click, high-ranked and
        # relevant results are much more likely to receive it.
        position_weight = {
            1: 6.0,
            2: 3.0,
            3: 1.7,
            4: 0.9,
            5: 0.5,
        }

        weights = []

        for _, row in group.iterrows():

            relevance = float(
                row["relevance_score"]
            )

            rank = int(
                row["rank_position"]
            )

            weight = (
                position_weight[rank]
                * (
                    0.35
                    + relevance
                )
            )

            weights.append(weight)

        selected_index = rng.choices(
            list(group.index),
            weights=weights,
            k=1,
        )[0]

        results.at[
            selected_index,
            "clicked",
        ] = True

    return results


# ============================================================
# DWELL SIMULATION
# ============================================================

def simulate_dwell(
    results: pd.DataFrame,
    experiment_id: int,
) -> pd.DataFrame:
    """
    Simulate dwell time from relevance and rank.

    High relevance at a high position creates longer dwell,
    which then feeds into successful search.
    """

    rng = seeded_rng(
        RANDOM_SEED + 600 + experiment_id
    )

    results = results.copy()

    dwell_times = []
    returned = []

    for _, row in results.iterrows():

        if not row["clicked"]:

            dwell_times.append(0.0)
            returned.append(False)

            continue

        relevance = float(
            row["relevance_score"]
        )

        rank = int(
            row["rank_position"]
        )

        # High relevance and better rank increase expected dwell.
        expected_dwell = (
            28
            + 48 * relevance
            + max(0, 5 - rank) * 3
        )

        dwell = rng.normalvariate(
            expected_dwell,
            9,
        )

        dwell = max(
            5,
            min(
                180,
                dwell,
            ),
        )

        dwell = round(
            dwell,
            1,
        )

        # Short dwell creates a return-to-search event.
        return_to_search = (
            dwell < MIN_SUCCESS_DWELL_SECONDS
            and rng.random() < 0.70
        )

        dwell_times.append(dwell)
        returned.append(return_to_search)

    results[
        "dwell_time_seconds"
    ] = dwell_times

    results[
        "returned_to_search"
    ] = returned

    return results[
        [
            "result_id",
            "search_id",
            "rank_position",
            "result_type",
            "relevance_score",
            "clicked",
            "dwell_time_seconds",
            "returned_to_search",
        ]
    ]


# ============================================================
# REFORMULATION
# ============================================================

def detect_reformulation(
    searches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect another search within 300 seconds in the same session.
    """

    df = searches.copy()

    df["search_timestamp"] = pd.to_datetime(
        df["search_timestamp"]
    )

    df = df.sort_values(
        [
            "session_id",
            "search_timestamp",
            "search_id",
        ]
    ).reset_index(drop=True)

    previous_timestamp = (
        df.groupby("session_id")[
            "search_timestamp"
        ].shift(1)
    )

    seconds_since_previous = (
        df["search_timestamp"]
        - previous_timestamp
    ).dt.total_seconds()

    df["is_reformulation"] = (
        seconds_since_previous.between(
            0,
            REFORMULATION_WINDOW_SECONDS,
            inclusive="both",
        )
    )

    df.loc[
        previous_timestamp.isna(),
        "is_reformulation",
    ] = False

    return df[
        [
            "search_id",
            "session_id",
            "query_text",
            "query_category",
            "search_timestamp",
            "search_latency_ms",
            "search_error",
            "is_reformulation",
        ]
    ].copy()


# ============================================================
# SUCCESS CALCULATION
# ============================================================

def calculate_success(
    results: pd.DataFrame,
    reformulations: pd.DataFrame,
) -> pd.DataFrame:
    """
    Search is successful when:
        1. user clicked a result
        2. dwell >= 30 seconds
        3. search was not a reformulation
    """

    quality = results[
        (results["clicked"] == True)
        & (
            results[
                "dwell_time_seconds"
            ]
            >= MIN_SUCCESS_DWELL_SECONDS
        )
    ]

    quality_by_search = (
        quality
        .groupby("search_id")
        .size()
        .reset_index(
            name="quality_click_count"
        )
    )

    output = reformulations[
        [
            "search_id",
            "session_id",
            "query_text",
            "query_category",
            "search_timestamp",
            "is_reformulation",
        ]
    ].copy()

    output = output.merge(
        quality_by_search,
        on="search_id",
        how="left",
    )

    output[
        "quality_click_count"
    ] = (
        output[
            "quality_click_count"
        ]
        .fillna(0)
        .astype(int)
    )

    output[
        "has_quality_click"
    ] = (
        output[
            "quality_click_count"
        ] > 0
    )

    output[
        "successful_search"
    ] = (
        output["has_quality_click"]
        & (
            ~output[
                "is_reformulation"
            ]
        )
    )

    return output


# ============================================================
# BUSINESS EVENTS
# ============================================================

def generate_business_events(
    results: pd.DataFrame,
    reformulations: pd.DataFrame,
    success: pd.DataFrame,
) -> pd.DataFrame:
    """Generate business events from observed behaviour."""

    events = []

    # Click events.
    for _, row in results[
        results["clicked"] == True
    ].iterrows():

        events.append(
            {
                "search_id": int(
                    row["search_id"]
                ),
                "event_type": "click",
            }
        )

    # Dwell events.
    for _, row in results[
        results[
            "dwell_time_seconds"
        ] > 0
    ].iterrows():

        events.append(
            {
                "search_id": int(
                    row["search_id"]
                ),
                "event_type": "dwell",
            }
        )

    # Reformulation events.
    for _, row in reformulations[
        reformulations[
            "is_reformulation"
        ] == True
    ].iterrows():

        events.append(
            {
                "search_id": int(
                    row["search_id"]
                ),
                "event_type": "reformulation",
            }
        )

    # Successful-search events.
    for _, row in success[
        success[
            "successful_search"
        ] == True
    ].iterrows():

        events.append(
            {
                "search_id": int(
                    row["search_id"]
                ),
                "event_type": "success",
            }
        )

    events_df = pd.DataFrame(
        events
    )

    # Add timestamps BEFORE assigning event IDs.
    # The timestamp lookup is one row per search, and event IDs are
    # assigned only after the final event row set is constructed.
    search_times = (
        reformulations[
            [
                "search_id",
                "search_timestamp",
            ]
        ]
        .drop_duplicates(
            subset=["search_id"],
            keep="first",
        )
    )

    events_df = events_df.merge(
        search_times,
        on="search_id",
        how="left",
        validate="many_to_one",
    )

    events_df.rename(
        columns={
            "search_timestamp":
                "event_timestamp"
        },
        inplace=True,
    )

    events_df.insert(
        0,
        "event_id",
        range(
            1,
            len(events_df) + 1,
        ),
    )

    return events_df[
        [
            "event_id",
            "search_id",
            "event_type",
            "event_timestamp",
        ]
    ]


# ============================================================
# MAIN PIPELINE
# ============================================================

def main() -> None:
    """Generate all four scenarios."""

    all_users = []
    all_assignments = []
    all_sessions = []
    all_searches = []
    all_results = []
    all_reformulations = []
    all_success = []
    all_events = []

    scenario_summary = []

    for experiment_id, scenario in SCENARIOS.items():

        print(
            f"\nGenerating Experiment "
            f"{experiment_id}: "
            f"{scenario['name']}"
        )

        # ----------------------------------------------------
        # 1. Users
        # ----------------------------------------------------

        users = generate_users(
            experiment_id
        )

        # ----------------------------------------------------
        # 2. Sticky assignments
        # ----------------------------------------------------

        assignments = generate_assignments(
            users,
            experiment_id,
        )

        # ----------------------------------------------------
        # 3. Sessions
        # ----------------------------------------------------

        sessions = generate_sessions(
            users,
            assignments,
            experiment_id,
        )

        # ----------------------------------------------------
        # 4. Searches
        # ----------------------------------------------------

        searches = generate_searches(
            sessions,
            assignments,
            scenario,
            experiment_id,
        )

        # ----------------------------------------------------
        # 5. Ranking
        # ----------------------------------------------------

        results = generate_results(
            searches,
            sessions,
            assignments,
            users,
            scenario,
            experiment_id,
        )

        # ----------------------------------------------------
        # 6. Click
        # ----------------------------------------------------

        results = simulate_clicks(
            results,
            experiment_id,
        )

        # ----------------------------------------------------
        # 7. Dwell
        # ----------------------------------------------------

        results = simulate_dwell(
            results,
            experiment_id,
        )

        # ----------------------------------------------------
        # 8. Reformulation
        # ----------------------------------------------------

        reformulations = (
            detect_reformulation(
                searches
            )
        )

        # ----------------------------------------------------
        # 9. Success
        # ----------------------------------------------------

        success = calculate_success(
            results,
            reformulations,
        )

        # ----------------------------------------------------
        # 10. Business events
        # ----------------------------------------------------

        events = generate_business_events(
            results,
            reformulations,
            success,
        )

        all_users.append(users)
        all_assignments.append(assignments)
        all_sessions.append(sessions)
        all_searches.append(searches)
        all_results.append(results)
        all_reformulations.append(
            reformulations
        )
        all_success.append(success)
        all_events.append(events)

        # ----------------------------------------------------
        # Scenario summary
        # ----------------------------------------------------

        control_users = (
            assignments["variant"]
            == "Control"
        ).sum()

        treatment_users = (
            assignments["variant"]
            == "Treatment"
        ).sum()

        control_user_ids = set(
            assignments.loc[
                assignments["variant"]
                == "Control",
                "user_id",
            ]
        )

        treatment_user_ids = set(
            assignments.loc[
                assignments["variant"]
                == "Treatment",
                "user_id",
            ]
        )

        session_user_map = (
            sessions
            .set_index("session_id")[
                "user_id"
            ]
            .to_dict()
        )

        search_users = searches[
            "session_id"
        ].map(
            session_user_map
        )

        control_mask = (
            search_users.isin(
                control_user_ids
            )
        )

        treatment_mask = (
            search_users.isin(
                treatment_user_ids
            )
        )

        control_search_ids = set(
            searches.loc[
                control_mask,
                "search_id",
            ]
        )

        treatment_search_ids = set(
            searches.loc[
                treatment_mask,
                "search_id",
            ]
        )

        control_success = success[
            success["search_id"].isin(
                control_search_ids
            )
        ]

        treatment_success = success[
            success["search_id"].isin(
                treatment_search_ids
            )
        ]

        scenario_summary.append(
            {
                "experiment_id":
                    experiment_id,

                "scenario":
                    scenario["name"],

                "users":
                    len(users),

                "assigned_users":
                    len(assignments),

                "control_users":
                    control_users,

                "treatment_users":
                    treatment_users,

                "sessions":
                    len(sessions),

                "searches":
                    len(searches),

                "results":
                    len(results),

                "clicks":
                    int(
                        results[
                            "clicked"
                        ].sum()
                    ),

                "successful_searches":
                    int(
                        success[
                            "successful_search"
                        ].sum()
                    ),

                "ssr":
                    float(
                        success[
                            "successful_search"
                        ].mean()
                    ),

                "control_ssr":
                    float(
                        control_success[
                            "successful_search"
                        ].mean()
                    ),

                "treatment_ssr":
                    float(
                        treatment_success[
                            "successful_search"
                        ].mean()
                    ),

                "latency_control_median":
                    float(
                        searches.loc[
                            control_mask,
                            "search_latency_ms",
                        ].median()
                    ),

                "latency_treatment_median":
                    float(
                        searches.loc[
                            treatment_mask,
                            "search_latency_ms",
                        ].median()
                    ),
            }
        )

    # ========================================================
    # CONCATENATE
    # ========================================================

    users_final = pd.concat(
        all_users,
        ignore_index=True,
    )

    assignments_final = pd.concat(
        all_assignments,
        ignore_index=True,
    )

    # Global primary-key uniqueness.
    assignments_final[
        "assignment_id"
    ] = range(
        1,
        len(assignments_final) + 1,
    )

    sessions_final = pd.concat(
        all_sessions,
        ignore_index=True,
    )

    searches_final = pd.concat(
        all_searches,
        ignore_index=True,
    )

    results_final = pd.concat(
        all_results,
        ignore_index=True,
    )

    reformulations_final = pd.concat(
        all_reformulations,
        ignore_index=True,
    )

    success_final = pd.concat(
        all_success,
        ignore_index=True,
    )

    events_final = pd.concat(
        all_events,
        ignore_index=True,
    )

    # Event IDs are unique only within each experiment while the
    # individual event DataFrames are being generated. After combining
    # all four experiments, assign one GLOBAL event_id sequence.
    # This guarantees uniqueness across the final business_events table.
    events_final["event_id"] = range(
        1,
        len(events_final) + 1,
    )

    # ========================================================
    # WRITE CSV FILES
    # ========================================================

    users_final.to_csv(
        OUTPUT_DIR
        / "users_prototype.csv",
        index=False,
    )

    assignments_final.to_csv(
        OUTPUT_DIR
        / "experiment_assignments_prototype.csv",
        index=False,
    )

    sessions_final.to_csv(
        OUTPUT_DIR
        / "search_sessions_prototype.csv",
        index=False,
    )

    searches_final.to_csv(
        OUTPUT_DIR
        / "searches_prototype.csv",
        index=False,
    )

    results_final.to_csv(
        OUTPUT_DIR
        / "search_results_final.csv",
        index=False,
    )

    results_final.to_csv(
        OUTPUT_DIR
        / "search_results_prototype.csv",
        index=False,
    )

    reformulations_final.to_csv(
        OUTPUT_DIR
        / "searches_with_reformulation.csv",
        index=False,
    )

    success_final.to_csv(
        OUTPUT_DIR
        / "search_success_prototype.csv",
        index=False,
    )

    events_final.to_csv(
        OUTPUT_DIR
        / "business_events_prototype.csv",
        index=False,
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "PRYVIA SCENARIO GENERATION COMPLETE"
    )
    print("=" * 70)

    print("\nDataset sizes:")

    print(
        f"Users:              "
        f"{len(users_final):,}"
    )

    print(
        f"Assignments:        "
        f"{len(assignments_final):,}"
    )

    print(
        f"Sessions:           "
        f"{len(sessions_final):,}"
    )

    print(
        f"Searches:           "
        f"{len(searches_final):,}"
    )

    print(
        f"Results:            "
        f"{len(results_final):,}"
    )

    print(
        f"Reformulation rows: "
        f"{len(reformulations_final):,}"
    )

    print(
        f"Success rows:       "
        f"{len(success_final):,}"
    )

    print(
        f"Business events:    "
        f"{len(events_final):,}"
    )

    print("\nScenario summary:")

    summary_df = pd.DataFrame(
        scenario_summary
    )

    print(
        summary_df[
            [
                "experiment_id",
                "scenario",
                "users",
                "assigned_users",
                "control_users",
                "treatment_users",
                "searches",
                "ssr",
                "control_ssr",
                "treatment_ssr",
                "latency_control_median",
                "latency_treatment_median",
            ]
        ].to_string(
            index=False
        )
    )

    # ========================================================
    # STRUCTURAL VALIDATION
    # ========================================================

    assert users_final[
        "user_id"
    ].is_unique

    assert assignments_final[
        "assignment_id"
    ].is_unique

    assert assignments_final[
        "user_id"
    ].isin(
        users_final["user_id"]
    ).all()

    assert sessions_final[
        "session_id"
    ].is_unique

    assert sessions_final[
        "user_id"
    ].isin(
        users_final["user_id"]
    ).all()

    assert searches_final[
        "search_id"
    ].is_unique

    assert searches_final[
        "session_id"
    ].isin(
        sessions_final["session_id"]
    ).all()

    assert results_final[
        "result_id"
    ].is_unique

    assert results_final[
        "search_id"
    ].isin(
        searches_final["search_id"]
    ).all()

    assert reformulations_final[
        "search_id"
    ].is_unique

    assert success_final[
        "search_id"
    ].is_unique

    assert success_final[
        "search_id"
    ].isin(
        searches_final["search_id"]
    ).all()

    assert events_final[
        "search_id"
    ].isin(
        searches_final["search_id"]
    ).all()

    # Every user is assigned at most once.
    assert not (
        assignments_final
        .duplicated(
            subset=[
                "experiment_id",
                "user_id",
            ]
        )
        .any()
    )

    # Every experiment has users.
    assignment_counts = (
        assignments_final
        .groupby("experiment_id")[
            "user_id"
        ]
        .nunique()
    )

    assert (
        assignment_counts > 0
    ).all()

    # Experiment 2 must be intentionally smaller.
    assert (
        assignment_counts.loc[2]
        == EXPERIMENT_2_EXPOSED_USERS
    )

    print("\nValidation: PASS")

    print(
        "All IDs are unique."
    )

    print(
        "All foreign-key relationships "
        "are valid."
    )

    print(
        "SSR is generated from "
        "user behaviour."
    )

    print(
        "Experiment 2 is intentionally "
        "underpowered by exposure."
    )

    print(
        "\nNEXT: run "
        "validate_experiment_scenarios.py"
    )

    print(
        "Do NOT import into PostgreSQL yet."
    )


if __name__ == "__main__":
    main()
