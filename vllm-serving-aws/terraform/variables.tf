variable "aws_region" {
  description = "AWS region to deploy EKS infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the Amazon EKS cluster."
  type        = string
  default     = "vllm-serving-aws"
}

variable "cluster_version" {
  description = "Kubernetes control plane version."
  type        = string
  default     = "1.30"
}

variable "system_instance_types" {
  description = "EC2 instance types for the CPU system managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "gpu_instance_types" {
  description = "EC2 instance types for the GPU node group (g4dn.xlarge = 1x NVIDIA T4 16GB; g5.xlarge = 1x NVIDIA A10G 24GB)."
  type        = list(string)
  default     = ["g4dn.xlarge"]
}

variable "enable_gpu_node_group" {
  description = "Toggle to enable/disable the GPU node group."
  type        = bool
  default     = true
}

variable "spot_gpu" {
  description = "Whether to use AWS Spot Instances for the GPU node group to save ~70%."
  type        = bool
  default     = false
}
