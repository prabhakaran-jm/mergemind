{{ config(materialized='view') }}

SELECT
  project_id, 
  id as mr_id, 
  created_at,
  COALESCE(merged_at, closed_at) AS end_at,
  TIMESTAMP_DIFF(COALESCE(merged_at, closed_at), created_at, HOUR) AS cycle_time_hours
FROM {{ source('raw', 'merge_requests') }}
WHERE state IN ('merged','closed')
  AND COALESCE(merged_at, closed_at) IS NOT NULL
