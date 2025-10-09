{{ config(materialized='view') }}

WITH base AS (
  SELECT 
    *, 
    SAFE_DIVIDE(additions + deletions, 1) AS churn
  FROM `{{ var('modeled_dataset', 'mergemind') }}.mr_activity_view`
),

sizes AS (
  SELECT 
    mr_id,
    CASE
      WHEN churn < 50 THEN 'S'
      WHEN churn < 200 THEN 'M'
      WHEN churn < 800 THEN 'L'
      ELSE 'XL'
    END AS change_size_bucket
  FROM base
),

age AS (
  SELECT 
    mr_id, 
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours
  FROM base
)

SELECT
  b.mr_id, 
  b.project_id,
  (SELECT age_hours FROM age WHERE mr_id=b.mr_id) AS age_hours,
  COALESCE(b.notes_count_24h, 0) AS notes_count_24h,
  IFNULL(b.last_pipeline_status='failed', FALSE) AS last_pipeline_status_is_fail,
  COALESCE(b.approvals_left, 0) AS approvals_left,
  (SELECT change_size_bucket FROM sizes WHERE mr_id=b.mr_id) AS change_size_bucket,
  
  -- Placeholder features (to be populated by data pipeline)
  0.0 AS author_recent_fail_rate_7d,
  0.0 AS repo_merge_conflict_rate_14d,
  
  -- Derived features
  REGEXP_CONTAINS(UPPER(b.title), r'(^WIP|WIP:)') AS work_in_progress,
  FALSE AS labels_sensitive,
  
  -- Risk scoring (computed in application layer)
  0 AS risk_score_rule,
  'Low' AS risk_label
FROM base b
