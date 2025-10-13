# Terraform Remote Backend Configuration
# This configuration reuses the existing GitLab remote backend with a different prefix

terraform {
  backend "gcs" {
    # Reuse existing GitLab backend bucket
    bucket = "terraform-state-ai-accelerate-mergemind"
    
    # Use different prefix for MergeMind infrastructure
    prefix = "mergemind/terraform.tfstate"
    
    # Enable state locking
    # This prevents concurrent modifications to the same state
  }
}

# Note: This reuses the existing backend bucket from GitLab setup
# The bucket should already exist, so you can directly run:
# terraform init -migrate-state
