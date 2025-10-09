terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.36" # recent
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Static external IP
resource "google_compute_address" "gitlab_ip" {
  name   = "gitlab-static-ip"
  region = var.region
}

# Firewall: 22, 80, 443 (targets instances with tag "gitlab")
resource "google_compute_firewall" "gitlab_fw" {
  name    = "allow-gitlab-80-443-22"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443"]
  }

  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gitlab"]
}

# GitLab VM
resource "google_compute_instance" "gitlab" {
  name         = "gitlab-ce"
  machine_type = var.machine_type
  tags         = ["gitlab", "http-server", "https-server"]

  advanced_machine_features {
    threads_per_core = 2
  }

  boot_disk {
    auto_delete = true
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
      size  = 20
      type  = "pd-ssd"
    }
  }

  # Secondary SSD for GitLab data
  attached_disk {
    device_name = "gitlab-data"
    type        = "PERSISTENT"
    mode        = "READ_WRITE"
    disk_encryption_key_raw = null
    # Create disk inline:
    initialize_params {
      size  = 50
      type  = "pd-ssd"
    }
    auto_delete = true
  }

  network_interface {
    # default VPC
    network = "default"
    access_config {
      nat_ip = google_compute_address.gitlab_ip.address
    }
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  # Useful metadata (available via instance metadata)
  metadata = {
    enable-oslogin = "TRUE"
    # Pass a friendly hostname hint; you will still configure EXTERNAL_URL in bootstrap.
    gitlab-host-hint = "${google_compute_address.gitlab_ip.address}.sslip.io"
  }

  service_account {
    # Default SA is fine for demo; optionally create a dedicated SA.
    scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write",
      "https://www.googleapis.com/auth/devstorage.read_write"
    ]
  }
}
