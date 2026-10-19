# Setup - vLLM on AKS

## Prerequisites

**Local tools:**
- Azure CLI (logged in) — `az account show`
- Terraform ~> 1.15 — `terraform version`
- kubectl — `kubectl version --client`
- Helm ≥ 3, and `jq` (pretty-prints the smoke-test JSON)
- An HCP Terraform (Terraform Cloud) account — `terraform login`

**Azure subscription:**
- Permissions to create resource groups, AKS clusters, VMs, managed identities.
- **GPU vCPU quota** — the #1 blocker. `Standard NCASv3_T4 Family vCPUs` must be **≥ 4**
  (one `Standard_NC4as_T4_v3`). Approval is a human-reviewed request. Check with:
  ```bash
  az vm list-usage --location australiacentral \
    --query "[?contains(name.value,'NCASv3_T4')]" --output table
  ```
- **Resource providers must be registered by hand.** `providers.tf` sets
  `resource_provider_registrations = "none"` because azurerm's default bulk registration
  409-throttles a fresh subscription:
  ```bash
  for ns in Microsoft.ContainerService Microsoft.Compute Microsoft.Network Microsoft.OperationalInsights; do
    az provider register --namespace "$ns"
  done
  ```
- Region: `australiacentral` (where the T4 quota was approved). Confirm the SKU is actually
  deployable there — quota ≠ capacity:
  ```bash
  az vm list-skus --location australiacentral --size Standard_NC4as_T4 --output table
  ```
  > `Restrictions` must be empty. This SKU has **no availability zones** in this region, so
  > don't set `zones` on the node pool.
- Model `Qwen/Qwen2.5-7B-Instruct-AWQ` is ungated on Hugging Face — no token needed.

**HCP Terraform workspace:**
- Workspace `vllm-serving-aks` in your org, **Execution Mode = Local**.
- Local execution is required: azurerm authenticates off your local `az login` session, which
  a remote runner would not have.

---

## Setup steps

Each step has a verify check — don't move on until it passes.

1. **Confirm GPU quota is approved.**
   ```bash
   az vm list-usage --location australiacentral \
     --query "[?contains(name.value,'NCASv3_T4')]" --output table
   ```
   > Verify: `Limit` ≥ 4. `CurrentValue` should be `0` — the quota is subscription-wide, so a
   > non-zero value means another cluster already holds the GPU.

2. **Provision with Terraform** (resource group + AKS + system pool + GPU pool + GPU Operator,
   one apply):
   ```bash
   cd terraform && terraform init && terraform apply   # ~10–15 min
   ```
   > Verify: apply completes and prints the `configure_kubectl` output.

3. **Point kubectl at the cluster:**
   ```bash
   az aks get-credentials --resource-group rg-vllm-serving-aks --name vllm-serving-aks
   kubectl get nodes -o wide
   ```
   > Verify: 1 system + 1 GPU node, both `Ready`. The GPU node must show
   > `Ubuntu 22.04` and `containerd://1.7.x`. If `CONTAINER-RUNTIME` reads
   > `containerd://unknown` and the node is `NotReady`, the containerd drop-in version bug hit —
   > see [project-summary.md](project-summary.md) war story 3.

4. **Confirm the GPU Operator installed and the GPU is advertised:**
   ```bash
   kubectl -n gpu-operator get pods
   kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}{"\n"}'
   ```
   > Verify: pods `Running`/`Completed` (`nvidia-cuda-validator` shows `Completed`); a node
   > shows `nvidia.com/gpu: "1"`. **Until that number appears, vLLM will sit `Pending`.**
   > If it never appears, check the Operator DaemonSets' tolerations first.

5. **Deploy vLLM:**
   ```bash
   kubectl apply -f k8s/vllm-deployment.yaml
   kubectl get pods -l app=vllm -w
   ```
   > Verify: pod schedules on the GPU node (not `Pending`). First boot is slow — pulls a ~11 GB
   > image + downloads weights (~10 min); the startup probe allows for it.

6. **Prove tokens + read GPU memory:**
   ```bash
   bash scripts/verify.sh
   ```
   (waits for the pod, port-forwards, POSTs `/v1/completions`, runs `nvidia-smi` in the pod,
   greps the KV-cache log lines)
   > Verify: response contains generated `"text"`; `nvidia-smi` shows ~13.6 GB of 15 GB used;
   > logs report `Available KV cache memory: 7.32 GiB`.

7. **Tear down** — the GPU bills whether you're using it or not:
   ```bash
   terraform destroy
   ```
   > Verify: `az vm list-usage` shows `CurrentValue` back to `0`, and
   > `az group exists --name rg-vllm-serving-aks` returns `false`.

---

## Costs (australiacentral, on-demand)

| State | ~$/hr | What's running |
|---|---|---|
| **Active** (working) | **~$0.81** | everything up — the only time the GPU bills |
| **Destroyed** (`terraform destroy`) | **$0** | nothing |

Breakdown at "active": GPU `Standard_NC4as_T4_v3` **$0.684/hr** + system node
`Standard_D2s_v3` **$0.125/hr** + AKS control plane **$0** (`sku_tier = "Free"`).

Because the control plane is free, there is **no cheap middle state** worth keeping — unlike a
paid-control-plane cluster, destroying everything costs nothing but a ~15 min rebuild. Destroy
by default.

A focused 2h session ≈ **$1.60**. Leaving it up for 24h ≈ **$19**. A full month ≈ **$580** —
don't.

**Guardrails:** `terraform destroy` after every session · tag `project=vllm-serving-aks` · set an
**Azure Cost Management budget alert** as the backstop for the night you forget.

**Spot is 71% cheaper ($0.198/hr) but currently blocked** — `Total Regional Low-priority vCPUs`
is 3 and this VM needs 4. Spot and on-demand draw from separate quota pools.
