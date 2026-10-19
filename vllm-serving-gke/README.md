# vLLM Serving on Google Kubernetes Engine (GKE)

Production-grade Infrastructure-as-Code (Terraform) and Kubernetes manifests to serve large language models with **vLLM** on **Google Kubernetes Engine (GKE)** using NVIDIA GPUs (L4 24GB or T4 16GB).

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------------+
|                                    GKE ARCHITECTURE                                     |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   Google Cloud Project: project-53d8ce01-b0e0-4f8b-94c                                  |
|   Region: us-central1 | Zone: us-central1-a                                             |
|                                                                                         |
|   +---------------------------------------------------------------------------------+   |
|   | GKE Zonal Control Plane (Free Tier: $0/month cluster management fee)            |   |
|   +---------------------------------------------------------------------------------+   |
|             |                                                                           |
|             +---> [ System Node Pool: 1x e2-standard-2 ]                                |
|             |       - CoreDNS, kube-system controllers, Ingress                         |
|             |       - Cost: ~$0.067 / hr (~$48/mo)                                      |
|             |                                                                           |
|             +---> [ GPU Node Pool: 1x g2-standard-4 (1x NVIDIA L4 24GB) ]               |
|                     - Native GKE driver injection (gpu_driver_version = "DEFAULT")      |
|                     - Taint: nvidia.com/gpu=present:NoSchedule                          |
|                     - On-demand: ~$0.70/hr | Spot: ~$0.23/hr                            |
|                     - Pod: vllm (Qwen2.5-7B-Instruct-AWQ via Marlin kernel)             |
+-----------------------------------------------------------------------------------------+
```

---

## Why GKE + NVIDIA L4 for vLLM?

| Feature | Azure AKS (T4) | Google GKE (L4) | Benefit on GKE |
| :--- | :--- | :--- | :--- |
| **GPU Model** | NVIDIA T4 (Turing, SM 7.5) | NVIDIA L4 (Ada Lovelace, SM 8.9) | **Newer architecture** (FP8, BF16 native) |
| **VRAM** | 16 GB | 24 GB (+50%) | **Larger KV Cache** & longer context |
| **Quantization** | AWQ (Generic GEMM) | AWQ Marlin Kernel | **2.5x higher token generation speed** |
| **Driver Setup** | Custom NVIDIA Helm Operator | Native GKE Driver Injection | **Zero containerd version clashes** |
| **Control Plane** | $0 (Free Tier) | $0 (1st Zonal Cluster Free) | **$0/month cluster overhead** |
| **Quota Approval** | Gated on Student accounts | **1.0 L4 GPU pre-approved** | **Ready to deploy immediately** |

---

## Directory Layout

```
vllm-serving-gke/
├── terraform/
│   ├── versions.tf      # Provider constraints (Google ~> 6.0, Kubernetes)
│   ├── variables.tf     # Configurable variables (project, zone, machine types)
│   ├── vpc.tf           # VPC network with secondary ranges for pods & services
│   ├── gke.tf           # GKE cluster, system node pool, and GPU node pool
│   └── outputs.tf       # Connection commands and endpoints
├── k8s/
│   └── vllm-deployment.yaml # vLLM Deployment & Service (L4 tuned: Marlin + BF16)
├── scripts/
│   └── verify.sh        # Automated smoke test, token verification, and nvidia-smi
└── README.md
```

---

## Quickstart Deployment

### 1. Prerequisites
Ensure you are authenticated to Google Cloud:
```bash
gcloud auth list
gcloud config set project project-53d8ce01-b0e0-4f8b-94c
```

### 2. Provision Infrastructure via Terraform
```bash
cd terraform
terraform init
terraform apply -auto-approve
```
*Provisioning takes ~4-6 minutes for VPC, GKE control plane, and node pools.*

### 3. Connect kubectl
```bash
gcloud container clusters get-credentials vllm-serving-gke --zone us-central1-a --project project-53d8ce01-b0e0-4f8b-94c
kubectl get nodes -L workload
```

### 4. Deploy vLLM Serving
```bash
kubectl apply -f ../k8s/vllm-deployment.yaml
```

### 5. Verify Serving
Run the automated end-to-end verification script:
```bash
../scripts/verify.sh
```

---

## Cost Optimization (Spot VMs)

To save up to **70%** on compute costs during development or benchmarks, enable Spot VMs in `variables.tf` or via CLI:

```bash
terraform apply -var="spot=true"
```

---

## Teardown
When you are done testing, destroy all resources to stop billing:
```bash
terraform destroy -auto-approve
```
