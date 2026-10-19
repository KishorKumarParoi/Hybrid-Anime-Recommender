variable "project_id" {
  description = "The Google Cloud project ID where GKE will be provisioned."
  type        = string
  default     = "project-53d8ce01-b0e0-4f8b-94c"
}

variable "region" {
  description = "The GCP region for networking and cluster resources."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for the GKE zonal cluster (1 free zonal cluster per billing account: $0/mo control plane)."
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "The name of the GKE cluster."
  type        = string
  default     = "vllm-serving-gke"
}

variable "system_machine_type" {
  description = "Machine type for the CPU system node pool (CoreDNS, kube-system, ingress)."
  type        = string
  default     = "e2-standard-2"
}

variable "enable_gpu_node_pool" {
  description = "Whether to provision the dedicated GPU node pool."
  type        = bool
  default     = true
}

variable "gpu_machine_type" {
  description = "Machine type for the GPU node pool. g2-standard-4 (4 vCPU, 16GB RAM) natively attaches 1x NVIDIA L4 (24GB)."
  type        = string
  default     = "g2-standard-4"
}

variable "gpu_type" {
  description = "The accelerator type (e.g., nvidia-l4 or nvidia-tesla-t4)."
  type        = string
  default     = "nvidia-l4"
}

variable "spot" {
  description = "Whether to use Spot VMs for the GPU node pool to reduce cost by ~65-70%."
  type        = bool
  default     = false
}

variable "disk_size_gb" {
  description = "Boot disk size in GB for the worker nodes."
  type        = number
  default     = 60
}
