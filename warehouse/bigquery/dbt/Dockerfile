# Dockerfile for dbt Cloud Build
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dbt
RUN pip install dbt-bigquery==1.7.0

# Set working directory
WORKDIR /workspace

# Copy dbt project files
COPY warehouse/bigquery/dbt/ ./warehouse/bigquery/dbt/

# Install dbt dependencies
RUN cd warehouse/bigquery/dbt && dbt deps

# Set environment variables
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}
ENV BQ_DATASET_RAW=${BQ_DATASET_RAW:-mergemind_raw}
ENV BQ_DATASET_MODELED=${BQ_DATASET_MODELED:-mergemind}

# Run dbt transformations
CMD ["sh", "-c", "cd warehouse/bigquery/dbt && dbt run --profiles-dir . && dbt test --profiles-dir ."]
