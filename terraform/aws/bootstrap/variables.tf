variable "aws_region" {
  description = "AWS region for Terraform state infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project identifier used in naming"
  type        = string
  default     = "hybrid-anime-recommender"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "bucket_name_override" {
  description = "Optional custom name for the S3 state bucket. If blank, a globally unique name will be generated."
  type        = string
  default     = ""
}

variable "lock_table_name" {
  description = "Name of DynamoDB state locking table"
  type        = string
  default     = "hybrid-anime-recommender-tf-locks"
}
