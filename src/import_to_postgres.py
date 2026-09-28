import os
import pandas as pd
import psycopg


# ============================================================
# PRYVIA — POSTGRESQL DATA IMPORT
# ============================================================
# Loads the validated, frozen PRYVIA dataset into PostgreSQL.
#
# Target database:
#     pryvia_analytics
#
# Target tables:
#     1. users
#     2. experiments
#     3. experiment_assignments
#     4. search_sessions
#     5. searches
#     6. search_results
#     7. business_events
#
# Important:
# - CSV files are NOT modified.
# - Import runs inside one transaction.
# - If anything fails, the transaction is rolled back.
# ============================================================


# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "pryvia_analytics",
    "user": "postgres",
    "password": os.environ.get("PRYVIA_DB_PASSWORD"),
}


# ============================================================
# 2. START
# ============================================================

print("=" * 70)
print("PRYVIA — POSTGRESQL DATA IMPORT")
print("=" * 70)


# ============================================================
# 3. LOAD CSV FILES
# ============================================================

print("\nLoading CSV files...")

users_df = pd.read_csv(
    "users_prototype.csv"
)

assignments_df = pd.read_csv(
    "experiment_assignments_prototype.csv"
)

sessions_df = pd.read_csv(
    "search_sessions_prototype.csv"
)

searches_df = pd.read_csv(
    "searches_prototype.csv"
)

reformulation_df = pd.read_csv(
    "searches_with_reformulation.csv"
)

results_df = pd.read_csv(
    "search_results_final.csv"
)

events_df = pd.read_csv(
    "business_events_prototype.csv"
)

print("[PASS] All CSV files loaded")


# ============================================================
# 4. EXPERIMENT METADATA
# ============================================================
# These four experiments correspond to the frozen scenarios:
#
# Experiment 1 → Clear winner
# Experiment 2 → Inconclusive / underpowered
# Experiment 3 → Segment signal
# Experiment 4 → Guardrail violation
#
# Experiment 2 intentionally has only 1,000 assigned users.
# ============================================================

experiments = [
    (
        1,
        "Clear winner",
        "2026-01-01",
        "2026-01-31",
        0.5000,
        "SSR",
    ),
    (
        2,
        "Inconclusive / underpowered",
        "2026-02-01",
        "2026-02-28",
        0.5000,
        "SSR",
    ),
    (
        3,
        "Segment signal",
        "2026-03-01",
        "2026-03-31",
        0.5000,
        "SSR",
    ),
    (
        4,
        "Guardrail violation",
        "2026-04-01",
        "2026-04-30",
        0.5000,
        "SSR",
    ),
]


# ============================================================
# 5. PREPARE DATA TYPES
# ============================================================

sessions_df["session_start"] = pd.to_datetime(
    sessions_df["session_start"]
)

sessions_df["session_end"] = pd.to_datetime(
    sessions_df["session_end"]
)

searches_df["search_timestamp"] = pd.to_datetime(
    searches_df["search_timestamp"]
)

reformulation_df["search_timestamp"] = pd.to_datetime(
    reformulation_df["search_timestamp"]
)

events_df["event_timestamp"] = pd.to_datetime(
    events_df["event_timestamp"]
)


# ============================================================
# 6. CREATE REFORMULATION LOOKUP
# ============================================================
# searches_prototype.csv does not contain is_reformulation.
#
# The final reformulation flag comes from:
# searches_with_reformulation.csv
#
# We use search_id as the lookup key.
# ============================================================

reformulation_lookup = dict(
    zip(
        reformulation_df["search_id"],
        reformulation_df["is_reformulation"],
    )
)


# Safety check: every search must have a reformulation flag.

missing_reformulation_ids = (
    set(searches_df["search_id"])
    - set(reformulation_lookup.keys())
)

if missing_reformulation_ids:

    raise ValueError(
        "Some searches do not have a reformulation flag: "
        f"{len(missing_reformulation_ids):,}"
    )

