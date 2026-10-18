resource "google_container_cluster" "primary" {
  name     = "${var.cluster_name}-${var.environment}"
  location = var.gcp_region

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # GKE Autopilot mode handles node provisioning, autoscaling, and OS patching
  enable_autopilot = var.enable_autopilot

  ip_allocation_policy {
    cluster_secondary_range_name  = "k8s-pod-range"
    services_secondary_range_name = "k8s-service-range"
  }

  release_channel {
    channel = "REGULAR"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All Networks (Configurable per environment)"
    }
  }

  resource_labels = local.common_labels

  deletion_protection = false
}
