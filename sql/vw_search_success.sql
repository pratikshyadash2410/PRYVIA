-- Reusable search-level analytical view for PRYVIA.
-- Centralizes successful-search logic and adds
-- experiment and user-segment dimensions.

CREATE OR REPLACE VIEW vw_search_success AS

WITH search_quality AS (

    SELECT
        sr.search_id,

        -- A quality click means:
        -- clicked result + at least 30 seconds dwell time.
        MAX(
            CASE
                WHEN sr.clicked = TRUE
                     AND sr.dwell_time_seconds >= 30
                THEN 1
                ELSE 0
            END
        ) AS quality_click

    FROM search_results sr

    GROUP BY
        sr.search_id
)

SELECT
    -- Existing columns: KEEP SAME ORDER
    s.search_id,
    s.session_id,
    ss.user_id,
    s.search_timestamp,
    s.query_category,
    s.search_latency_ms,
    s.search_error,
    s.is_reformulation,
    sq.quality_click,
    CASE
        WHEN sq.quality_click = 1
             AND s.is_reformulation = FALSE
        THEN 1
        ELSE 0
    END AS successful_search,

    -- New analytical dimensions
    u.device_type,
    u.activity_level,
    ea.experiment_id,
    ea.variant

FROM searches s

JOIN search_sessions ss
    ON s.session_id = ss.session_id

JOIN users u
    ON ss.user_id = u.user_id

JOIN experiment_assignments ea
    ON ss.user_id = ea.user_id

JOIN search_quality sq
    ON s.search_id = sq.search_id;

SELECT *
FROM vw_search_success
LIMIT 10;

SELECT
    experiment_id,
    variant,
    device_type,
    COUNT(*) AS searches,
    ROUND(
        100.0 * AVG(successful_search),
        2
    ) AS ssr_percent
FROM vw_search_success
GROUP BY
    experiment_id,
    variant,
    device_type
ORDER BY
    experiment_id,
    variant,
    device_type;