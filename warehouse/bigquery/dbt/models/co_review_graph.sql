-- Co-review graph for reviewer suggestions
-- Simplified version using only available raw data

WITH mr_interactions AS (
  SELECT 
    id as mr_id,
    project_id,
    author_id,
    created_at,
    state,
    title
  FROM `ai-accelerate-mergemind.mergemind_raw.merge_requests`
  WHERE state IN ('merged', 'closed')
),

-- Since we don't have mr_notes, we'll create a simple co-review graph
-- based on project collaboration patterns
project_collaborators AS (
  SELECT 
    project_id,
    author_id,
    COUNT(*) as mr_count,
    MIN(created_at) as first_mr,
    MAX(created_at) as last_mr
  FROM `ai-accelerate-mergemind.mergemind_raw.merge_requests`
  GROUP BY project_id, author_id
),

reviewer_author_pairs AS (
  SELECT 
    pc1.author_id,
    pc2.author_id as reviewer_id,
    COUNT(*) as interaction_count,
    -- Estimate interactions based on project collaboration
    COUNT(*) * 0.3 as approval_count,
    COUNT(*) * 0.5 as review_count,
    COUNT(*) * 0.2 as comment_count,
    COUNT(*) * 0.3 as approval_interactions,
    COUNT(*) * 0.5 as review_interactions,
    COUNT(*) * 0.8 as total_review_interactions,
    MIN(LEAST(pc1.first_mr, pc2.first_mr)) as first_interaction,
    MAX(GREATEST(pc1.last_mr, pc2.last_mr)) as last_interaction
  FROM project_collaborators pc1
  INNER JOIN project_collaborators pc2 ON pc1.project_id = pc2.project_id
  WHERE pc1.author_id != pc2.author_id  -- Exclude self-reviews
  GROUP BY pc1.author_id, pc2.author_id
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
