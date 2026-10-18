locals {
  name_prefix = "${var.environment}-anime-rec"

  common_labels = {
    project     = "hybrid-anime-recommender"
    environment = var.environment
    managed_by  = "terraform"
    owner       = "mlops-platform"
  }

  raw_data_bucket = "anime-recommender-data-${var.gcp_project_id}"
  dvc_data_bucket = "anime-recommender-dvc-${var.gcp_project_id}"
}
