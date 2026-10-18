# ==============================================================================
# AZURE EVENT HUBS (KAFKA STREAMING) & AI SECURITY - VARIABLES
# ==============================================================================

variable "project_name" {
  description = "Project name prefix used for all Azure resources"
  type        = string
  default     = "hybrid-anime"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "azure_region" {
  description = "Azure data center location"
  type        = string
  default     = "eastus"
}

variable "eventhub_sku" {
  description = "Azure Event Hubs pricing tier (Standard tier enables native Kafka 1.0+ surface)"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.eventhub_sku)
    error_message = "SKU must be Standard or Premium to support Kafka API."
  }
}

variable "eventhub_capacity" {
  description = "Base throughput units (1 TU = 1MB/s ingress, 2MB/s egress)"
  type        = number
  default     = 1
}

variable "auto_inflate_enabled" {
  description = "Enable automatic scaling of throughput units on traffic spikes"
  type        = bool
  default     = true
}

variable "max_throughput_units" {
  description = "Maximum throughput units when auto-inflate is enabled"
  type        = number
  default     = 5
}

variable "message_retention_days" {
  description = "Number of days to retain streaming messages in Event Hub topics"
  type        = number
  default     = 7
}

variable "partition_count" {
  description = "Number of partitions for high-throughput parallel event consumption"
  type        = number
  default     = 4
}
