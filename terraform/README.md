# Terraform Infrastructure as Code for Hybrid Anime Recommender

Automated, production-grade Infrastructure-as-Code (IaC) that provisions **Google Cloud Platform (GCP)** infrastructure and delivers the application via **Helm**.

---

## 🏛️ Architecture Overview

```text
+-------------------------------------------------------------------------------+
|                             TERRAFORM PROVISIONS                              |
|                                                                               |
|  1. Custom VPC & Subnets      -> Pod range (10.48.0.0/14), Service (10.52/20)|
|  2. Cloud Router & Cloud NAT  -> Secure outbound egress without public IPs    |
|  3. Cloud Storage (GCS)       -> Raw datasets & DVC remote model weights      |
|  4. Artifact Registry         -> Docker container image repository            |
|  5. GKE Autopilot Cluster     -> Serverless, auto-scaling Kubernetes cluster  |
|  6. Helm Provider             -> Deploys helm/hybrid-anime-recommender        |
+-------------------------------------------------------------------------------+
```

---

## 📁 File Structure

```
terraform/
├── versions.tf          # Provider constraints (google, helm, kubernetes)
├── variables.tf         # Typed variables with descriptions & validation
├── locals.tf            # Naming conventions & common labels
├── network.tf           # VPC, subnets with secondary ranges, Cloud NAT, firewall
├── storage.tf           # GCS buckets (datasets/DVC) and Artifact Registry
├── gke.tf               # GKE Autopilot cluster configuration
├── helm.tf              # Automated Helm deployment using helm_release
├── outputs.tf           # Endpoint URLs, bucket names, and repo IDs
├── terraform.tfvars.example
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure you are authenticated with Google Cloud:
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project project-53d8ce01-b0e0-4f8b-94c
```

### 2. Configure Variables
Copy the example variables file:
```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

### 3. Initialize & Validate
```bash
cd terraform
terraform init
terraform validate
```

### 4. Review the Plan
```bash
terraform plan
```

### 5. Deploy Infrastructure & App
```bash
terraform apply -auto-approve
```

### 6. Clean Up / Destroy
```bash
terraform destroy
```
