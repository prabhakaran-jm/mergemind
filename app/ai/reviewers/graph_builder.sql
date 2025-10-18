-- Co-review graph builder for reviewer suggestions
-- Computes normalized edge weights between authors and candidates using mr_notes (reviews/approvals proxy)

WITH co_review_edges AS (
  SELECT 
    mr.author_id,
    note.author_id AS reviewer_id,
    COUNT(*) AS interaction_count,
    COUNTIF(note.note_type = 'approval') AS approval_count,
    COUNTIF(note.note_type = 'review') AS review_count,
    COUNTIF(note.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)) AS recent_interactions
  FROM `mergemind_raw.merge_requests` mr
  JOIN `mergemind_raw.mr_notes` note ON mr.project_id = note.project_id AND mr.mr_id = note.mr_id
  WHERE 
    mr.author_id != note.author_id  -- Exclude self-reviews
    AND note.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
    AND note.note_type IN ('approval', 'review', 'comment')
  GROUP BY mr.author_id, note.author_id
),

-- Calculate normalized weights
weighted_edges AS (
  SELECT 
    author_id,
    reviewer_id,
    interaction_count,
    approval_count,
    review_count,
    recent_interactions,
    -- Normalize by total interactions for this author
    SAFE_DIVIDE(interaction_count, SUM(interaction_count) OVER (PARTITION BY author_id)) AS normalized_weight,
    -- Calculate expertise score (approvals weighted higher than reviews)
    (approval_count * 2 + review_count) AS expertise_score,
    -- Recent activity bonus
    CASE 
      WHEN recent_interactions > 0 THEN 1.2
      ELSE 1.0
    END AS recency_multiplier
  FROM co_review_edges
),

-- Final edge weights with recency adjustment
final_edges AS (
  SELECT 
    author_id,
    reviewer_id,
    interaction_count,
    approval_count,
    review_count,
    normalized_weight,
    expertise_score,
    recency_multiplier,
    -- Final weight combines normalized interaction, expertise, and recency
    normalized_weight * expertise_score * recency_multiplier AS final_weight
  FROM weighted_edges
)

SELECT 
  author_id,
  reviewer_id,
  interaction_count,
  approval_count,
  review_count,
  normalized_weight,
  expertise_score,
  recency_multiplier,
  final_weight,
  -- Rank reviewers by weight for each author
  ROW_NUMBER() OVER (PARTITION BY author_id ORDER BY final_weight DESC) AS rank_by_weight
FROM final_edges
ORDER BY author_id, final_weight DESC;
