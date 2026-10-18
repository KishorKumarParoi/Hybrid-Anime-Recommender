output "s3_bucket_name" {
  description = "Name of the secure S3 remote state bucket"
  value       = aws_s3_bucket.tf_state.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 remote state bucket"
  value       = aws_s3_bucket.tf_state.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB state locking table"
  value       = aws_dynamodb_table.tf_locks.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB state locking table"
  value       = aws_dynamodb_table.tf_locks.arn
}

output "kms_key_arn" {
  description = "ARN of the customer-managed KMS key used for encrypting S3 & DynamoDB"
  value       = aws_kms_key.tf_state_key.arn
}

output "backend_config_snippet" {
  description = "HCL backend configuration snippet to paste into terraform/aws/main.tf"
  value       = <<EOT
backend "s3" {
  bucket         = "${aws_s3_bucket.tf_state.id}"
  key            = "aws/terraform.tfstate"
  region         = "${var.aws_region}"
  dynamodb_table = "${aws_dynamodb_table.tf_locks.name}"
  encrypt        = true
  kms_key_id     = "${aws_kms_key.tf_state_key.arn}"
}
EOT
}
