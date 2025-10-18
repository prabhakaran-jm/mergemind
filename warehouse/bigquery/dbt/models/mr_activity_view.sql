{{ config(materialized='view') }}

-- Enhanced MR activity view using real data from Fivetran connector
SELECT
  id as mr_id,
  project_id, 
  title, 
  author_id, 
  created_at, 
  state,
  -- Real data from enhanced connector
  last_pipeline_status,
  last_pipeline_age_min,
  notes_count_24h,
  approvals_left,
  additions, 
  deletions,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
  source_branch,
  target_branch,
  web_url,
  assignee_id,
  updated_at,
  merged_at,
  closed_at,
  -- Additional enhanced fields
  work_in_progress,
  labels,
  milestone_id,
  merge_user_id,
  merge_commit_sha
FROM {{ source('raw', 'merge_requests') }}
