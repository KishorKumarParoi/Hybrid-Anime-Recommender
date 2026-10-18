variable "gcp_project_id" {
  type        = string
  description = "The Google Cloud Platform project ID"
  default     = "project-53d8ce01-b0e0-4f8b-94c"

  validation {
    condition     = length(var.gcp_project_id) > 3
    error_message = "Project ID must be a valid GCP project identifier."
  }
}

variable "gcp_region" {
  type        = string
  description = "The GCP primary compute and storage region"
  default     = "us-central1"
}

variable "gcp_zone" {
  type        = string
  description = "The GCP primary compute zone"
  default     = "us-central1-a"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "cluster_name" {
  type        = string
  description = "The name of the GKE cluster"
  default     = "hybrid-anime-cluster"
}

variable "network_name" {
  type        = string
  description = "The VPC network name"
  default     = "anime-rec-vpc"
}

variable "subnet_name" {
  type        = string
  description = "The subnet name for the GKE cluster"
  default     = "anime-rec-subnet"
}

variable "enable_autopilot" {
  type        = bool
  description = "Deploy GKE in Autopilot mode (fully managed) or Standard mode"
  default     = true
}

variable "deploy_helm" {
  type        = bool
  description = "Whether to automatically deploy the hybrid-anime-recommender Helm chart"
  default     = true
}

variable "image_tag" {
  type        = string
  description = "Container image tag to deploy via Helm"
  default     = "latest"
}

variable "artifact_registry_name" {
  type        = string
  description = "Google Artifact Registry repository name for Docker images"
  default     = "anime-recommender-repo"
}

variable "groq_api_key" {
  type        = string
  description = "Groq API key for AI agent reasoning"
  sensitive   = true
  default     = ""
}

variable "api_key" {
  type        = string
  description = "API authentication key for client access"
  sensitive   = true
  default     = ""
}

