# vLLM Serving on Amazon Web Services (AWS EKS)

Production-grade Infrastructure-as-Code (Terraform) and Kubernetes manifests to serve large language models with **vLLM** on **Amazon Elastic Kubernetes Service (EKS)** using AWS GPU instances (`g4dn.xlarge` with NVIDIA T4 or `g5.xlarge` with NVIDIA A10G).

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------------+
|                                    AWS EKS ARCHITECTURE                                 |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   AWS Region: us-east-1 | Account: 789130777295                                         |
|                                                                                         |
|   +---------------------------------------------------------------------------------+   |
|   | Amazon EKS Control Plane (v1.30, Managed High-Availability across AZs)          |   |
|   +---------------------------------------------------------------------------------+   |
|             |                                                                           |
|             +---> [ System Managed Node Group: 1x t3.medium ]                           |
|             |       - CoreDNS, kube-system controllers, AWS VPC CNI                     |
|             |       - Cost: ~$0.0416 / hr                                               |
|             |                                                                           |
|             +---> [ GPU Managed Node Group: 1x g4dn.xlarge (1x NVIDIA T4 16GB) ]        |
|                     - EKS Accelerated AMI: AL2_x86_64_GPU (Pre-baked drivers)           |
|                     - Taint: nvidia.com/gpu=present:NoSchedule                          |
|                     - Spot: ~$0.158/hr | On-demand: ~$0.526/hr                          |
|                     - Autoscaling: min 0, max 1 (scales to $0/hr when idle)             |
|                     - Pod: vllm (Qwen2.5-7B-Instruct-AWQ via AWQ GEMM)                  |
+-----------------------------------------------------------------------------------------+
```

---

## Multi-Cloud Comparison (AWS vs GCP vs Azure)

| Metric | AWS (EKS) | GCP (GKE) | Azure (AKS) |
| :--- | :--- | :--- | :--- |
| **Control Plane Fee** | $0.10 / hr ($73/mo) | **$0.00** (1st zonal free) | **$0.00** (Free Tier) |
| **GPU Node Type** | `g4dn.xlarge` (T4) / `g5.xlarge` (A10G) | **`g2-standard-4` (L4 24GB)** | `Standard_NC4as_T4_v3` (T4) |
| **Driver Setup** | Pre-baked AMI (`AL2_x86_64_GPU`) | **Native Driver Auto-Injection** | NVIDIA GPU Operator (Helm) |
| **Spot Discount** | ~70% off | ~67% off | ~70% off |
| **Active Quota** | Ready (`us-east-1`) | **1.0 L4 GPU Approved** | Pending Support Review |

---

## Directory Layout

```
vllm-serving-aws/
├── terraform/
│   ├── versions.tf      # AWS (~> 5.0) and Kubernetes providers
│   ├── variables.tf     # Configurable variables (region, cluster name, node types)
│   ├── vpc.tf           # VPC, public/private subnets across 2 AZs, NAT Gateway
│   ├── iam.tf           # IAM roles for EKS cluster and managed node groups
│   ├── eks.tf           # EKS cluster, system node group, and GPU node group
│   └── outputs.tf       # Connection commands and outputs
├── k8s/
│   ├── vllm-deployment.yaml # vLLM Deployment & Service (T4 tuned with AWQ)
│   └── network-policy.yaml  # Zero-trust NetworkPolicy (blocks IMDS SSRF)
├── scripts/
│   └── verify.sh        # Smoke test, token verification, and nvidia-smi diagnostics
└── README.md
```

---

## Quickstart Deployment

### 1. Prerequisites
Verify active AWS credentials:
```bash
aws sts get-caller-identity
```

### 2. Provision Infrastructure via Terraform
```bash
cd terraform
terraform init
terraform apply -auto-approve
```
*Provisioning takes ~10-12 minutes for VPC, EKS control plane, and node groups.*

### 3. Connect kubectl
```bash
aws eks update-kubeconfig --region us-east-1 --name vllm-serving-aws
kubectl get nodes -L workload
```

### 4. Deploy Zero-Trust Security & vLLM Serving
```bash
kubectl apply -f ../k8s/network-policy.yaml
kubectl apply -f ../k8s/vllm-deployment.yaml
```

### 5. Verify Serving
Run the automated end-to-end verification script:
```bash
../scripts/verify.sh
```

---

## Cost Optimization (Spot Instances)

To run the GPU node as an AWS Spot instance (saving ~70%):
```bash
terraform apply -var="spot_gpu=true"
```

---

## Teardown
When finished testing, destroy all AWS resources to avoid ongoing charges:
```bash
terraform destroy -auto-approve
```
