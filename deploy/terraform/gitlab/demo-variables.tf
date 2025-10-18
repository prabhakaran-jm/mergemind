# Variables for GitLab Demo Resources

variable "gitlab_token" {
  description = "GitLab personal access token"
  type        = string
  sensitive   = true
}

variable "gitlab_base_url" {
  description = "GitLab base URL"
  type        = string
  default     = "https://your-gitlab-domain.com/api/v4/"
}

variable "demo_user_email" {
  description = "Email for demo commits"
  type        = string
  default     = "demo@example.com"
}

variable "demo_user_name" {
  description = "Name for demo commits"
  type        = string
  default     = "Demo User"
}
