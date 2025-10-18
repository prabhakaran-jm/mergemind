# Outputs for GitLab Demo Resources

output "demo_projects" {
  description = "Created demo projects"
  value = {
    frontend = {
      id   = gitlab_project.demo_frontend.id
      name = gitlab_project.demo_frontend.name
      url  = gitlab_project.demo_frontend.web_url
    }
    backend = {
      id   = gitlab_project.demo_backend.id
      name = gitlab_project.demo_backend.name
      url  = gitlab_project.demo_backend.web_url
    }
    api = {
      id   = gitlab_project.demo_api.id
      name = gitlab_project.demo_api.name
      url  = gitlab_project.demo_api.web_url
    }
  }
}

output "project_ids_for_config" {
  description = "Project IDs for Fivetran connector configuration"
  value = [
    gitlab_project.demo_frontend.id,
    gitlab_project.demo_backend.id,
    gitlab_project.demo_api.id
  ]
}

output "gitlab_info" {
  description = "GitLab instance information"
  value = {
    base_url = var.gitlab_base_url
    projects_created = 3
    branches_created = 3
    note = "Merge requests and issues need to be created manually via web interface or API"
  }
}
