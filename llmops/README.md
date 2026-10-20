# Continuous Fine-Tuning & Dynamic Multi-LoRA Serving

Production-grade, end-to-end LLMOps pipeline designed for the **Hybrid Anime Recommendation Platform**. Enables automated continuous dataset curation, QLoRA fine-tuning, regression gating, and dynamic multi-adapter serving on a single GPU instance across **Azure (AKS)**, **Google Cloud (GKE)**, and **AWS (EKS)**.

---

## 1. Executive Summary & Problem Formulation

### The Problem: Multi-Model Sprawl & GPU Inefficiency
Deploying specialized LLMs for diverse domain tasks (e.g., in-depth sakuga anime critique, personalized otaku conversational styling, structured metadata extraction) traditionally requires running independent model replicas. 

Hosting three separate 7B parameter models on dedicated GPU nodes (e.g., Azure NC4as_T4_v3 or AWS g4dn.xlarge at ~$380–$550/month each) leads to:
* **Cost Inefficiency**: $1,200–$1,650/month in idle compute.
* **Cold-Start Delays**: 45–90 seconds per model switch in serverless setups.
* **Operational Fragmentation**: Managing separate deployment manifests, ingress endpoints, and health monitoring.

### The Solution: Dynamic Multi-LoRA Serving on vLLM
By decoupling the foundational world knowledge in a frozen 4-bit base model (`Qwen2.5-7B-Instruct-AWQ`) from task-specific low-rank decomposition matrices ($W = W_0 + \frac{\alpha}{r} B \cdot A$), vLLM dynamically injects adapter weights during the GEMM forward pass on-the-fly.
* **Single GPU Footprint**: Serves the base model plus multiple adapters (`anime-critic`, `anime-stylist`) on **one 16GB or 24GB GPU**.
* **Zero Cold-Start Latency**: Adapters are dynamically resolved in-flight per request header in sub-millisecond overhead.
* **75–87.5% Infrastructure Savings**: Consolidates multiple workloads into a single Kubernetes deployment.

---

## 2. Architecture & Data Flow

+-----------------------------------------------------------------------------------+
|                           CONTINUOUS LLMOPS FLYWHEEL                              |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. INTERACTION LOGS & TELEMETRY                                                 |
|     [ User Interactions ] ---> [ Raw Interaction Logs (data/raw/) ]               |
|                                         |                                         |
|                                         v                                         |
|  2. DATA CURATION & SANITIZATION ENGINE (llmops/curation/)                        |
|     +-------------------------------------------------------------------+         |
|     | - PII Redaction: Regex scrubbing for emails, phones, API keys, IPs|         |
|     | - Quality Filtering: Rejection of low-confidence/degenerate pairs |         |
|     | - ChatML Standardizer: Formats conversations for instruction SFT  |         |
|     | - 15% General Replay Buffer: Injects core logic & reasoning pairs |         |
|     |   (Mitigates Catastrophic Forgetting of foundational reasoning)   |         |
|     +-------------------------------------------------------------------+         |
|                                         |                                         |
|                                         v                                         |
|  3. PARAMETER-EFFICIENT QLORA FINE-TUNING (llmops/training/)                      |
|     +-------------------------------------------------------------------+         |
|     | - Base Model: Frozen 4-bit NF4 / AWQ Foundation                   |         |
|     | - Target Modules: q_proj, k_proj, v_proj, o_proj, gate, up, down  |         |
|     | - Hyperparams: Rank r=16, Alpha=32, Dropout=0.05, AdamW-torch     |         |
|     | - Output: Standardized PEFT adapter checkpoint (~50MB - 120MB)    |         |
|     +-------------------------------------------------------------------+         |
|                                         |                                         |
|                                         v                                         |
|  4. AUTOMATED CI/CD QUALITY GATING & EVALUATION (llmops/evals/)                   |
|     +-------------------------------------------------------------------+         |
|     | Evaluates 4 Weighted Dimensions (Pass Threshold >= 0.85):         |         |
|     | 1. Domain Nuance & Vocabulary (Sakuga, Studio, Pacing) [35%]      |         |
|     | 2. JSON Schema Compliance & Structural Validity        [25%]      |         |
|     | 3. Reasoning Depth & Thematic Synthesis               [25%]      |         |
|     | 4. General Knowledge Retention (No Catastrophic Loss) [15%]      |         |
|     | Decision Gate: APPROVED_FOR_DEPLOYMENT vs REJECTED                |         |
|     +-------------------------------------------------------------------+         |
|                                         |                                         |
|                                         v (Approved Artifacts)                    |
|  5. DYNAMIC MULTI-LORA SERVING INFRASTRUCTURE (Kubernetes / vLLM)                 |
|     +-------------------------------------------------------------------+         |
|     |  vLLM OpenAI Server (--enable-lora --max-loras=4 --max-lora-rank=32)|        |
|     |                                                                   |         |
|     |        +-----------------------------------------------+          |         |
|     |        | Frozen Base Model: Qwen2.5-7B-AWQ (5.6 GB)    |          |         |
|     |        +-----------------------------------------------+          |         |
|     |             |                           |                         |         |
|     |             v                           v                         |         |
|     |    [ Adapter: anime-critic ]   [ Adapter: anime-stylist ]          |         |
|     |    (Sakuga & Narrative)        (Otaku Persona & Prose)            |         |
|     +-------------------------------------------------------------------+         |
|                                         ^                                         |
|                                         | (Dynamic In-Flight Routing)             |
|  6. MULTI-LORA CLIENT ROUTER (llmops/client/multilora_client.py)                 |
|     - Request A: model="anime-critic"  --> Critic Adapter Response                |
|     - Request B: model="anime-stylist" --> Stylist Persona Response               |
|     - Request C: model=None            --> Base Foundation Response               |
+-----------------------------------------------------------------------------------+

