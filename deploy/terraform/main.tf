# MergeMind GCP Infrastructure
# This Terraform configuration sets up the required GCP APIs and resources for MergeMind

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data source for current project
data "google_project" "current" {
  project_id = var.project_id
}

# Enable required GCP APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",           # Vertex AI (for AI features)
    "iam.googleapis.com",                  # Identity and Access Management (for service accounts)
    "secretmanager.googleapis.com",        # Secret Manager (for GitLab token)
    "run.googleapis.com",                  # Cloud Run
    "cloudbuild.googleapis.com",           # Cloud Build (for dbt automation)
    "containerregistry.googleapis.com",    # Container Registry (for Docker images)
    "eventarc.googleapis.com",            # Eventarc (for event-driven dbt triggers)
    "pubsub.googleapis.com",               # Pub/Sub (for event messaging)
    "cloudfunctions.googleapis.com",       # Cloud Functions (for dbt trigger function)
    "logging.googleapis.com",             # Cloud Logging (for audit logs)
  ])

  service = each.value
  project  = var.project_id

  disable_on_destroy = false
}

# Note: BigQuery datasets already exist:
# - ai-accelerate-mergemind.mergemind_raw (raw GitLab data)
# - ai-accelerate-mergemind.mergemind (transformed data)
# No need to create them again

# Note: Fivetran data can use existing datasets
# No need to create separate fivetran_data dataset

# Service Account for MergeMind API
resource "google_service_account" "mergemind_api" {
  account_id   = "mergemind-api"
  display_name = "MergeMind API Service Account"
  description  = "Service account for MergeMind API operations"

  depends_on = [google_project_service.apis]
}

# Service Account for Vertex AI
resource "google_service_account" "vertex_ai" {
  account_id   = "vertex-ai-mergemind"
  display_name = "Vertex AI Service Account"
  description  = "Service account for Vertex AI operations"

  depends_on = [google_project_service.apis]
}

# IAM roles for MergeMind API service account
resource "google_project_iam_member" "mergemind_api_roles" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/bigquery.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.mergemind_api.email}"
}

# IAM roles for Vertex AI service account
resource "google_project_iam_member" "vertex_ai_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/bigquery.dataViewer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.vertex_ai.email}"
}

# Secret Manager secrets
resource "google_secret_manager_secret" "gitlab_token" {
  secret_id = "gitlab-token"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "vertex_ai_key" {
  secret_id = "vertex-ai-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Note: Terraform state bucket already exists: terraform-state-ai-accelerate-mergemind
# This bucket is shared with GitLab infrastructure and configured in backend.tf

# Cloud Storage bucket for MergeMind application data
resource "google_storage_bucket" "mergemind_data" {
  name          = "${var.project_id}-mergemind-data"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    application = "mergemind"
  }

  depends_on = [google_project_service.apis]
}

# Note: Using existing networking infrastructure
# No need to create new VPC, subnet, or firewall rules

# Outputs
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "bigquery_location" {
  description = "BigQuery Location"
  value       = var.bigquery_location
}

output "mergemind_dataset_id" {
  description = "MergeMind BigQuery Dataset ID (existing)"
  value       = var.bq_dataset_modeled
}

output "gitlab_dataset_id" {
  description = "GitLab Connector BigQuery Dataset ID (existing)"
  value       = var.bq_dataset_raw
}

output "mergemind_api_service_account" {
  description = "MergeMind API Service Account Email"
  value       = google_service_account.mergemind_api.email
}

output "vertex_ai_service_account" {
  description = "Vertex AI Service Account Email"
  value       = google_service_account.vertex_ai.email
}

output "terraform_state_bucket" {
  description = "Terraform State Storage Bucket (existing)"
  value       = "terraform-state-ai-accelerate-mergemind"
}

output "mergemind_data_bucket" {
  description = "MergeMind Data Storage Bucket"
  value       = google_storage_bucket.mergemind_data.name
}

output "vpc_network" {
  description = "VPC Network Name (using existing)"
  value       = "default"
}

output "subnet_name" {
  description = "Subnet Name (using existing)"
  value       = "default"
}

# Service Account for dbt Cloud Build
resource "google_service_account" "dbt_cloud_build" {
  account_id   = "dbt-cloud-build-sa"
  display_name = "dbt Cloud Build Service Account"
  description  = "Service account for dbt automation via Cloud Build"
}

# IAM bindings for dbt service account
resource "google_project_iam_member" "dbt_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dbt_cloud_build.email}"
}

resource "google_project_iam_member" "dbt_cloud_build_builder" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.dbt_cloud_build.email}"
}

# Cloud Build Trigger for dbt automation
resource "google_cloudbuild_trigger" "dbt_automation" {
  name        = "dbt-transform-trigger"
  description = "Automatically run dbt when GitLab data is updated"
  location    = "us-central1"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^master$"
    }
  }

  service_account = google_service_account.dbt_cloud_build.id

  filename = "warehouse/bigquery/dbt/cloudbuild-trigger.yaml"

  substitutions = {
    _GCP_PROJECT_ID = var.project_id
  }
}
