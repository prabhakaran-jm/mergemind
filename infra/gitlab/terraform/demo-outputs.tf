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

output "demo_merge_requests" {
  description = "Created demo merge requests"
  value = {
    frontend_auth = {
      id    = gitlab_merge_request.frontend_auth_mr.iid
      title = gitlab_merge_request.frontend_auth_mr.title
      url   = gitlab_merge_request.frontend_auth_mr.web_url
    }
    backend_auth = {
      id    = gitlab_merge_request.backend_auth_mr.iid
      title = gitlab_merge_request.backend_auth_mr.title
      url   = gitlab_merge_request.backend_auth_mr.web_url
    }
    api_auth = {
      id    = gitlab_merge_request.api_auth_mr.iid
      title = gitlab_merge_request.api_auth_mr.title
      url   = gitlab_merge_request.api_auth_mr.web_url
    }
  }
}

output "demo_issues" {
  description = "Created demo issues"
  value = {
    frontend_auth = {
      id    = gitlab_issue.frontend_auth_issue.iid
      title = gitlab_issue.frontend_auth_issue.title
      url   = gitlab_issue.frontend_auth_issue.web_url
    }
    backend_auth = {
      id    = gitlab_issue.backend_auth_issue.iid
      title = gitlab_issue.backend_auth_issue.title
      url   = gitlab_issue.backend_auth_issue.web_url
    }
    api_auth = {
      id    = gitlab_issue.api_auth_issue.iid
      title = gitlab_issue.api_auth_issue.title
      url   = gitlab_issue.api_auth_issue.web_url
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
