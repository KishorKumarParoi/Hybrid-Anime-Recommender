# Architecture Diagram — vLLM Serving on AKS

```mermaid
graph TB
    subgraph dev["Developer / Local Machine"]
        CLI["kubectl / curl"]
        TF["Terraform CLI\n(az login session supplies creds)"]
    end

    subgraph hcp["HCP Terraform"]
        STATE["Remote State\nShikha_Projects / vllm-serving-aks\nExecution Mode: LOCAL"]
    end

    subgraph azure["Azure — australiacentral"]

        subgraph rg["Resource Group: rg-vllm-serving-aks  (you declare)"]

            subgraph aks["AKS Cluster — vllm-serving-aks\nsku_tier: Free  ·  SystemAssigned identity"]

                subgraph system_np["System Node Pool  ·  Standard_D2s_v3\nUbuntu 24.04  ·  containerd 2.3  ·  count 1"]
                    CORENS["CoreDNS Pod"]
                    GPUCTL["GPU Operator\nController Pod"]
                    NFD["Node Feature\nDiscovery Master"]
                end

                subgraph gpu_np["GPU Node Pool  ·  Standard_NC4as_T4_v3  (NVIDIA T4 15 GiB)\nos_sku: Ubuntu2204  ·  containerd 1.7  ·  gpu_driver: None\nTaint: nvidia.com/gpu=present:NoSchedule\nLabel: workload=gpu"]

                    subgraph gpuop_ns["Namespace: gpu-operator\n(Helm chart v26.3.2  ·  driver.enabled=TRUE)"]
                        DRV["Driver DaemonSet\n(installs NVIDIA driver 580.126.20)"]
                        TOOLKIT["Container Toolkit DaemonSet\nCONTAINERD_CONFIG=/etc/containerd/config.toml"]
                        DP["Device Plugin\nDaemonSet"]
                        DCGM["DCGM Exporter\nDaemonSet"]
                        GFD["GPU Feature\nDiscovery DaemonSet"]
                    end

                    subgraph default_ns["Namespace: default"]
                        SVC["Service: vllm\n(ClusterIP :8000)"]
                        POD["vLLM Pod\nvllm/vllm-openai:v0.22.1\n──────────────────\nQwen2.5-7B-Instruct-AWQ\nquantization: awq  (NOT marlin — SM 7.5)\ndtype: float16  (no bf16 on Turing)\nenforce-eager: true\ngpu-memory-utilization: 0.90\nmax-model-len: 4096\nmax-num-seqs: 8\nenableServiceLinks: FALSE\nresources: 1× nvidia.com/gpu\n──────────────────\nstartupProbe /health  (10 min)\nreadinessProbe /health\nlivenessProbe /health"]
                    end

                    GPU["NVIDIA T4 GPU\n15360 MiB VRAM\n13605 MiB allocated\n7.32 GiB KV cache\n137,072 tokens"]
                end
            end
        end

        subgraph mc_rg["MC_rg-vllm-serving-aks_...  (AKS creates & owns — NOT in your state)"]
            VNET["Virtual Network\naks-vnet-38583473"]
            NSG["Network Security Group\naks-agentpool-...-nsg"]
            LB["Load Balancer\nkubernetes"]
            PIP["Public IP"]
            MI["Managed Identity\nvllm-serving-aks-agentpool"]
            VMSS["VM Scale Sets\n(the actual nodes)"]
        end

        HF[("HuggingFace Hub\nQwen2.5-7B-AWQ\n~5.6 GiB weights\nungated — no token")]
        NGC[("NVIDIA NGC\nhelm.ngc.nvidia.com\ngpu-operator chart")]
    end

    subgraph budget["Azure Cost Management"]
        ALERT["Budget alert\ntag: project=vllm-serving-aks"]
    end

    %% Provisioning flow
    TF -->|"terraform apply"| STATE
    TF -->|"1. aks.tf → resource group + cluster"| aks
    TF -->|"2. aks.tf → gpu node pool"| gpu_np
    TF -->|"3. gpu-operator.tf\n(helm_release depends_on gpu pool)"| gpuop_ns
    aks -.->|"AKS auto-creates"| mc_rg

    %% GPU Operator owns the full driver stack
    NGC -.->|"helm chart"| gpuop_ns
    DRV -->|"installs driver\ninto the node"| gpu_np
    TOOLKIT -->|"registers nvidia runtime\nin containerd"| gpu_np
    DP -->|"advertises nvidia.com/gpu: 1"| gpu_np
    DCGM -->|"VRAM / utilisation metrics"| GPU
    GFD -->|"node feature labels"| gpu_np

    %% Scheduling
    POD -->|"nodeSelector: workload=gpu\ntoleration: nvidia.com/gpu"| gpu_np
    POD -->|"limits: nvidia.com/gpu: 1"| GPU

    %% Model weights
    POD -->|"download weights\non first boot (~10 min)"| HF
    HF -.->|"~5.6 GiB\nQwen2.5-7B-AWQ"| GPU

    %% Service → Pod
    SVC --> POD

    %% Developer access
    CLI -->|"az aks get-credentials"| aks
    CLI -->|"kubectl port-forward\nsvc/vllm 8000:8000"| SVC
    CLI -->|"curl /v1/completions"| SVC

    %% Cost tagging
    rg -.->|"tag: project=vllm-serving-aks"| ALERT

    %% Styling
    classDef azure_svc fill:#0078D4,color:#fff,stroke:#005a9e
    classDef k8s fill:#326CE5,color:#fff,stroke:#1a56c4
    classDef nvidia fill:#76B900,color:#000,stroke:#4d7a00
    classDef cost fill:#e8f4e8,color:#333,stroke:#4CAF50
    classDef tf fill:#7B42BC,color:#fff,stroke:#5a2f8a
    classDef hidden fill:#f0f0f0,color:#666,stroke:#999,stroke-dasharray: 5 5

    class HF,NGC azure_svc
    class SVC,POD,CORENS,GPUCTL,NFD k8s
    class DRV,TOOLKIT,DP,DCGM,GFD,GPU nvidia
    class ALERT,budget cost
    class TF,STATE tf
    class VNET,NSG,LB,PIP,MI,VMSS,mc_rg hidden
```

