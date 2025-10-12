{{ config(materialized='view') }}

-- Simplified MR activity view using only available raw data
SELECT
  id as mr_id,
  project_id, 
  title, 
  author_id, 
  created_at, 
  state,
  -- Default values for missing fields
  'unknown' AS last_pipeline_status,
  0 AS last_pipeline_age_min,
  0 AS notes_count_24h,
  0 AS approvals_left,
  0 AS additions, 
  0 AS deletions,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
  source_branch,
  target_branch,
  web_url,
  assignee_id,
  updated_at,
  merged_at,
  closed_at
FROM `ai-accelerate-mergemind.gitlab_connector_v1.merge_requests`
