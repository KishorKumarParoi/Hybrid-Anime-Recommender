terraform {
  required_version = ">= 1.15"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = var.zone
  credentials = fileexists("${path.module}/../../project-53d8ce01-b0e0-4f8b-94c-49d8c945edc2.json") ? file("${path.module}/../../project-53d8ce01-b0e0-4f8b-94c-49d8c945edc2.json") : null
}

# Authenticate Kubernetes provider against the created GKE cluster
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}