---

## 3. GPU Memory Budget & Latency Economics

### Memory Allocation on Single GPU

| Component | Azure AKS (T4 16GB) | GCP GKE / AWS (L4 24GB) | Notes |
| :--- | :--- | :--- | :--- |
| **GPU Architecture** | Turing (SM 7.5) | Ada Lovelace (SM 8.9) | T4 uses AWQ GEMM; L4 uses AWQ Marlin |
| **Model Precision** | FP16 (`float16`) | BF16 (`bfloat16`) | Turing lacks native bfloat16 |
| **Base Model Weights** | ~5.6 GB (4-bit AWQ) | ~5.6 GB (4-bit AWQ) | Frozen foundational weights |
| **vLLM Engine Overhead**| ~1.2 GB | ~1.5 GB | PyTorch CUDA context, kernel workspaces |
| **LoRA Adapters (x2)** | ~0.15 GB (~75MB each)| ~0.15 GB (~75MB each)| Rank r=16, alpha=32 matrices |
| **Paged KV Cache Pool** | **~8.8 GB** | **~16.7 GB** | Dynamic PageAttention block allocation |
| **Max Context Window** | 4,096 tokens | 8,192 tokens | Halved on 16GB to guarantee KV headroom |
| **Max Concurrency** | 8 concurrent sequences | 16 concurrent sequences | Sustained continuous batching |

### Cost Comparison (Monthly Production Estimates)

| Deployment Strategy | GPU Instances | Monthly Cost | Cold-Start Latency | Failure Domain |
| :--- | :--- | :--- | :--- | :--- |
| **Independent Replicas** | 3x T4 Instances | **~$1,140/mo** | 0s (always hot) | 3 distinct endpoints to monitor |
| **Serverless On-Demand** | 1x Shared GPU | **~$450/mo** | 45–90s per swap | High tail-latency spikes |
| **Dynamic Multi-LoRA** | **1x T4 or L4 GPU** | **~$380/mo** | **< 1ms dynamic swap**| **Single resilient deployment** |

---

## 4. Multi-Cloud Kubernetes Manifest Parity

Dynamic Multi-LoRA serving is uniformly packaged across three major cloud providers:

### 1. Azure Kubernetes Service (AKS)
* **Manifest**: `vllm-serving-aks/k8s/vllm-multilora-deployment.yaml`
* **Node Pool**: `Standard_NC4as_T4_v3` (NVIDIA T4 16GB VRAM, Turing SM 7.5).
* **vLLM Kernels**: `--quantization=awq`, `--dtype=float16`, `--enforce-eager`.
* **Adapter Staging**: Mariner base initContainer synchronizes adapter weights into shared `/data/adapters`.

### 2. Google Kubernetes Engine (GKE)
* **Manifest**: `vllm-serving-gke/k8s/vllm-multilora-deployment.yaml`
* **Node Pool**: `g2-standard-4` (NVIDIA L4 24GB VRAM, Ada Lovelace SM 8.9).
* **vLLM Kernels**: `--quantization=awq_marlin`, `--dtype=bfloat16`, `--gpu-memory-utilization=0.90`.
* **Adapter Staging**: Cloud SDK initContainer mounts GCS-staged adapter checkpoints.

### 3. Amazon Elastic Kubernetes Service (EKS)
* **Manifest**: `vllm-serving-aws/k8s/vllm-multilora-deployment.yaml`
* **Node Pool**: `g4dn.xlarge` (T4) or `g5.xlarge` (A10G).
* **vLLM Kernels**: `--quantization=awq`, `--dtype=float16`, `--enforce-eager`.
* **Adapter Staging**: AWS CLI initContainer synchronizes adapter checkpoints from S3.

