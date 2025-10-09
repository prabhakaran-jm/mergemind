{{ config(materialized='view') }}

WITH last_pipeline AS (
  SELECT 
    project_id, 
    mr_id, 
    ARRAY_AGG(
      STRUCT(
        status, 
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), updated_at, MINUTE) AS age_min
      )
      ORDER BY updated_at DESC 
      LIMIT 1
    )[OFFSET(0)] AS lp
  FROM `{{ var('raw_dataset', 'mergemind_raw') }}.pipelines`
  WHERE mr_id IS NOT NULL
  GROUP BY project_id, mr_id
),

recent_notes AS (
  SELECT 
    project_id, 
    mr_id, 
    COUNTIF(created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)) AS notes_count_24h
  FROM `{{ var('raw_dataset', 'mergemind_raw') }}.mr_notes`
  GROUP BY project_id, mr_id
)

SELECT
  mr.project_id, 
  mr.mr_id, 
  mr.title, 
  mr.author_id, 
  mr.created_at, 
  mr.state,
  lp.lp.status AS last_pipeline_status,
  lp.lp.age_min AS last_pipeline_age_min,
  COALESCE(rn.notes_count_24h, 0) AS notes_count_24h,
  mr.approvals_left,
  mr.additions, 
  mr.deletions
FROM `{{ var('raw_dataset', 'mergemind_raw') }}.merge_requests` mr
LEFT JOIN last_pipeline lp USING (project_id, mr_id)
LEFT JOIN recent_notes rn USING (project_id, mr_id)
