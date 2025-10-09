output "gitlab_external_ip" {
  description = "Static external IP for GitLab"
  value       = google_compute_address.gitlab_ip.address
}

output "suggested_gitlab_host" {
  description = "Convenient host using sslip.io (works with Let's Encrypt)"
  value       = "${google_compute_address.gitlab_ip.address}.sslip.io"
}

output "ssh_command" {
  description = "SSH command from Cloud Shell"
  value       = "gcloud compute ssh gitlab-ce --zone ${var.zone}"
}

output "instance_url_http" {
  value       = "http://${google_compute_address.gitlab_ip.address}"
  description = "HTTP URL before TLS is configured"
}
