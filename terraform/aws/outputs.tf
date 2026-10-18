output "alb_dns" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "app_url" {
  description = "Primary URL endpoint for the Hybrid Anime Recommender service"
  value       = local.https_enabled ? "https://${aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}"
}

output "pyrit_dashboard_url" {
  description = "Direct URL for the PyRIT Red Teaming Dashboard"
  value       = "http://${aws_lb.main.dns_name}:8001"
}

output "app_ecr_url" {
  description = "Amazon ECR repository URL for the main application"
  value       = aws_ecr_repository.app.repository_url
}

output "pyrit_ecr_url" {
  description = "Amazon ECR repository URL for PyRIT red team container"
  value       = aws_ecr_repository.pyrit.repository_url
}

output "tensorzero_ecr_url" {
  description = "Amazon ECR repository URL for TensorZero sidecar"
  value       = aws_ecr_repository.tensorzero.repository_url
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary cluster connection endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "db_endpoint" {
  description = "RDS PostgreSQL database endpoint connection string"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "bedrock_guardrail_id" {
  description = "AWS Bedrock Content & Injection Safety Guardrail ID"
  value       = aws_bedrock_guardrail.main.guardrail_id
}

output "bedrock_guardrail_arn" {
  description = "AWS Bedrock Content & Injection Safety Guardrail ARN"
  value       = aws_bedrock_guardrail.main.guardrail_arn
}

output "secrets_manager_config_arn" {
  description = "AWS Secrets Manager ARN holding runtime application configuration"
  value       = aws_secretsmanager_secret.config.arn
}

output "cloudfront_domain_name" {
  description = "CloudFront global edge distribution domain name"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "s3_static_bucket" {
  description = "S3 bucket for static SPA assets and ML model weights"
  value       = aws_s3_bucket.static_cdn.bucket
}

output "docdb_endpoint" {
  description = "Amazon DocumentDB (MongoDB compatible) cluster endpoint"
  value       = aws_docdb_cluster.main.endpoint
}

output "docdb_cluster_id" {
  description = "Amazon DocumentDB cluster identifier"
  value       = aws_docdb_cluster.main.id
}

