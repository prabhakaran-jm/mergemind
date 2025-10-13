{{ config(materialized='view') }}

-- Simplified risk features using only available raw data
WITH base AS (
  SELECT 
    id as mr_id,
    project_id,
    title,
    created_at,
    state,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours
  FROM `ai-accelerate-mergemind.mergemind_raw.merge_requests`
)

SELECT
  mr_id, 
  project_id,
  age_hours,
  0 AS notes_count_24h,  -- Not available in raw data
  FALSE AS last_pipeline_status_is_fail,  -- Not available in raw data
  0 AS approvals_left,  -- Not available in raw data
  'S' AS change_size_bucket,  -- Default to small since we don't have additions/deletions
  
  -- Placeholder features (to be populated by data pipeline)
  0.0 AS author_recent_fail_rate_7d,
  0.0 AS repo_merge_conflict_rate_14d,
  
  -- Derived features
  REGEXP_CONTAINS(UPPER(title), r'(^WIP|WIP:)') AS work_in_progress,
  FALSE AS labels_sensitive,
  
  -- Risk scoring (computed in application layer)
  0 AS risk_score_rule,
  'Low' AS risk_label
FROM base
