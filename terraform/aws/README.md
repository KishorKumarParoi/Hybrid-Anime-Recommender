# AWS Production Infrastructure for Hybrid Anime Recommender & AI Security Platform

This directory contains the production-grade Terraform stack for deploying the **Hybrid Anime Recommender**, **AI Security Guardrails**, and **Autonomous Research Agent** on Amazon Web Services (AWS), adapted directly from the enterprise architecture in `190 - AI SECURITY PROJECT MATERIALS`.

---

## Architecture Overview

```text
               +-------------------------------------------------------+
               |                  Amazon Web Services                  |
               |                                                       |
               |   +-----------------------------------------------+   |
               |   |            Custom VPC (10.0.0.0/16)           |   |
               |   |                                               |   |
               |   |   +---------------------------------------+   |   |
               |   |   | Public Subnets (10.0.0.0/24, 10.0.1.0)|   |   |
               |   |   | - Application Load Balancer (ALB)     |   |   |
               |   |   |   Port 80/443 (App), Port 8001 (PyRIT)|   |   |
               |   |   +-------------------+-------------------+   |   |
               |   |                       |                       |   |
               |   |   +-------------------v-------------------+   |   |
               |   |   | Private Subnets (10.0.10.0, 10.0.11.0)|   |   |
               |   |   |                                       |   |   |
               |   |   | +-----------------------------------+ |   |   |
               |   |   | | ECS Fargate Cluster               | |   |   |
               |   |   | | - App Task (FastAPI + TensorZero) | |   |   |
               |   |   | | - PyRIT Red Team Task             | |   |   |
               |   |   | | - Target Tracking Auto-Scaler     | |   |   |
               |   |   | +-----------------+-----------------+ |   |   |
               |   |   |                   |                   |   |   |
               |   |   | +-----------------v-----------------+ |   |   |
               |   |   | | ElastiCache Redis 7.1             | |   |   |
               |   |   | | - Semantic Vector Cache           | |   |   |
               |   |   | | - Session Memory & Job Queue      | |   |   |
               |   |   | +-----------------+-----------------+ |   |   |
               |   |   |                   |                   |   |   |
               |   |   | +-----------------v-----------------+ |   |   |
               |   |   | | RDS PostgreSQL 15.8 (pgvector)    | |   |   |
               |   |   | | - Long-term Research Memory       | |   |   |
               |   |   | | - Autonomous Dossier Store        | |   |   |
               |   |   | +-----------------------------------+ |   |   |
               |   |   |                                       |   |   |
               |   |   | +-----------------------------------+ |   |   |
               |   |   | | VPC Endpoints (No NAT Gateway)    | |   |   |
               |   |   | | - ECR, S3, Secrets Manager,       | |   |   |
               |   |   | |   Bedrock Runtime, CloudWatch Logs| |   |   |
               |   |   | +-----------------------------------+ |   |   |
               |   |   +---------------------------------------+   |   |
               |   |                                               |   |
               |   |   +---------------------------------------+   |   |
               |   |   | AWS Bedrock Content Safety Guardrail  |   |   |
               |   |   | - High Strength Prompt Attack Shield  |   |   |
               |   |   | - PII Redaction & Blocking            |   |   |
               |   |   | - Toxic Topic Deny Filters            |   |   |
               |   |   +---------------------------------------+   |   |
               |   |                                               |   |
               |   |   +---------------------------------------+   |   |
               |   |   | EventBridge Weekly Scheduled Audit    |   |   |
               |   |   | - Runs PyRIT Red Team automated audit |   |   |
               |   |   +---------------------------------------+   |   |
               |   +-----------------------------------------------+   |
               +-------------------------------------------------------+
```

---

## Key Features & Enterprise Components

1. **Bedrock Guardrail Integration (`aws_bedrock_guardrail.main`)**:
   - `PROMPT_ATTACK` filter with `HIGH` input strength.
   - PII blocking (`US_SOCIAL_SECURITY_NUMBER`, `CREDIT_DEBIT_CARD_NUMBER`, `AWS_ACCESS_KEY`).
   - PII anonymization (`EMAIL`, `PHONE`).
   - Managed profanity list and policy deny topics (`weapons`, `illegal_activities`, `self_harm`).

2. **Zero NAT Gateway Egress Architecture (Cost-Optimized)**:
   - Private subnets communicate with AWS managed services via Interface VPC Endpoints (`ECR`, `Secrets Manager`, `Bedrock Runtime`, `CloudWatch Logs`) and S3 Gateway Endpoint, completely eliminating expensive NAT Gateway hourly and data transfer fees.

3. **Autonomous Research Agent Storage**:
   - **ElastiCache Redis 7.1**: Real-time semantic vector caching (<5ms cache hits) and Redis Streams task coordination.
   - **RDS PostgreSQL 15.8**: Multi-AZ capable database for storing research dossiers, user profiles, and vector embeddings.

4. **Automated Weekly Red Teaming (EventBridge + PyRIT)**:
   - AWS EventBridge triggers an ECS Fargate standalone task running Microsoft PyRIT every Monday at 02:00 AM UTC to automatically probe the API for prompt injection vulnerabilities, jailbreaks, and sensitive data leakage.

5. **Secrets Management**:
   - AWS Secrets Manager securely stores the runtime JSON configuration consumed by the app and the TensorZero sidecar (`GROQ_API_KEY`, `OPENAI_API_KEY`, database credentials, cache parameters).

---

## Terraform Remote State Backend Security (S3 + DynamoDB)

Before running `terraform apply`, provision the secure state storage using either the automated CLI script or the dedicated Terraform bootstrap module:

### Security Controls Enforced:
1. **S3 Versioning**: Protects against catastrophic state corruption, human error, and allows point-in-time state rollbacks.
2. **KMS / SSE-S3 Encryption**: All state files (which may contain sensitive metadata or connection strings) are encrypted at rest with customer-managed KMS keys or AES-256.
3. **Public Access Block**: All four S3 public access vectors are strictly blocked (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`).
4. **TLS 1.2+ Transport Enforcement**: A bucket policy rejects any unencrypted HTTP requests (`aws:SecureTransport = false`).
5. **DynamoDB Concurrency Locking**: Prevents simultaneous deployments from conflicting or corrupting the `.tfstate` file, configured with `PAY_PER_REQUEST` billing, server-side encryption, and Point-in-Time Recovery (PITR).
6. **Automated Lifecycle Expiration**: Retains historical state versions while transitioning stale non-current versions to cost-effective storage.

### Option A: Pure Terraform Bootstrap Module (Recommended)
```bash
cd terraform/aws/bootstrap
terraform init
terraform apply -out=tfplan
terraform apply tfplan
```
This module outputs the exact `backend "s3" { ... }` block to paste into `terraform/aws/main.tf`.

### Option B: Automated CLI Script (Inspired by 190 Materials)
```bash
cd terraform/aws
./bootstrap.sh us-east-1 hybrid-anime-recommender
```

---

## How to Deploy the Platform

### Step 1: Initialize Terraform
```bash
cd terraform/aws
terraform init
```

### Step 2: Configure Variables
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Groq API key and desired settings
```

### Step 3: Plan and Apply
```bash
terraform plan -out=tfplan
terraform apply tfplan
```

### Step 4: Access Outputs
```bash
terraform output alb_dns
terraform output app_url
terraform output pyrit_dashboard_url
```

