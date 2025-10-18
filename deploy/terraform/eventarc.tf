# Simplified event-driven dbt pipeline
# Fivetran connector calls Cloud Function directly when sync completes

# Enable required APIs
resource "google_project_service" "cloudfunctions" {
  service = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "logging" {
  service = "logging.googleapis.com"
  disable_on_destroy = false
}

# Service account for Cloud Function
resource "google_service_account" "dbt_trigger_function_sa" {
  account_id   = "dbt-trigger-function"
  display_name = "dbt Trigger Function Service Account"
  description  = "Service account for Cloud Function that triggers dbt runs"
}

# IAM roles for Cloud Function service account
resource "google_project_iam_member" "dbt_function_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.dbt_trigger_function_sa.email}"
}

resource "google_project_iam_member" "dbt_function_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.dbt_trigger_function_sa.email}"
}

resource "google_project_iam_member" "dbt_function_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.dbt_trigger_function_sa.email}"
}

# Cloud Storage bucket for Cloud Function source code
resource "google_storage_bucket" "dbt_function_source" {
  name     = "${var.project_id}-dbt-function-source"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = "mergemind"
    component   = "event-driven-dbt"
  }
}

# Single Cloud Function that runs dbt when called by Fivetran connector
resource "google_cloudfunctions2_function" "dbt_trigger_function" {
  name        = "dbt-trigger-function"
  location    = var.region
  description = "HTTP-triggered Cloud Function that runs dbt transformations (v2 with dbt dependencies)"

  build_config {
    runtime     = "python311"
    entry_point = "trigger_dbt_run"
    
    source {
      storage_source {
        bucket = google_storage_bucket.dbt_function_source.name
        object = "dbt-trigger-function.zip"
      }
    }
  }


  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "512M"
    timeout_seconds       = 540
    service_account_email = google_service_account.dbt_trigger_function_sa.email
    ingress_settings      = "ALLOW_ALL"  # Allow unauthenticated HTTP requests
    
    environment_variables = {
      PROJECT_ID        = var.project_id
      BQ_DATASET_RAW    = var.bq_dataset_raw
      BQ_DATASET_MODELED = var.bq_dataset_modeled
      DBT_PROFILES_DIR  = "/tmp"
      GCP_PROJECT_ID    = var.project_id
      AUTH_TOKEN        = var.dbt_trigger_auth_token
    }
  }

  depends_on = [
    google_project_service.cloudfunctions,
    google_storage_bucket.dbt_function_source
  ]
}

# Note: Cloud Function source is uploaded via deploy_function.sh script
# The zip file is created dynamically and uploaded to Cloud Storage
# Run ./deploy_function.sh before terraform apply

# Allow unauthenticated invocations of the Cloud Function
resource "google_cloud_run_service_iam_member" "dbt_trigger_function_invoker" {
  location = google_cloudfunctions2_function.dbt_trigger_function.location
  service  = google_cloudfunctions2_function.dbt_trigger_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the Cloud Function URL for Fivetran connector
output "dbt_trigger_function_url" {
  description = "URL to trigger dbt runs via HTTP (call this from Fivetran connector)"
  value       = google_cloudfunctions2_function.dbt_trigger_function.service_config[0].uri
}