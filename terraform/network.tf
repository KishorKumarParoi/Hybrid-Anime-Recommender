resource "google_compute_network" "vpc" {
  name                    = "${var.network_name}-${var.environment}"
  auto_create_subnetworks = false
  description             = "VPC network for Hybrid Anime Recommender platform"
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "${var.subnet_name}-${var.environment}"
  ip_cidr_range            = "10.10.0.0/20"
  region                   = var.gcp_region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "k8s-pod-range"
    ip_cidr_range = "10.48.0.0/14"
  }

  secondary_ip_range {
    range_name    = "k8s-service-range"
    ip_cidr_range = "10.52.0.0/20"
  }
}

# Cloud Router and NAT for outbound egress (pulling models, pip, packages)
resource "google_compute_router" "router" {
  name    = "${local.name_prefix}-router"
  region  = var.gcp_region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${local.name_prefix}-nat"
  router                             = google_compute_router.router.name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall Rule: Allow Inbound HTTP/HTTPS to Services
resource "google_compute_firewall" "allow_http" {
  name    = "${local.name_prefix}-allow-http"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "5000", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["anime-rec-node", "gke-node"]
}

# Firewall Rule: Allow GCP Health Checks for LoadBalancers
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.name_prefix}-allow-health-checks"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["5000", "80", "8080"]
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  target_tags   = ["anime-rec-node", "gke-node"]
}
