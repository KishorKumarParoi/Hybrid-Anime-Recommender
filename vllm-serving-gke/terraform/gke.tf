resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  # Remove the default node pool to manage separate system and GPU pools explicitly
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.self_link
  subnetwork = google_compute_subnetwork.subnet.self_link

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  # Enable Kubernetes NetworkPolicy for Zero-Trust pod isolation
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  addons_config {
    network_policy_config {
      disabled = false
    }
  }

  # Workload Identity for least-privilege pod IAM (no hardcoded credentials)
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  deletion_protection = false

  resource_labels = {
    project = var.cluster_name
  }
}

# CPU System Node Pool (CoreDNS, kube-system controllers, Ingress)
resource "google_container_node_pool" "system" {
  name     = "system-pool"
  location = var.zone
  cluster  = google_container_cluster.primary.id

  node_count = 1

  node_config {
    machine_type = var.system_machine_type
    disk_size_gb = 50
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      workload = "system"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

# Dedicated GPU Node Pool (NVIDIA L4 or T4) with Automated Certified Driver Injection & Autoscaling
resource "google_container_node_pool" "gpu" {
  count    = var.enable_gpu_node_pool ? 1 : 0
  name     = "gpu-pool"
  location = var.zone
  cluster  = google_container_cluster.primary.id

  # Cost Optimization: Scale to 0 when idle
  autoscaling {
    min_node_count = 0
    max_node_count = 1
  }

  node_config {
    machine_type = var.gpu_machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-balanced"
    spot         = var.spot

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    guest_accelerator {
      type  = var.gpu_type
      count = 1
      gpu_driver_installation_config {
        gpu_driver_version = "DEFAULT"
      }
    }

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }

    labels = {
      workload = "gpu"
    }

    # Security: Conceal Google Cloud metadata server from pods (SSRF prevention)
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}
