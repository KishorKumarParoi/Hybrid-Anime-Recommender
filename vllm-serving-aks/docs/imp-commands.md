
# Important Commands — `vllm-serving-aks`

Every command run for this project, in order, with what it does and why.
Copy/paste-able. Read top-to-bottom to reproduce the build from scratch.

---

## 0. One-time setup

```bash
chmod +x scripts/*.sh
```
Makes `verify.sh` and `gpu-nodes-scaling.sh` executable.

---

## 1. Pre-flight — before spending anything

### 1.1 Confirm GPU quota is available

```bash
az vm list-usage --location australiacentral \
  --query "[?contains(name.value,'NCASv3_T4')]" --output table
```
Shows `CurrentValue` vs `Limit` for the T4 GPU family. **Result: `0 / 4`** — 4 vCPUs free =
exactly one `Standard_NC4as_T4_v3`. `CurrentValue: 0` also proves no other project
(e.g. `llm-argo-canary`) is holding the GPU — the 4-vCPU quota is subscription-wide, so
only one GPU cluster can exist at a time.

### 1.2 Dump ALL quota families (find what else is constrained)

```bash
az vm list-usage --location australiacentral --output json \
  | jq -r '.[] | select(.limit > 0) | "\(.currentValue)/\(.limit)\t\(.localName)"' \
  | sort -t$'\t' -k2
```
The full picture rather than one family. The four lines that matter here:

| Quota | Value | Consequence |
|---|---|---|
| `Standard NCASv3_T4 Family vCPUs` | **0/4** | Exactly one GPU node. No canary/blue-green (needs 2). |
| `Total Regional Low-priority vCPUs` | **0/3** | **Spot GPU is impossible** — the VM needs 4 vCPUs, quota is 3. |
| `Total Regional vCPUs` | 0/14 | GPU (4) + system (2) = 6. Fits. |
| `Standard DSv3 Family vCPUs` | 0/10 | `Standard_D2s_v3` system pool fits. |

### 1.3 Get real pricing (never estimate — query the API)

```bash
curl -s "https://prices.azure.com/api/retail/prices?\$filter=armRegionName%20eq%20'australiacentral'%20and%20armSkuName%20eq%20'Standard_NC4as_T4_v3'%20and%20priceType%20eq%20'Consumption'" \
  | jq -r '.Items[] | "\(.retailPrice)\t\(.productName)\t\(.meterName)"' | sort -n
```
Azure's public retail price API — no auth needed. **Filter out `Windows` product names**
(we run Ubuntu) and `Spot`/`Low Priority` meters (no quota for them here).

Result for `Standard_NC4as_T4_v3` in `australiacentral`:

| Price/hr | Product | Usable? |
|---|---|---|
| $0.137 | Low Priority (Linux) | ❌ only 3 low-pri vCPUs, need 4 |
| $0.19836 | Spot (Linux) | ❌ same quota block |
| $0.684 | **On-demand (Linux)** | ✅ **what we pay** |
| $0.868 | On-demand (Windows) | ❌ n/a |

Same query for the system node (`Standard_D2s_v3` → **$0.125/hr** Linux on-demand;
`Standard_B2s` → $0.0528/hr as a cheaper alternative).

### 1.4 Register Azure resource providers

```bash
for ns in Microsoft.ContainerService Microsoft.Compute Microsoft.Network Microsoft.OperationalInsights; do
  az provider register --namespace "$ns"
done

for ns in Microsoft.ContainerService Microsoft.Compute Microsoft.Network Microsoft.OperationalInsights; do
  echo -e "$ns\t$(az provider show --namespace $ns --query registrationState -o tsv)"
done
```
`providers.tf` sets `resource_provider_registrations = "none"` because a fresh subscription
409-throttles when azurerm tries to bulk-register dozens of RPs. So we register the four
AKS actually needs, by hand. **All four returned `Registered`.**

### 1.5 Confirm the GPU SKU is actually deployable

