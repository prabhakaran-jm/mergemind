#!/bin/bash

# Seed demo data for MergeMind
# This script creates sample data in BigQuery for testing

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
DATASET_RAW=${BQ_DATASET_RAW:-"mergemind_raw"}
DATASET_MODELED=${BQ_DATASET_MODELED:-"mergemind"}
LOCATION=${VERTEX_LOCATION:-"us-central1"}

echo "Seeding demo data for MergeMind..."
echo "Project: $PROJECT_ID"
echo "Raw Dataset: $DATASET_RAW"
echo "Modeled Dataset: $DATASET_MODELED"
echo "Location: $LOCATION"

# Check if bq command is available
if ! command -v bq &> /dev/null; then
    echo "Error: bq command not found. Please install Google Cloud SDK."
    exit 1
fi

# Create datasets if they don't exist
echo "Creating datasets..."
bq mk --location=$LOCATION --dataset $PROJECT_ID:$DATASET_RAW || echo "Raw dataset already exists"
bq mk --location=$LOCATION --dataset $PROJECT_ID:$DATASET_MODELED || echo "Modeled dataset already exists"

# Create raw tables
echo "Creating raw tables..."

# Merge requests table
bq mk --table $PROJECT_ID:$DATASET_RAW.merge_requests \
    mr_id:INTEGER,project_id:INTEGER,title:STRING,author_id:INTEGER,created_at:TIMESTAMP,state:STRING,merged_at:TIMESTAMP,closed_at:TIMESTAMP,additions:INTEGER,deletions:INTEGER,approvals_left:INTEGER,sha:STRING

# MR notes table
bq mk --table $PROJECT_ID:$DATASET_RAW.mr_notes \
    note_id:INTEGER,project_id:INTEGER,mr_id:INTEGER,author_id:INTEGER,created_at:TIMESTAMP,note_type:STRING,body:STRING

# Pipelines table
bq mk --table $PROJECT_ID:$DATASET_RAW.pipelines \
    pipeline_id:INTEGER,project_id:INTEGER,mr_id:INTEGER,status:STRING,created_at:TIMESTAMP,updated_at:TIMESTAMP

# Users table
bq mk --table $PROJECT_ID:$DATASET_RAW.users \
    user_id:INTEGER,name:STRING,username:STRING,email:STRING,created_at:TIMESTAMP

# Projects table
bq mk --table $PROJECT_ID:$DATASET_RAW.projects \
    project_id:INTEGER,name:STRING,path:STRING,created_at:TIMESTAMP

# Issues table
bq mk --table $PROJECT_ID:$DATASET_RAW.issues \
    issue_id:INTEGER,project_id:INTEGER,title:STRING,author_id:INTEGER,created_at:TIMESTAMP,state:STRING,labels:STRING

echo "Inserting demo data..."

# Insert demo merge requests
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.merge_requests\` 
(mr_id, project_id, title, author_id, created_at, state, merged_at, closed_at, additions, deletions, approvals_left, sha)
VALUES
(1, 100, 'Add user authentication system', 101, '2024-01-15 10:00:00', 'opened', NULL, NULL, 150, 20, 2, 'abc123'),
(2, 100, 'Fix login validation bug', 102, '2024-01-14 14:30:00', 'merged', '2024-01-15 09:00:00', NULL, 45, 12, 0, 'def456'),
(3, 101, 'Implement API rate limiting', 103, '2024-01-13 16:45:00', 'opened', NULL, NULL, 200, 50, 1, 'ghi789'),
(4, 101, 'Update documentation', 101, '2024-01-12 11:20:00', 'closed', NULL, '2024-01-14 15:30:00', 30, 5, 0, 'jkl012'),
(5, 100, 'WIP: Add payment processing', 104, '2024-01-11 09:15:00', 'opened', NULL, NULL, 300, 80, 3, 'mno345')
"

# Insert demo MR notes
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.mr_notes\`
(note_id, project_id, mr_id, author_id, created_at, note_type, body)
VALUES
(1, 100, 1, 105, '2024-01-15 10:30:00', 'comment', 'Looks good, but need to add error handling'),
(2, 100, 1, 106, '2024-01-15 11:00:00', 'approval', 'Approved after testing'),
(3, 100, 2, 107, '2024-01-14 15:00:00', 'review', 'Found a potential security issue'),
(4, 101, 3, 108, '2024-01-13 17:00:00', 'comment', 'Need to consider performance impact'),
(5, 101, 3, 109, '2024-01-13 17:30:00', 'approval', 'Approved with minor suggestions')
"

# Insert demo pipelines
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.pipelines\`
(pipeline_id, project_id, mr_id, status, created_at, updated_at)
VALUES
(1, 100, 1, 'success', '2024-01-15 10:05:00', '2024-01-15 10:15:00'),
(2, 100, 2, 'success', '2024-01-14 14:35:00', '2024-01-14 14:45:00'),
(3, 101, 3, 'failed', '2024-01-13 16:50:00', '2024-01-13 17:00:00'),
(4, 101, 4, 'success', '2024-01-12 11:25:00', '2024-01-12 11:35:00'),
(5, 100, 5, 'running', '2024-01-11 09:20:00', '2024-01-11 09:25:00')
"

# Insert demo users
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.users\`
(user_id, name, username, email, created_at)
VALUES
(101, 'John Doe', 'john.doe', 'john@example.com', '2024-01-01 00:00:00'),
(102, 'Jane Smith', 'jane.smith', 'jane@example.com', '2024-01-01 00:00:00'),
(103, 'Mike Johnson', 'mike.johnson', 'mike@example.com', '2024-01-01 00:00:00'),
(104, 'Sarah Wilson', 'sarah.wilson', 'sarah@example.com', '2024-01-01 00:00:00'),
(105, 'David Brown', 'david.brown', 'david@example.com', '2024-01-01 00:00:00'),
(106, 'Lisa Davis', 'lisa.davis', 'lisa@example.com', '2024-01-01 00:00:00'),
(107, 'Tom Miller', 'tom.miller', 'tom@example.com', '2024-01-01 00:00:00'),
(108, 'Amy Garcia', 'amy.garcia', 'amy@example.com', '2024-01-01 00:00:00'),
(109, 'Chris Martinez', 'chris.martinez', 'chris@example.com', '2024-01-01 00:00:00')
"

# Insert demo projects
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.projects\`
(project_id, name, path, created_at)
VALUES
(100, 'Web Application', 'web-app', '2024-01-01 00:00:00'),
(101, 'API Service', 'api-service', '2024-01-01 00:00:00'),
(102, 'Mobile App', 'mobile-app', '2024-01-01 00:00:00')
"

# Insert demo issues
bq query --use_legacy_sql=false --location=$LOCATION "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.issues\`
(issue_id, project_id, title, author_id, created_at, state, labels)
VALUES
(1, 100, 'Login page not responsive', 101, '2024-01-10 10:00:00', 'opened', 'bug,frontend'),
(2, 101, 'API timeout issues', 102, '2024-01-09 14:00:00', 'closed', 'bug,backend'),
(3, 100, 'Add dark mode support', 103, '2024-01-08 16:00:00', 'opened', 'enhancement,ui')
"

echo "Demo data seeded successfully!"
echo ""
echo "You can now run the following commands to test:"
echo "  make dev.api    # Start the API server"
echo "  make dev.ui     # Start the UI server"
echo "  make dbt.run    # Run dbt models"
echo "  make dbt.test   # Test dbt models"
echo ""
echo "Sample MR IDs to test: 1, 2, 3, 4, 5"
