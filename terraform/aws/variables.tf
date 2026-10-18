variable "aws_region" {
  description = "AWS region for provisioning resources"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name prefix for AWS resources"
  type        = string
  default     = "hybrid-anime-recommender"
}

variable "app_image" {
  description = "ECR image URI or Docker Hub image for the Hybrid Anime Recommender app"
  type        = string
  default     = "kishorkumarparoi/hybrid-anime-recommender:latest"
}

variable "pyrit_image" {
  description = "ECR image URI for the PyRIT automated red teaming dashboard"
  type        = string
  default     = "kishorkumarparoi/pyrit-dashboard:latest"
}

variable "tensorzero_image" {
  description = "ECR image URI for TensorZero gateway sidecar"
  type        = string
  default     = "tensorzero/gateway:latest"
}

variable "api_key" {
  description = "API key for authenticating requests to the research agent"
  type        = string
  sensitive   = true
  default     = ""
}

variable "groq_api_key" {
  description = "Groq API key for LLaMA 3.3 70B inference"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (optional fallback for multi-agent reasoning)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langsmith_api_key" {
  description = "LangSmith API key for LLM tracing and LLM-as-judge evaluations"
  type        = string
  sensitive   = true
  default     = ""
}

variable "app_desired_count" {
  description = "Initial number of app ECS tasks"
  type        = number
  default     = 1
}

variable "app_min_capacity" {
  description = "Minimum number of app ECS tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "app_max_capacity" {
  description = "Maximum number of app ECS tasks for auto-scaling"
  type        = number
  default     = 5
}

variable "app_cpu" {
  description = "CPU units for app task (1024 = 1 vCPU)"
  type        = string
  default     = "2048"
}

variable "app_memory" {
  description = "Memory in MB for app task"
  type        = string
  default     = "4096"
}

variable "db_instance_class" {
  description = "RDS instance class for research dossier pgvector store"
  type        = string
  default     = "db.t3.micro"
}

variable "db_multi_az" {
  description = "Enable RDS Multi-AZ for high availability"
  type        = bool
  default     = false
}

variable "redis_node_type" {
  description = "ElastiCache node type for semantic vector caching"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "cpu_scale_target" {
  description = "Target CPU utilization percentage for ECS auto-scaling"
  type        = number
  default     = 70
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Leave empty to use HTTP only."
  type        = string
  default     = ""
}

variable "docdb_master_password" {
  description = "Master password for Amazon DocumentDB (MongoDB compatible) cluster"
  type        = string
  sensitive   = true
  default     = "DocumentDBP@ssw0rd2026!"
}

