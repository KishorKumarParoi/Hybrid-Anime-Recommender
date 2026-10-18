terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project
      ManagedBy   = "Terraform"
      Environment = var.environment
      Purpose     = "TerraformStateBackendSecurity"
    }
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  bucket_name = var.bucket_name_override != "" ? var.bucket_name_override : "${var.project}-tfstate-${random_id.bucket_suffix.hex}"
}

# ─── 1. Customer-Managed KMS Key for Encryption at Rest ───────────────────────

resource "aws_kms_key" "tf_state_key" {
  description             = "KMS Key for Terraform remote state S3 bucket and DynamoDB lock table"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableRootAccountManagement"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "tf_state_key_alias" {
  name          = "alias/${var.project}-tfstate-key"
  target_key_id = aws_kms_key.tf_state_key.key_id
}

data "aws_caller_identity" "current" {}

# ─── 2. Secure S3 Bucket for Remote State ─────────────────────────────────────

resource "aws_s3_bucket" "tf_state" {
  bucket        = local.bucket_name
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

# 2a. S3 Versioning (Prevents accidental overwrites or state corruption)
resource "aws_s3_bucket_versioning" "tf_state_versioning" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 2b. Server-Side Encryption (KMS with Bucket Key enabled for cost reduction)
resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state_crypto" {
  bucket = aws_s3_bucket.tf_state.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.tf_state_key.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# 2c. Strict Public Access Block (Blocks all public read, write, ACL, or policies)
resource "aws_s3_bucket_public_access_block" "tf_state_access_block" {
  bucket = aws_s3_bucket.tf_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2d. Bucket Policy: Enforce TLS 1.2+ and reject unencrypted HTTP transfers
resource "aws_s3_bucket_policy" "tf_state_enforce_tls" {
  bucket     = aws_s3_bucket.tf_state.id
  depends_on = [aws_s3_bucket_public_access_block.tf_state_access_block]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.tf_state.arn,
          "${aws_s3_bucket.tf_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "DenyIncorrectEncryptionHeader"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.tf_state.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      }
    ]
  })
}

# 2e. S3 Lifecycle: Expire old non-current state versions after 180 days
resource "aws_s3_bucket_lifecycle_configuration" "tf_state_lifecycle" {
  bucket = aws_s3_bucket.tf_state.id

  rule {
    id     = "expire-stale-noncurrent-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_transition {
      noncurrent_days = 60
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 180
    }
  }
}


# ─── 3. DynamoDB State Lock Table with Encryption & Recovery ──────────────────

resource "aws_dynamodb_table" "tf_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.tf_state_key.arn
  }

  tags = {
    Name        = var.lock_table_name
    Description = "Terraform state concurrency lock table"
  }
}
