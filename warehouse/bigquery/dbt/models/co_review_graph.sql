-- Co-review graph for reviewer suggestions
-- Analyzes reviewer-author relationships based on historical MR interactions

WITH mr_interactions AS (
  SELECT 
    mr_id,
    project_id,
    author_id,
    created_at,
    state,
    title
  FROM `{{ ref('mr_activity_view') }}`
  WHERE state IN ('merged', 'closed')
),

mr_notes AS (
  SELECT 
    mr_id,
    author_id as reviewer_id,
    created_at,
    note_type,
    CASE 
      WHEN note_type = 'approval' THEN 1
      WHEN note_type = 'review' THEN 1
      ELSE 0
    END as is_review_interaction
  FROM `{{ source('raw', 'mr_notes') }}`
  WHERE note_type IN ('approval', 'review', 'comment')
),

reviewer_author_pairs AS (
  SELECT 
    mi.author_id,
    mn.reviewer_id,
    COUNT(*) as interaction_count,
    COUNTIF(note_type = 'approval') as approval_count,
    COUNTIF(note_type = 'review') as review_count,
    COUNTIF(note_type = 'comment') as comment_count,
    COUNTIF(note_type = 'approval') as approval_interactions,
    COUNTIF(note_type = 'review') as review_interactions,
    COUNTIF(mn.is_review_interaction = 1) as total_review_interactions,
    MIN(mi.created_at) as first_interaction,
    MAX(mi.created_at) as last_interaction
  FROM mr_interactions mi
  INNER JOIN mr_notes mn ON mi.mr_id = mn.mr_id
  WHERE mi.author_id != mn.reviewer_id  -- Exclude self-reviews
  GROUP BY mi.author_id, mn.reviewer_id
),

weighted_interactions AS (
  SELECT 
    author_id,
    reviewer_id,
    interaction_count,
    approval_count,
    review_count,
    comment_count,
    approval_interactions,
    review_interactions,
    total_review_interactions,
    first_interaction,
    last_interaction,
    -- Weight calculations
    (approval_count * 3.0) + (review_count * 2.0) + (comment_count * 1.0) as weighted_score,
    -- Recency bonus (more recent interactions get higher weight)
    CASE 
      WHEN DATE_DIFF(CURRENT_DATE(), DATE(last_interaction), DAY) <= 30 THEN 1.2
      WHEN DATE_DIFF(CURRENT_DATE(), DATE(last_interaction), DAY) <= 90 THEN 1.1
      ELSE 1.0
    END as recency_multiplier,
    -- Frequency bonus (more interactions get higher weight)
    CASE 
      WHEN interaction_count >= 10 THEN 1.3
      WHEN interaction_count >= 5 THEN 1.2
      WHEN interaction_count >= 3 THEN 1.1
      ELSE 1.0
    END as frequency_multiplier
  FROM reviewer_author_pairs
),

final_weights AS (
  SELECT 
    author_id,
    reviewer_id,
    interaction_count,
    approval_count,
    review_count,
    comment_count,
    approval_interactions,
    review_interactions,
    total_review_interactions,
    first_interaction,
    last_interaction,
    weighted_score,
    recency_multiplier,
    frequency_multiplier,
    -- Final weight calculation
    weighted_score * recency_multiplier * frequency_multiplier as final_weight,
    -- Ranking within each author
    ROW_NUMBER() OVER (
      PARTITION BY author_id 
      ORDER BY weighted_score * recency_multiplier * frequency_multiplier DESC
    ) as rank_by_weight
  FROM weighted_interactions
)

SELECT 
  author_id,
  reviewer_id,
  interaction_count,
  approval_count,
  review_count,
  comment_count,
  approval_interactions,
  review_interactions,
  total_review_interactions,
  first_interaction,
  last_interaction,
  weighted_score,
  recency_multiplier,
  frequency_multiplier,
  final_weight,
  rank_by_weight,
  CURRENT_TIMESTAMP() as created_at,
  CURRENT_TIMESTAMP() as updated_at
FROM final_weights
WHERE final_weight > 0  -- Only include meaningful relationships
ORDER BY author_id, final_weight DESC