---

## 5. Walkthrough & Quickstart

### Step 1: Ingest & Curate Training Data
Scrub PII, discard low-quality samples, format into ChatML, and inject the 15% general reasoning replay buffer:
```bash
uv run python -m llmops.curation.curate_dataset \
    --input data/raw/sample_interactions.jsonl \
    --output-dir data/curated \
    --min-quality 0.70 \
    --replay-ratio 0.15
```

### Step 2: Train Domain LoRA Adapters (or Run Simulation)
Train specialized adapters (supports dry-run mode for CI/CD runners without GPUs):
```bash
# Stylist persona adapter
uv run python -m llmops.training.train_lora \
    --output-dir artifacts/adapters/anime-stylist-lora \
    --dry-run

# Analytical critic adapter
uv run python -m llmops.training.train_lora \
    --output-dir artifacts/adapters/anime-critic-lora \
    --dry-run
```

### Step 3: Run Automated CI/CD Evaluation Gate
Evaluate candidate adapters against the four-dimensional quality rubric before deployment:
```bash
uv run python -m llmops.evals.eval_adapter \
    --adapter-path artifacts/adapters/anime-stylist-lora \
    --output-report artifacts/eval_report.json \
    --threshold 0.85
```

### Step 4: Test Dynamic Multi-LoRA Client Routing
Test dynamic in-flight model routing against a running vLLM cluster (or in mock simulation mode):
```bash
# Dynamic benchmarking across base model and both adapters on 1 GPU
uv run python -m llmops.client.multilora_client --compare --mock

# Query specific adapter directly
uv run python -m llmops.client.multilora_client \
    --adapter anime-critic \
    --prompt "Evaluate the animation choreography in Mob Psycho 100 Season 2 Episode 5" \
    --mock
```

### Step 5: Run Automated Integration Tests
Verify the entire pipeline end-to-end:
```bash
uv run pytest tests/test_llmops_pipeline.py -v
```

---

## 6. Senior Staff / Principal Engineer Interview Defense

When asked about LLM fine-tuning and inference architecture in technical interviews:

### Q1: "Why use Dynamic Multi-LoRA instead of full model fine-tuning or separate endpoints?"
> *"Full fine-tuning updates all 7 billion parameters, requiring multi-GPU distributed clusters (DeepSpeed ZeRO-3 / FSDP) and resulting in high operational sprawl. If we have 4 distinct domain personas, full fine-tuning requires 4 separate model weights (each 14GB in FP16), requiring 4 separate GPU deployments totaling ~$1,500/month.*
>
> *With Dynamic Multi-LoRA on vLLM, we freeze the foundational model in a compact 4-bit AWQ representation (~5.6 GB). Adapters only train low-rank decomposition matrices ($r=16$) occupying ~75MB each. vLLM loads the base model once into GPU VRAM and dynamically applies adapter weights during the GEMM computation based on the request's model header. We serve multiple specialized capabilities on a single $380/mo T4/L4 GPU with zero cold-start delay, reducing infrastructure spend by over 75%."*

### Q2: "How do you prevent Catastrophic Forgetting during continuous domain fine-tuning?"
> *"Catastrophic forgetting occurs when gradient updates on a narrow domain dataset override the model's general reasoning, math, and instruction-following abilities. In our data curation flywheel (`llmops/curation/curate_dataset.py`), we implement an experience replay buffer: 15% of every training split consists of general logical deductions, deductive reasoning, and foundational QA samples. Furthermore, our CI/CD quality gate (`llmops/evals/eval_adapter.py`) explicitly includes a `general_retention` evaluation dimension alongside domain nuance, blocking any adapter from production promotion if general reasoning degrades."*

### Q3: "What are the kernel-level differences between serving on Azure T4 vs GCP L4 GPUs?"
> *"Hardware architecture dictates the optimal GEMM kernels and memory layout:*
> 1. *Azure NC4as_T4_v3 features an NVIDIA T4 (Turing, SM 7.5, 16GB VRAM). Turing lacks native bfloat16 and cannot run Marlin kernels, which require compute capability SM 8.0+. On T4, vLLM must be configured with `--quantization=awq` (classic GEMM), `--dtype=float16`, `--enforce-eager` (skipping CUDA graph capture to conserve KV cache memory), with context length capped at 4096 tokens.*
> 2. *GCP GKE features an NVIDIA L4 (Ada Lovelace, SM 8.9, 24GB VRAM). Ada supports native bfloat16 and high-throughput Marlin quantized GEMM kernels (`--quantization=awq_marlin`), providing 2.5x higher token generation throughput. The 24GB memory footprint allows 8192 context length and 16 concurrent sequences while dedicating 16.7 GB strictly to the PageAttention KV cache pool."*
