# Variables for MergeMind GCP Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "ai-accelerate-mergemind"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "bigquery_location" {
  description = "BigQuery Dataset Location"
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "enable_vertex_ai" {
  description = "Enable Vertex AI resources"
  type        = bool
  default     = true
}

variable "enable_bigquery" {
  description = "Enable BigQuery resources"
  type        = bool
  default     = true
}

variable "enable_storage" {
  description = "Enable Cloud Storage resources"
  type        = bool
  default     = true
}

variable "enable_networking" {
  description = "Enable VPC networking resources"
  type        = bool
  default     = true
}

variable "vertex_ai_location" {
  description = "Vertex AI Location"
  type        = string
  default     = "us-central1"
}

variable "vertex_ai_model" {
  description = "Vertex AI Model to use"
  type        = string
  default     = "gemini-2.0-flash-exp"
}

variable "bigquery_slot_capacity" {
  description = "BigQuery slot capacity for reservations"
  type        = number
  default     = 100
}

variable "storage_class" {
  description = "Cloud Storage class"
  type        = string
  default     = "STANDARD"
}

variable "retention_days" {
  description = "Data retention period in days"
  type        = number
  default     = 90
}

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable structured logging"
  type        = bool
  default     = true
}

variable "enable_security" {
  description = "Enable security features"
  type        = bool
  default     = true
}

variable "gitlab_token_secret_name" {
  description = "Name of the GitLab token secret in Secret Manager"
  type        = string
  default     = "gitlab-token"
}

variable "vertex_ai_key_secret_name" {
  description = "Name of the Vertex AI key secret in Secret Manager"
  type        = string
  default     = "vertex-ai-key"
}

variable "dbt_trigger_auth_token" {
  description = "Authentication token for dbt trigger Cloud Function"
  type        = string
  sensitive   = true
  default     = "your-secure-token-here"
}
