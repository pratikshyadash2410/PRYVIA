-- ============================================================
-- PRYVIA — PostgreSQL Indexes
-- ============================================================
-- Purpose:
-- Improve query performance for common joins, filtering,
-- experiment analysis, ranking analysis, and event analysis.
-- ============================================================


-- Find experiment assignments for a specific user.
CREATE INDEX idx_experiment_assignments_user_id
ON experiment_assignments(user_id);


-- Quickly compare Control vs Treatment within an experiment.
CREATE INDEX idx_experiment_assignments_experiment_variant
ON experiment_assignments(experiment_id, variant);


-- Find all sessions belonging to a user.
CREATE INDEX idx_search_sessions_user_id
ON search_sessions(user_id);


-- Find all searches belonging to a session.
CREATE INDEX idx_searches_session_id
ON searches(session_id);


-- Support chronological search analysis within sessions.
CREATE INDEX idx_searches_session_timestamp
ON searches(session_id, search_timestamp);


-- Find all results belonging to a search.
CREATE INDEX idx_search_results_search_id
ON search_results(search_id);


-- Support ranking-position analysis.
CREATE INDEX idx_search_results_search_rank
ON search_results(search_id, rank_position);


-- Find business events belonging to a search.
CREATE INDEX idx_business_events_search_id
ON business_events(search_id);


-- Analyze events by event type.
CREATE INDEX idx_business_events_event_type
ON business_events(event_type);