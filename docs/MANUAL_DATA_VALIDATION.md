# Manual Data Validation Guide

This guide provides step-by-step instructions for manually validating the transformed data in MergeMind.

## 1. BigQuery Console Validation

### Access BigQuery Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to BigQuery
3. Select project: `ai-accelerate-mergemind`

### Check Raw Data
```sql
-- Check raw merge requests
SELECT COUNT(*) as total_mrs, 
       COUNTIF(state = 'opened') as open_mrs,
       COUNTIF(state = 'merged') as merged_mrs,
       COUNTIF(state = 'closed') as closed_mrs
FROM `gitlab_connector_v1.merge_requests`;

-- Check raw projects
SELECT COUNT(*) as total_projects
FROM `gitlab_connector_v1.projects`;

-- Check raw users
SELECT COUNT(*) as total_users
FROM `gitlab_connector_v1.users`;
```

### Check Transformed Data
```sql
-- Check MR Activity View
SELECT COUNT(*) as total_mrs,
       COUNTIF(state = 'opened') as open_mrs,
       AVG(age_hours) as avg_age_hours,
       COUNTIF(last_pipeline_status = 'unknown') as unknown_pipeline
FROM `mergemind.mr_activity_view`;

-- Check Risk Features
SELECT COUNT(*) as total_features,
       COUNTIF(work_in_progress = true) as wip_mrs,
       COUNTIF(change_size_bucket = 'S') as small_changes,
       COUNTIF(risk_label = 'Low') as low_risk
FROM `mergemind.merge_risk_features`;

-- Check Co-review Graph
SELECT COUNT(*) as total_relationships,
       COUNT(DISTINCT author_id) as unique_authors,
       COUNT(DISTINCT reviewer_id) as unique_reviewers
FROM `mergemind.co_review_graph`;

-- Check Cycle Time View
SELECT COUNT(*) as completed_mrs,
       AVG(cycle_time_hours) as avg_cycle_time,
       MIN(cycle_time_hours) as min_cycle_time,
       MAX(cycle_time_hours) as max_cycle_time
FROM `mergemind.cycle_time_view`;
```

## 2. Data Quality Checks

### Consistency Checks
```sql
-- Check data consistency between raw and transformed
SELECT 
  r.id as raw_id,
  t.mr_id as transformed_id,
  r.title as raw_title,
  t.title as transformed_title,
  r.state as raw_state,
  t.state as transformed_state
FROM `gitlab_connector_v1.merge_requests` r
JOIN `mergemind.mr_activity_view` t ON r.id = t.mr_id
WHERE r.id != t.mr_id OR r.title != t.title OR r.state != t.state;
-- Should return 0 rows if consistent
```

### Completeness Checks
```sql
-- Check for missing risk features
SELECT 
  m.mr_id,
  m.title,
  r.mr_id as risk_mr_id
FROM `mergemind.mr_activity_view` m
LEFT JOIN `mergemind.merge_risk_features` r ON m.mr_id = r.mr_id
WHERE r.mr_id IS NULL;
-- Should return 0 rows if complete
```

### Accuracy Checks
```sql
-- Check age calculation accuracy
SELECT 
  mr_id,
  title,
  created_at,
  age_hours,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) as calculated_age,
  ABS(age_hours - TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR)) as age_diff
FROM `mergemind.mr_activity_view`
WHERE ABS(age_hours - TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR)) > 1;
-- Should return 0 rows if accurate
```

## 3. API Validation

### Test MRs Endpoint
```bash
# Start the API server
cd api/fastapi_app
python main.py

# Test the endpoint
curl "http://localhost:8080/api/v1/mrs?limit=5"
```

### Test Blockers Endpoint
```bash
curl "http://localhost:8080/api/v1/mrs/blockers/top?limit=3"
```

### Test Individual MR Endpoint
```bash
curl "http://localhost:8080/api/v1/mr/3/context"
curl "http://localhost:8080/api/v1/mr/3/risk"
curl "http://localhost:8080/api/v1/mr/3/reviewers"
```

## 4. dbt Validation

