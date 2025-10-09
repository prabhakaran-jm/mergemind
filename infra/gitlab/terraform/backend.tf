terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.36" # recent
    }
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 16.0"
    }
  }
  
  backend "gcs" {
    bucket = "terraform-state-ai-accelerate-mergemind"
    prefix = "gitlab-infrastructure"
  }
}