---

## Component Summary

| Layer | Component | Detail |
|---|---|---|
| **Provisioning** | Terraform + HCP Terraform | Declares all infra as code; **Local execution** — azurerm auth comes from the local `az login` |
| **Network** | AKS-managed VNet | **Not declared** — AKS creates it in the `MC_*` resource group. No `vpc.tf` equivalent |
| **Orchestration** | AKS (`sku_tier = "Free"`) | Managed control plane at **$0**; system-assigned managed identity |
| **System Node** | `Standard_D2s_v3` — count 1 | Ubuntu 24.04 / containerd 2.3. Runs CoreDNS, GPU Operator controller, NFD master |
| **GPU Node** | `Standard_NC4as_T4_v3` (T4 15 GiB) — count 1 | **Pinned to Ubuntu 22.04 / containerd 1.7**; `gpu_driver = "None"`; tainted `nvidia.com/gpu=present:NoSchedule` |
| **GPU Operator** | Helm chart v26.3.2 | **`driver.enabled=true`** — owns driver + toolkit + device plugin + DCGM + GFD as one stack |
| **Serving Engine** | vLLM `v0.22.1` | OpenAI-compatible API on `:8000`; PagedAttention + continuous batching |
| **Model** | `Qwen2.5-7B-Instruct-AWQ` | 4-bit AWQ → ~5.6 GiB weights, **7.32 GiB KV cache** on the T4 |
| **Access** | ClusterIP Service + `kubectl port-forward` | No public load balancer; developer access only |

## Two things the diagram makes visible

**1. The GPU Operator owns the whole driver stack.** `gpu_driver = "None"` on the node pool plus
`driver.enabled=true` on the chart means Azure installs nothing and the Operator installs
everything — driver, toolkit, device plugin. That decouples driver lifecycle from the node image,
at the cost of a slower cold start.

**2. Most of the network is not yours.** The greyed `MC_*` box is created and owned by AKS. It
holds the VNet, NSG, load balancer, public IP, managed identity and the VM Scale Sets that are the
actual nodes — none of it in your Terraform state. Convenient, but invisible to your diff and your
cost reasoning. Never hand-edit it; AKS reconciles changes away.

## Cost States

| State | ~$/hr | Running |
|---|---|---|
| **Active** | ~$0.81 | Everything — GPU $0.684 + system $0.125 + control plane $0 |
| **Destroyed** | $0 | Nothing (`terraform destroy`) |

There is deliberately **no middle state**: the control plane is free, so a stopped cluster saves
nothing worth the complexity. Destroy by default.
