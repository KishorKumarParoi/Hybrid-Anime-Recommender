output "cluster_name" {
  description = "The name of the provisioned GKE cluster."
  value       = google_container_cluster.primary.name
}

output "zone" {
  description = "The zone where the cluster is running."
  value       = var.zone
}

output "project_id" {
  description = "The GCP project ID."
  value       = var.project_id
}

output "configure_kubectl" {
  description = "Command to connect kubectl to your GKE cluster."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.zone} --project ${var.project_id}"
}
