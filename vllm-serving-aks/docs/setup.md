# Setup - vLLM on AKS (Korea Central)

## Prerequisites

**Local tools:**
- Azure CLI (logged in) — `az account show`
- Terraform ≥ 1.15 — `terraform version`
- kubectl — `kubectl version --client`
- Helm ≥ 3, and `jq` (pretty-prints the smoke-test JSON)
- An HCP Terraform (Terraform Cloud) account — `terraform login`

**Azure subscription:**
- Subscription: **Azure for Students** (`a17774c6-e5cc-4461-b18c-df27f259f891`)
- Region: **`koreacentral`**
- Resource Providers:
  ```bash
  # Ensure core providers are registered (already done for this cluster)
  az provider register --namespace Microsoft.ContainerService --wait
  az provider register --namespace Microsoft.Compute --wait
  az provider register --namespace Microsoft.Network --wait
  ```
- **Modular Quota Handling (`enable_gpu_node_pool`)**:
  - **Zero-Quota Mode (`enable_gpu_node_pool = false`)**: Runs immediately without waiting for GPU quota. Deploys the free AKS control plane + the CPU system node pool (`Standard_D2s_v3`, 2 vCPUs) to run `k8s/inference-cpu-test.yaml`.
  - **GPU Mode (`enable_gpu_node_pool = true`)**: Requires 4 vCPUs of `Standard NCASv3_T4 Family`. Check status with:
    ```bash
    az vm list-usage --location koreacentral \
      --query "[?contains(name.value,'NCASv3_T4')]" --output table
    ```
- Model `Qwen/Qwen2.5-7B-Instruct-AWQ` is ungated on Hugging Face — no API token needed.

**HCP Terraform workspace:**
- Organization: **`kopa-samsu`**
- Workspace: **`vllm-serving-aks`**
- **Execution Mode = Local** (Required: azurerm authenticates off your local `az login` session on your Mac, while state is securely stored and locked in HCP Terraform Cloud).

---

## Setup Steps

### 1. Initialize and Provision Infrastructure with Terraform
```bash
cd terraform
terraform init
terraform apply
```
> When prompted, type `yes`. Terraform creates:
> - Resource Group: `rg-vllm-serving-aks`
> - AKS Cluster: `vllm-serving-aks` (`sku_tier = "Free"`, $0/mo control plane)
> - System Node Pool: 1x `Standard_D2s_v3` (2 vCPUs, 8GB RAM)

### 2. Connect `kubectl` to Your AKS Cluster
```bash
az aks get-credentials --resource-group rg-vllm-serving-aks --name vllm-serving-aks
kubectl get nodes -o wide
```
> Verify: The `system` node appears and shows status **`Ready`**.

---

## Testing & Workload Deployment

### Option A: Zero-Quota CPU / Mock Mode (Test Right Now)
If your student GPU quota request is still pending review, test the entire cluster infrastructure and OpenAI-compatible API without needing a GPU:

```bash
# 1. Deploy the CPU inference mock
kubectl apply -f ../k8s/inference-cpu-test.yaml

# 2. Run the automated CPU verification smoke test
../scripts/verify-cpu.sh
```
> Verify: The script connects, sends a prompt to `/v1/completions`, and outputs valid generated tokens!

---

### Option B: Full GPU Serving Mode (Post-Quota Approval)
Once Microsoft Support approves your 4 vCPU T4 quota (or you upgrade to Pay-As-You-Go):

1. **Attach the GPU node pool and NVIDIA Operator**:
   ```bash
   terraform apply -var="enable_gpu_node_pool=true"
   ```
2. **Verify GPU operator and node readiness**:
   ```bash
   kubectl -n gpu-operator get pods
   kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}{"\n"}'
   ```
   > Verify: Node displays `nvidia.com/gpu: "1"`.
3. **Deploy vLLM**:
   ```bash
   kubectl apply -f ../k8s/vllm-deployment.yaml
   kubectl get pods -l app=vllm -w
   ```
4. **Run live GPU token verification & nvidia-smi**:
   ```bash
   ../scripts/verify.sh
   ```

---

## Operational Cost & Teardown

| State | ~$/hr | What's running |
|:---|:---|:---|
| **CPU Testing Mode** | **~$0.096** | Control plane ($0) + `Standard_D2s_v3` system node |
| **Active GPU Serving** | **~$0.780** | Control plane ($0) + System node + `Standard_NC4as_T4_v3` GPU node |
| **Destroyed** (`terraform destroy`) | **$0.00** | Nothing |

### Cost Reduction Tools
- **Scale GPU to Zero**: When you are not actively benchmarking, scale the GPU node pool to 0:
  ```bash
  ../scripts/gpu-nodes-scaling.sh down
  ```
  *(Scale back up with `../scripts/gpu-nodes-scaling.sh up` when ready).*
- **Complete Teardown**:
  ```bash
  terraform destroy -auto-approve
  ```
  > Destroys all Azure resources and halts all billing immediately.
