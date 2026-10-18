# 1. GCS Bucket for Raw Datasets and Model Artifacts
resource "google_storage_bucket" "raw_data" {
  name                        = local.raw_data_bucket
  location                    = var.gcp_region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = local.common_labels
}

# 2. GCS Bucket for DVC Data & Model Versioning
resource "google_storage_bucket" "dvc_remote" {
  name                        = local.dvc_data_bucket
  location                    = var.gcp_region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  labels = local.common_labels
}

# 3. Google Artifact Registry for Container Images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = var.artifact_registry_name
  description   = "Docker container registry for Hybrid Anime Recommender platform"
  format        = "DOCKER"

  labels = local.common_labels
}
