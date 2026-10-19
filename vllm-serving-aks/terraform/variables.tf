variable "location" {
  description = "Azure region. Must have approved NCASv3_T4 (T4 GPU) quota."
  type        = string
  default     = "koreacentral"
}

variable "cluster_name" {
  description = "AKS cluster name (also used for the resource group: rg-<name>)."
  type        = string
  default     = "vllm-serving-aks"
}

variable "kubernetes_version" {
  description = "AKS Kubernetes version. null = let AKS pick its default (run `az aks get-versions --location <loc> -o table` to see options)."
  type        = string
  default     = null
}

variable "system_vm_size" {
  description = "CPU system node pool VM size (CoreDNS, controllers). DSv3 family (Standard_D2s_v3 = 2 vCPUs, fits student quota)."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "enable_gpu_node_pool" {
  description = "Set to true to provision the GPU node pool and NVIDIA GPU Operator. Set to false when waiting for Azure GPU quota approval."
  type        = bool
  default     = false
}

variable "gpu_vm_size" {
  description = "GPU node pool VM size. Standard_NC4as_T4_v3 = 1x NVIDIA T4 16GB (cheapest Azure GPU). Requires 4 vCPUs quota."
  type        = string
  default     = "Standard_NC4as_T4_v3"
}

