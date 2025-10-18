{{ config(materialized='view') }}

-- Enhanced risk features using real data from Fivetran connector
WITH base AS (
  SELECT 
    id as mr_id,
    project_id,
    title,
    created_at,
    state,
    additions,
    deletions,
    last_pipeline_status,
    notes_count_24h,
    approvals_left,
    work_in_progress,
    labels,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours
  FROM {{ source('raw', 'merge_requests') }}
)

SELECT
  mr_id, 
  project_id,
  age_hours,
  notes_count_24h,
  last_pipeline_status = 'failed' AS last_pipeline_status_is_fail,
  approvals_left,
  
  -- Change size bucket based on real additions/deletions
  CASE 
    WHEN (additions + deletions) <= 50 THEN 'S'
    WHEN (additions + deletions) <= 200 THEN 'M'
    WHEN (additions + deletions) <= 500 THEN 'L'
    ELSE 'XL'
  END AS change_size_bucket,
  
  -- Placeholder features (to be populated by data pipeline)
  0.0 AS author_recent_fail_rate_7d,
  0.0 AS repo_merge_conflict_rate_14d,
  
  -- Derived features using real data
  work_in_progress,
  REGEXP_CONTAINS(labels, r'(?i)(security|confidential|sensitive)') AS labels_sensitive,
  
  -- Risk scoring (computed in application layer)
  0 AS risk_score_rule,
  'Low' AS risk_label
FROM base
