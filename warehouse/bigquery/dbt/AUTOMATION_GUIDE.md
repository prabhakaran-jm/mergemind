# dbt Automation Guide

## Overview
This guide shows how to automate dbt transformations using Cloud Build Triggers. This is the most cost-effective and event-driven approach for running dbt when new data arrives from Fivetran.

## Current Setup
- ✅ **Raw Data**: `mergemind_raw` (projects, merge_requests, users)
- ✅ **dbt Models**: 4 models ready to transform data
- ✅ **Target**: `mergemind` dataset for transformed data
- ✅ **Automation**: Cloud Build Triggers (event-driven)

## Cloud Build Triggers Setup

### Quick Start
```bash
cd warehouse/bigquery/dbt
chmod +x setup.sh
./setup.sh
```

### How It Works
1. **Event-Driven**: Triggers when you push changes to your repository
2. **Cost-Effective**: ~$0.003 per build + compute time (~$0.01-0.05 per run)
3. **Automatic**: Runs dbt transformations automatically
4. **Integrated**: Works with your existing Git workflow

### Manual Trigger
If you want to trigger dbt runs manually:
```bash
gcloud builds triggers run dbt-transform-trigger --branch=main
```

### Monitor Builds
```bash
# List recent builds
gcloud builds list --filter='trigger.name:dbt-transform-trigger' --limit=10

# View build logs
gcloud builds log [BUILD_ID]
```

## Files Structure
```
warehouse/bigquery/dbt/
├── setup.sh                    # Setup script for Cloud Build Triggers
├── cloudbuild-trigger.yaml     # Cloud Build configuration
├── Dockerfile                  # Docker configuration for dbt
├── requirements.txt            # Python dependencies
├── run_dbt.sh                  # Manual dbt run script
├── dbt.env                     # Environment variables
├── profiles.yml                # dbt profiles configuration
├── dbt_project.yml             # dbt project configuration
├── models/                     # dbt models
│   ├── sources.yml
│   ├── mr_activity_view.sql
│   ├── cycle_time_view.sql
│   ├── merge_risk_features.sql
│   └── co_review_graph.sql
└── AUTOMATION_GUIDE.md         # This file
```

## Benefits
- ✅ **No idle costs** 
- ✅ **Pay per use** 
- ✅ **Event-driven** 
- ✅ **Scales automatically**
- ✅ **Integrated with Git workflow**
- ✅ **Easy to monitor and debug**

## Troubleshooting

### Build Fails
1. Check build logs: `gcloud builds log [BUILD_ID]`
2. Verify environment variables in `dbt.env`
3. Test locally: `./run_dbt.sh`

### Trigger Not Working
1. Verify repository connection: `git remote -v`
2. Check trigger status: `gcloud builds triggers list`
3. Test manual trigger: `gcloud builds triggers run dbt-transform-trigger --branch=main`

### Environment Variables
Make sure `dbt.env` contains:
```
GCP_PROJECT_ID=ai-accelerate-mergemind
BQ_DATASET_RAW=mergemind_raw
BQ_DATASET_MODELED=mergemind
```

## Next Steps
1. Run `./setup.sh` to create the trigger
2. Make a small change and push to test
3. Monitor builds in Cloud Console
4. Set up alerts for failed builds (optional)