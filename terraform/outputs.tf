output "gke_cluster_name" {
  description = "Name of the provisioned GKE cluster"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "Kubernetes API endpoint for the cluster"
  value       = google_container_cluster.primary.endpoint
}

output "gcs_raw_data_bucket" {
  description = "Google Cloud Storage bucket for datasets and model weights"
  value       = google_storage_bucket.raw_data.name
}

output "gcs_dvc_remote_bucket" {
  description = "Google Cloud Storage bucket for DVC remote tracking"
  value       = google_storage_bucket.dvc_remote.name
}

output "artifact_registry_repo" {
  description = "Full URL to the Artifact Registry Docker repository"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.docker_repo.name}"
}

output "helm_release_status" {
  description = "Status of the automated Helm release"
  value       = length(helm_release.hybrid_anime_recommender) > 0 ? helm_release.hybrid_anime_recommender[0].status : "DEPLOY_HELM_FALSE"
}

output "cloud_armor_policy_name" {
  description = "Name of the provisioned Cloud Armor WAF security policy"
  value       = google_compute_security_policy.anime_cloud_armor.name
}

output "secret_manager_config_id" {
  description = "Google Secret Manager secret ID storing enterprise agent configuration"
  value       = google_secret_manager_secret.app_config.id
}

output "weekly_redteam_scheduler_job" {
  description = "Google Cloud Scheduler weekly red team security audit job name"
  value       = google_cloud_scheduler_job.weekly_security_audit.name
}