### Run dbt Models
```bash
cd warehouse/bigquery/dbt
dbt run
```

### Run dbt Tests
```bash
dbt test
```

### Check dbt Documentation
```bash
dbt docs generate
dbt docs serve
```

## 5. Performance Validation

### Query Performance
```sql
-- Test query performance
SELECT 
  COUNT(*) as total_mrs,
  COUNTIF(state = 'opened') as open_mrs,
  AVG(age_hours) as avg_age
FROM `mergemind.mr_activity_view`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);
```

### Index Usage
```sql
-- Check if queries are using indexes efficiently
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM `mergemind.mr_activity_view` 
WHERE state = 'opened' 
ORDER BY age_hours DESC 
LIMIT 10;
```

## 6. Data Freshness Validation

### Check Data Recency
```sql
-- Check when data was last updated
SELECT 
  MAX(created_at) as latest_mr,
  MIN(created_at) as oldest_mr,
  COUNT(*) as total_mrs
FROM `mergemind.mr_activity_view`;

-- Check age distribution
SELECT 
  COUNTIF(age_hours < 24) as less_than_1_day,
  COUNTIF(age_hours BETWEEN 24 AND 168) as one_to_7_days,
  COUNTIF(age_hours > 168) as more_than_7_days
FROM `mergemind.mr_activity_view`
WHERE state = 'opened';
```

## 7. Business Logic Validation

### Risk Scoring Logic
```sql
-- Check risk scoring logic
SELECT 
  mr_id,
  age_hours,
  work_in_progress,
  change_size_bucket,
  risk_score_rule,
  risk_label,
  CASE 
    WHEN age_hours > 168 AND work_in_progress = true THEN 'High'
    WHEN age_hours > 72 THEN 'Medium'
    ELSE 'Low'
  END as expected_risk
FROM `mergemind.merge_risk_features`
WHERE risk_label != CASE 
  WHEN age_hours > 168 AND work_in_progress = true THEN 'High'
  WHEN age_hours > 72 THEN 'Medium'
  ELSE 'Low'
END;
-- Should return 0 rows if logic is correct
```

### Reviewer Suggestions Logic
```sql
-- Check co-review graph logic
SELECT 
  author_id,
  reviewer_id,
  interaction_count,
  final_weight,
  rank_by_weight
FROM `mergemind.co_review_graph`
WHERE final_weight <= 0 OR rank_by_weight <= 0;
-- Should return 0 rows if logic is correct
```

## 8. Automated Validation Scripts

### Run Transformed Data Validation
```bash
python validate_transformed_data.py
```

### Run dbt Models Validation
```bash
python validate_dbt_models.py
```

### Run End-to-End Validation
```bash
python validate_api.py
```

## 9. Common Issues and Solutions

### Issue: Missing Data
- **Check**: Raw data ingestion
- **Solution**: Verify Fivetran connector is running

### Issue: Stale Data
- **Check**: Last sync timestamps
- **Solution**: Check Fivetran sync schedule

### Issue: Performance Issues
- **Check**: Query execution times
- **Solution**: Add indexes or optimize queries

### Issue: Data Quality Issues
- **Check**: Data consistency and completeness
- **Solution**: Fix dbt model logic or add data quality tests

## 10. Validation Checklist

- [ ] Raw data is available and up-to-date
- [ ] Transformed data matches raw data counts
- [ ] All dbt models run successfully
- [ ] All dbt tests pass
- [ ] API endpoints return correct data
- [ ] Risk scoring logic is correct
- [ ] Data freshness is acceptable
- [ ] Query performance is acceptable
- [ ] Data quality checks pass
- [ ] Business logic validation passes

## 11. Monitoring and Alerting

### Set up Monitoring
1. Configure BigQuery monitoring for query performance
2. Set up alerts for data freshness
3. Monitor API response times
4. Track data quality metrics

### Create Dashboards
1. Data pipeline health dashboard
2. API performance dashboard
3. Data quality dashboard
4. Business metrics dashboard

This manual validation guide ensures that your transformed data is accurate, complete, and performing well for the MergeMind application.