```bash
az vm list-skus --location australiacentral --size Standard_NC4as_T4 --output json \
  | jq -r '.[] | "\(.name)\tzones=\(.locationInfo[0].zones // [] | join(",") | if . == "" then "none" else . end)\trestrictions=\(if (.restrictions|length)==0 then "NONE" else ([.restrictions[].reasonCode]|join(",")) end)"'
```
Quota ≠ capacity. This checks Azure will *actually* let you deploy the SKU in that region.
**Result: `restrictions=NONE`, `zones=none`** — deployable, but no availability zones for
this SKU here, so don't set `zones` on the node pool.

---

## 2. Deploy

### 2.1 Terraform

```bash
cd terraform
terraform init     # downloads azurerm/kubernetes/helm providers, connects HCP backend
terraform plan     # expect: resource group + AKS + gpu node pool + helm_release
terraform apply    # ~10-15 min (AKS control plane, then GPU node, then GPU Operator)
```
Requires an HCP Terraform workspace named `vllm-serving-aks` in org `Shikha_Projects`
with **Execution Mode = Local** — azurerm authenticates off the local `az login` session,
which a remote runner would not have.

### 2.2 Point kubectl at the cluster

```bash
az aks get-credentials --resource-group rg-vllm-serving-aks --name vllm-serving-aks
```
Writes cluster creds into `~/.kube/config` and switches context. (Also emitted as the
`configure_kubectl` Terraform output.)

### 2.3 Verify the cluster and GPU stack
echo "=== nodes ==="; kubectl get nodes -o wide
echo "=== gpu-operator pods ==="; kubectl get pods -n gpu-operator

```bash
kubectl get nodes -o wide                    # expect 2 Ready: system + gpu
kubectl describe node -l workload=gpu | grep nvidia.com/gpu   # expect: 1
kubectl get node -l workload=gpu -o jsonpath='{.items[0].status.allocatable}' | jq '{cpu, memory, "nvidia.com/gpu"}' 
                                             #Is gpu node allocatable

kubectl get deploy -o wide
kubectl logs deploy/vllm #Check deploy logs post deploy


kubectl get pods -n gpu-operator              # all Running/Completed
kubectl get pods -l app=vllm -o wide         # pod status 
kubectl get pods -o wide -A  # All pods, in all namespaces (-A)


```
The last one is the real checkpoint: it proves the GPU Operator installed the driver and
device plugin, and that Kubernetes now sees `nvidia.com/gpu: 1` as a schedulable resource.
Until that number appears, the vLLM pod will sit `Pending`.

### 2.4 Deploy vLLM

```bash
kubectl apply -f ../k8s/vllm-deployment.yaml
kubectl get pods -l app=vllm -w      # Ctrl-C once Running
```
First boot takes ~10 min: pulls the ~11GB image, then downloads the model weights.

### 2.5 Verify serving

```bash
../scripts/verify.sh
```
Waits for Ready, port-forwards 8000, POSTs `/v1/completions`, and prints `nvidia-smi` plus
the KV-cache lines from the startup logs. **PASS = P1 works on AKS.**

curl localhost:8000/v1/completions -H "Content-Type: application/json" -d '{"model":"Qwen/Qwen2.5-7B-Instruct-AWQ","prompt":"Hello, my name is","max_tokens":20}'

---


## 3. Teardown — run at the END of EVERY session

*Scale-down GPU node pool*

```bash
./gpu-nodes-scaling.sh in  
```

#Check status

```bash
az aks nodepool show --resource-group rg-vllm-serving-aks --cluster-name vllm-serving-aks --name gpu --query {name:name, count:count, state:provisioningState, vm:vmSize, os:osSku} -o table
```

*Complete Cleanup*

```bash
cd terraform && terraform destroy

```
To keep Terraform state in sync instead, use `terraform destroy` from `terraform/`.

The resource group is a Terraform resource (`azurerm_resource_group.this` in `aks.tf`), so one
destroy removes the AKS cluster, both node pools, disks, the managed identity, and the `MC_*`
group AKS creates for itself — and leaves state consistent. `az group delete` would delete the
same things faster but strand the state file.

Confirm the GPU quota was released:
```bash
az vm list-usage --location australiacentral \
  --query "[?contains(name.value,'NCASv3_T4')]" --output table   # CurrentValue back to 0
az group exists --name rg-vllm-serving-aks                        # false = fully deleted
```

---