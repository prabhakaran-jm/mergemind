# Outputs for MergeMind GCP Infrastructure

output "project_info" {
  description = "Project information"
  value = {
    project_id = var.project_id
    region     = var.region
    environment = var.environment
  }
}

output "enabled_apis" {
  description = "GCP APIs enabled (minimal set)"
  value = [
    "aiplatform.googleapis.com",
    "iam.googleapis.com", 
    "secretmanager.googleapis.com"
  ]
}

output "bigquery_datasets" {
  description = "BigQuery datasets (existing)"
  value = {
    mergemind = {
      dataset_id = "mergemind"
      location   = "US"
      project    = var.project_id
      note       = "existing dataset"
    }
    gitlab_connector_v1 = {
      dataset_id = "gitlab_connector_v1"
      location   = "US"
      project    = var.project_id
      note       = "existing dataset"
    }
  }
}

output "service_accounts" {
  description = "Service accounts created"
  value = {
    mergemind_api = {
      email       = google_service_account.mergemind_api.email
      name        = google_service_account.mergemind_api.name
      description = google_service_account.mergemind_api.description
    }
    vertex_ai = {
      email       = google_service_account.vertex_ai.email
      name        = google_service_account.vertex_ai.name
      description = google_service_account.vertex_ai.description
    }
  }
}

output "storage_buckets" {
  description = "Cloud Storage buckets created"
  value = {
    mergemind_data = {
      name     = google_storage_bucket.mergemind_data.name
      location = google_storage_bucket.mergemind_data.location
      url      = google_storage_bucket.mergemind_data.url
    }
  }
}

output "networking" {
  description = "Networking resources (using existing infrastructure)"
  value = {
    note = "Using existing VPC and networking infrastructure"
  }
}

output "secrets" {
  description = "Secret Manager secrets"
  value = {
    gitlab_token = {
      name = google_secret_manager_secret.gitlab_token.name
      id   = google_secret_manager_secret.gitlab_token.secret_id
    }
    vertex_ai_key = {
      name = google_secret_manager_secret.vertex_ai_key.name
      id   = google_secret_manager_secret.vertex_ai_key.secret_id
    }
  }
}

output "vertex_ai_config" {
  description = "Vertex AI configuration"
  value = {
    location = var.vertex_ai_location
    model    = var.vertex_ai_model
    enabled  = var.enable_vertex_ai
  }
}

output "bigquery_config" {
  description = "BigQuery configuration"
  value = {
    location      = var.bigquery_location
    slot_capacity = var.bigquery_slot_capacity
    enabled       = var.enable_bigquery
  }
}

output "monitoring_config" {
  description = "Monitoring configuration"
  value = {
    enabled = var.enable_monitoring
    logging = var.enable_logging
  }
}

output "security_config" {
  description = "Security configuration"
  value = {
    enabled = var.enable_security
    secrets = {
      gitlab_token_secret = var.gitlab_token_secret_name
      vertex_ai_key_secret = var.vertex_ai_key_secret_name
    }
  }
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    terraform_version = ">= 1.0"
    provider_version  = "~> 5.0"
    last_updated      = timestamp()
    environment       = var.environment
  }
}
