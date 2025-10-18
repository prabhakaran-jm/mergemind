# GitLab Demo Resources Terraform Configuration - Simplified
# This creates demo projects and sample files

# Configure GitLab Provider
provider "gitlab" {
  token    = var.gitlab_token
  base_url = var.gitlab_base_url
}

# Demo Projects - Simplified configuration
resource "gitlab_project" "demo_frontend" {
  name                   = "mergemind-demo-frontend"
  description            = "Frontend application for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled = true
  wiki_enabled           = false
  snippets_enabled       = false
}

resource "gitlab_project" "demo_backend" {
  name                   = "mergemind-demo-backend"
  description            = "Backend API for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled = true
  wiki_enabled           = false
  snippets_enabled       = false
}

resource "gitlab_project" "demo_api" {
  name                   = "mergemind-demo-api"
  description            = "API service for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled = true
  wiki_enabled           = false
  snippets_enabled       = false
}