print("[PASS] Reformulation lookup prepared")


# ============================================================
# 7. DATABASE CONNECTION
# ============================================================

print("\nConnecting to PostgreSQL...")

if not DB_CONFIG["password"]:

    raise ValueError(
        "PRYVIA_DB_PASSWORD environment variable is not set."
    )


try:

    connection = psycopg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

    print(
        "[PASS] PostgreSQL connection established"
    )

except Exception as error:

    print(
        "[FAIL] PostgreSQL connection failed"
    )

    print(error)

    raise SystemExit(1)


# ============================================================
# 8. IMPORT EVERYTHING IN ONE TRANSACTION
# ============================================================

try:

    with connection:

        with connection.cursor() as cursor:

            # =================================================
            # 8.1 CLEAR EXISTING PROTOTYPE DATA
            # =================================================
            #
            # Child tables are listed first because of FK
            # relationships.
            #
            # The whole operation is inside the transaction.
            # =================================================

            print(
                "\n" + "-" * 70
            )

            print(
                "CLEARING EXISTING PROTOTYPE DATA"
            )

            print(
                "-" * 70
            )

            cursor.execute(
                """
                TRUNCATE TABLE
                    business_events,
                    search_results,
                    searches,
                    search_sessions,
                    experiment_assignments,
                    users,
                    experiments
                RESTART IDENTITY CASCADE;
                """
            )

            print(
                "[PASS] Existing data cleared"
            )


            # =================================================
            # 8.2 USERS
            # =================================================

            print("\nImporting users...")

            users_sql = """
                INSERT INTO users (
                    user_id,
                    user_type,
                    device_type,
                    country,
                    activity_level,
                    signup_date
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            user_records = [
                (
                    int(row["user_id"]),
                    row["user_type"],
                    row["device_type"],
                    row["country"],
                    row["activity_level"],
                    row["signup_date"],
                )
                for _, row in users_df.iterrows()
            ]

            cursor.executemany(
                users_sql,
                user_records,
            )

            print(
                f"[PASS] Users imported: "
                f"{len(user_records):,}"
            )


            # =================================================
            # 8.3 EXPERIMENTS
            # =================================================

            print("\nImporting experiments...")

            experiments_sql = """
                INSERT INTO experiments (
                    experiment_id,
                    experiment_name,
                    start_date,
                    end_date,
                    allocation_ratio,
                    primary_metric
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            cursor.executemany(
                experiments_sql,
                experiments,
            )

            print(
                f"[PASS] Experiments imported: "
                f"{len(experiments):,}"
            )


            # =================================================
            # 8.4 EXPERIMENT ASSIGNMENTS
            # =================================================
            #
            # assignment_id is generated by PostgreSQL identity.
            # Therefore we intentionally DO NOT insert it.
            # =================================================

            print(
                "\nImporting experiment assignments..."
            )

            assignments_sql = """
                INSERT INTO experiment_assignments (
                    experiment_id,
                    user_id,
                    variant
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
            """

            assignment_records = [
                (
                    int(row["experiment_id"]),
                    int(row["user_id"]),
                    row["variant"],
                )
                for _, row in assignments_df.iterrows()
            ]

            cursor.executemany(
                assignments_sql,
                assignment_records,
            )

            print(
                f"[PASS] Assignments imported: "
                f"{len(assignment_records):,}"
            )


            # =================================================
            # 8.5 SEARCH SESSIONS
            # =================================================

            print(
                "\nImporting search sessions..."
            )

            sessions_sql = """
                INSERT INTO search_sessions (
                    session_id,
                    user_id,
                    session_start,
                    session_end
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            session_records = [
                (
                    int(row["session_id"]),
                    int(row["user_id"]),
                    row["session_start"].to_pydatetime(),
                    (
                        row["session_end"].to_pydatetime()
                        if pd.notna(row["session_end"])
                        else None
                    ),
                )
                for _, row in sessions_df.iterrows()
            ]

            cursor.executemany(
                sessions_sql,
                session_records,
            )

            print(
                f"[PASS] Sessions imported: "
                f"{len(session_records):,}"
            )


            # =================================================
            # 8.6 SEARCHES
            # =================================================

            print("\nImporting searches...")

            searches_sql = """
                INSERT INTO searches (
                    search_id,
                    session_id,
                    query_text,
                    query_category,
                    search_timestamp,
                    search_latency_ms,
                    search_error,
                    is_reformulation
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            search_records = [
                (
                    int(row["search_id"]),
                    int(row["session_id"]),
                    row["query_text"],
                    row["query_category"],
                    row["search_timestamp"].to_pydatetime(),
                    int(row["search_latency_ms"]),
                    bool(row["search_error"]),
                    bool(
                        reformulation_lookup[
                            row["search_id"]
                        ]
                    ),
                )
                for _, row in searches_df.iterrows()
            ]

            cursor.executemany(
                searches_sql,
                search_records,
            )

            print(
                f"[PASS] Searches imported: "
                f"{len(search_records):,}"
            )


            # =================================================
            # 8.7 SEARCH RESULTS
            # =================================================

            print(
                "\nImporting search results..."
            )

            results_sql = """
                INSERT INTO search_results (
                    result_id,
                    search_id,
                    rank_position,
                    result_type,
                    relevance_score,
                    clicked,
                    dwell_time_seconds,
                    returned_to_search
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            result_records = [
                (
                    int(row["result_id"]),
                    int(row["search_id"]),
                    int(row["rank_position"]),
                    row["result_type"],
                    float(row["relevance_score"]),
                    bool(row["clicked"]),
                    (
                        float(row["dwell_time_seconds"])
                        if pd.notna(
                            row["dwell_time_seconds"]
                        )
                        else None
                    ),
                    (
                        bool(row["returned_to_search"])
                        if pd.notna(
                            row["returned_to_search"]
                        )
                        else None
                    ),
                )
                for _, row in results_df.iterrows()
            ]

            cursor.executemany(
                results_sql,
                result_records,
            )

            print(
                f"[PASS] Search results imported: "
                f"{len(result_records):,}"
            )


            # =================================================
            # 8.8 BUSINESS EVENTS
            # =================================================

            print(
                "\nImporting business events..."
            )

            events_sql = """
                INSERT INTO business_events (
                    event_id,
                    search_id,
                    event_type,
                    event_timestamp
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            event_records = [
                (
                    int(row["event_id"]),
                    int(row["search_id"]),
                    row["event_type"],
                    row["event_timestamp"].to_pydatetime(),
                )
                for _, row in events_df.iterrows()
            ]

            cursor.executemany(
                events_sql,
                event_records,
            )

            print(
                f"[PASS] Business events imported: "
                f"{len(event_records):,}"
            )


            # =================================================
            # 9. ROW-COUNT VALIDATION
            # =================================================

            print(
                "\n" + "-" * 70
            )

            print(
                "POSTGRESQL ROW-COUNT VALIDATION"
            )

            print(
                "-" * 70
            )

            expected_counts = {
                "users": len(users_df),
                "experiments": len(experiments),
                "experiment_assignments": len(assignments_df),
                "search_sessions": len(sessions_df),
                "searches": len(searches_df),
                "search_results": len(results_df),
                "business_events": len(events_df),
            }

            for table_name, expected_count in expected_counts.items():

                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    """
                )

                actual_count = cursor.fetchone()[0]

                if actual_count != expected_count:

                    raise ValueError(
                        f"[FAIL] {table_name}: "
                        f"expected={expected_count:,}, "
                        f"actual={actual_count:,}"
                    )

                print(
                    f"[PASS] "
                    f"{table_name:<25}"
                    f"{actual_count:,}"
                )


            # =================================================
            # 10. FOREIGN-KEY VALIDATION
            # =================================================

            print(
                "\n" + "-" * 70
            )

            print(
                "FOREIGN-KEY VALIDATION"
            )

            print(
                "-" * 70
            )


            fk_checks = {

                "assignments → users": """
                    SELECT COUNT(*)
                    FROM experiment_assignments ea
                    LEFT JOIN users u
                        ON ea.user_id = u.user_id
                    WHERE u.user_id IS NULL
                """,

                "assignments → experiments": """
                    SELECT COUNT(*)
                    FROM experiment_assignments ea
                    LEFT JOIN experiments e
                        ON ea.experiment_id = e.experiment_id
                    WHERE e.experiment_id IS NULL
                """,

                "sessions → users": """
                    SELECT COUNT(*)
                    FROM search_sessions ss
                    LEFT JOIN users u
                        ON ss.user_id = u.user_id
                    WHERE u.user_id IS NULL
                """,

                "searches → sessions": """
                    SELECT COUNT(*)
                    FROM searches s
                    LEFT JOIN search_sessions ss
                        ON s.session_id = ss.session_id
                    WHERE ss.session_id IS NULL
                """,

                "results → searches": """
                    SELECT COUNT(*)
                    FROM search_results sr
                    LEFT JOIN searches s
                        ON sr.search_id = s.search_id
                    WHERE s.search_id IS NULL
                """,

                "events → searches": """
                    SELECT COUNT(*)
                    FROM business_events be
                    LEFT JOIN searches s
                        ON be.search_id = s.search_id
                    WHERE s.search_id IS NULL
                """,
            }


            for check_name, query in fk_checks.items():

                cursor.execute(query)

                orphan_count = cursor.fetchone()[0]

                if orphan_count != 0:

                    raise ValueError(
                        f"[FAIL] {check_name}: "
                        f"{orphan_count:,} orphaned rows"
                    )

                print(
                    f"[PASS] {check_name}"
                )


            # =================================================
            # 11. VARIANT VALIDATION
            # =================================================

            print(
                "\n" + "-" * 70
            )

            print(
                "EXPERIMENT VARIANT VALIDATION"
            )

            print(
                "-" * 70
            )

            cursor.execute(
                """
                SELECT DISTINCT variant
                FROM experiment_assignments
                ORDER BY variant;
                """
            )

            variants = {
                row[0]
                for row in cursor.fetchall()
            }

            expected_variants = {
                "Control",
                "Treatment",
            }

            if variants != expected_variants:

                raise ValueError(
                    "Unexpected experiment variants: "
                    f"{variants}"
                )

            print(
                "[PASS] Control + Treatment variants present"
            )


            # =================================================
            # 12. EXPERIMENT ASSIGNMENT VALIDATION
            # =================================================

            cursor.execute(
                """
                SELECT
                    experiment_id,
                    variant,
                    COUNT(*)
                FROM experiment_assignments
                GROUP BY experiment_id, variant
                ORDER BY experiment_id, variant;
                """
            )

            assignment_summary = cursor.fetchall()

            print(
                "\nExperiment assignment summary:"
            )

            for experiment_id, variant, count in assignment_summary:

                print(
                    f"  Experiment {experiment_id}: "
                    f"{variant} = {count:,}"
                )


    # ========================================================
    # FINAL SUCCESS
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "POSTGRESQL IMPORT COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )

    print(
        "\nValidated PRYVIA dataset is now loaded "
        "into PostgreSQL."
    )


except Exception as error:

    connection.rollback()

    print(
        "\n" + "=" * 70
    )

    print(
        "POSTGRESQL IMPORT FAILED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nError: {error}"
    )

    print(
        "\nTransaction rolled back."
    )

    print(
        "No partial import was committed."
    )

    raise


finally:

    connection.close()

    print(
        "\nPostgreSQL connection closed."
    )