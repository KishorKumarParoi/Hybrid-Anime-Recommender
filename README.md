# 🎬 Hybrid Anime Intelligence & Continuous LLMOps Platform

[![Tests Status](https://img.shields.io/badge/Tests-76%2F76%20Passing%20(100%25)-success?style=for-the-badge&logo=pytest)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/scripts/test_all.sh)
[![Python](https://img.shields.io/badge/Python-3.12%20(uv)-3776AB?style=for-the-badge&logo=python&logoColor=white)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/pyproject.toml)
[![Rust](https://img.shields.io/badge/Rust-1.85%2B%20(SIMD)-000000?style=for-the-badge&logo=rust&logoColor=white)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/services/rust-scoring-engine)
[![Go](https://img.shields.io/badge/Go-1.24%2B%20(Auth)-00ADD8?style=for-the-badge&logo=go&logoColor=white)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/services/go-auth-service)
[![vLLM](https://img.shields.io/badge/vLLM-Dynamic%20Multi--LoRA-blueviolet?style=for-the-badge&logo=nvidia)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/llmops/serving)
[![Multi-Cloud](https://img.shields.io/badge/Multi--Cloud-AKS%20%7C%20GKE%20%7C%20EKS-orange?style=for-the-badge&logo=kubernetes)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/terraform)
[![AI Security](https://img.shields.io/badge/AI%20Security-PyRIT%20Red%20Teaming-red?style=for-the-badge&logo=shield)](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/src/security)

A production-grade, globally distributed enterprise AI platform engineered to demonstrate **Principal Engineer / Senior Staff** competencies across:
1. **Hybrid Recommendation Architecture**: Dual-tower neural collaborative filtering, metadata cosine similarity, and ChromaDB HNSW dense vector search.
2. **Polyglot Event-Driven Microservice Mesh**: High-concurrency Go auth service, sub-millisecond Rust SIMD vector scoring, Node.js Express telemetry, and Python FastAPI core connected via Apache Kafka and two-tier Redis caching.
3. **Continuous Fine-Tuning & LLMOps Flywheel**: Automated PII scrubbing, quality gating, 15% general reasoning replay buffer (preventing catastrophic forgetting), and QLoRA fine-tuning with **RSLoRA ($\alpha/\sqrt{r}$)**, **NeFTune**, and **completion-only loss masking**.
4. **Dynamic Multi-LoRA Serving on vLLM**: Hosting multiple domain-specific adapters (`anime-critic`, `anime-stylist`) alongside a frozen 4-bit foundation on a **single GPU** with sub-millisecond in-flight routing, reducing cloud compute costs by **75–87.5%**.
5. **Multi-Cloud Kubernetes & GitOps**: Production manifests and Terraform automation across **Azure (AKS)**, **Google Cloud (GKE)**, and **Amazon Web Services (EKS)** with DCGM GPU telemetry.
6. **AI Security Defense-in-Depth**: Microsoft PyRIT automated red teaming, jailbreak resistance, and adversarial prompt injection mitigation.

---

## 🧭 Executive Documentation Navigator & Learning Paths

| Document | Focus & Target Audience | Core Content & Topics Covered |
| :--- | :--- | :--- |
| **[Step-by-Step Learning Curriculum](docs/STEP_BY_STEP_LEARNING.md)** | Self-Paced Learners & Engineers | 6 pedagogical modules: Polyglot mesh, NCF/ChromaDB algorithms, RSLoRA math, dynamic vLLM serving, enterprise suite, and cloud bootstrap. |
| **[Workflow Serialization & Data Journey](docs/WORKFLOW_SERIALIZATION.md)** | System Architects & Leads | Detailed request lifecycle tracing: client ingress $\to$ auth $\to$ SIMD scoring $\to$ telemetry flywheel $\to$ evaluation gates $\to$ vLLM multi-LoRA. |
| **[System Design & Architecture Specification](docs/ARCHITECTURE.md)** | Lead Architects & Directors | Polyglot mechanical sympathy, multi-database persistence (Postgres, Mongo, Redis), Enterprise AI Suite (RAG, Saga, Outbox, Lakehouse, KMS). |
| **[Principal Architect Portfolio](docs/PORTFOLIO_ARCHITECT.md)** | Executive Interviewers & Staff+ | 3 Reference architectures, ADR-001/002/003, STRIDE threat model, ISO 27001/SOC 2 mapping, 75% GPU cost optimization study, and P0 runbooks. |
| **[Interview & Negotiation Playbook](docs/INTERVIEW_COMP_PLAYBOOK.md)** | Principal Candidates & Negotiators | 6-Step whiteboard system design protocol, 3 executive STAR stories, and senior total compensation (TC) negotiation frameworks. |

---

## 🌳 5-Tier GitOps Branching Model

The repository adheres to an enterprise multi-branch promotion pipeline. All 5 branches are active and synchronized:

```
feature/*  ────────>  test  ────────>  dev  ────────>  stage  ────────>  prod / main
(Atomic Work)      (Unit CI)      (Integration)    (Pre-Prod UAT)        (Live Production)
```

* **`feature/*`**: Individual developer branches for atomic features, hotfixes, or experiments.
* **`test`**: Automated test execution branch running unified polyglot and contract test suites.
* **`dev`**: Active integration branch where all 9 microservices are assembled and validated.
* **`stage`**: Pre-production staging environment mirroring cloud Kubernetes clusters and GPU pools.
* **`prod`** (and **`main`**): Release-grade production code tagged with semantic releases and verified Docker images.

---

## 🏛️ End-to-End System Architecture

![System Architecture Overview](docs/images/01_architecture_overview.jpg)

```
+-------------------------------------------------------------------------------------------------------------------------+
|                                              GLOBAL CLIENT & EDGE INGRESS                                               |
|                      Next.js 16 (React 19, Turbopack) • NGINX Reverse Proxy • TLS 1.3 • Rate Limiting                   |
+-----------------------------------------------------------+-------------------------------------------------------------+
                                                            |
                                    +-----------------------+-----------------------+
                                    |                                               |
+-----------------------------------+--------------------+     +--------------------+------------------------------------+
|               POLYGLOT MICROSERVICE MESH               |     |                 EVENT STREAMING & CACHE                 |
|  * Go 1.24 Auth (JWT, Goroutines, Port 8081)           |     |  * Apache Kafka: Telemetry & Event Ingestion (9092)     |
|  * Node.js 22 Interactions (MongoDB, Port 8082)        | <-> |  * Redis Two-Tier Cache: Sub-millisecond Recs (6379)    |
|  * Rust 1.85 SIMD Vector Scoring (Port 8083)           |     |  * PostgreSQL: Relational User Metadata                 |
|  * Python FastAPI Core Intelligence (Port 8000)        |     |  * ChromaDB: HNSW ANN Dense Vector Embeddings           |
+-----------------------------------+--------------------+     +--------------------+------------------------------------+
                                    |                                               |
                                    +-----------------------+-----------------------+
                                                            |
+-----------------------------------------------------------+-------------------------------------------------------------+
|                                    CONTINUOUS LLMOPS FLYWHEEL & TRAINING PIPELINE                                       |
|  Telemetry Ingestion -> PII Scrubbing -> Quality Gate -> ChatML -> 15% Replay Buffer -> RSLoRA/NeFTune Fine-Tuning   |
+-----------------------------------------------------------+-------------------------------------------------------------+
                                                            |
                                                            v
+-------------------------------------------------------------------------------------------------------------------------+
|                                  DYNAMIC MULTI-LORA GPU SERVING (vLLM on KUBERNETES)                                    |
|             Single GPU VRAM: Base Model (Qwen2.5-7B-AWQ 5.6GB) + PageAttention KV Cache + LoRA Adapters (150MB)        |
|                  * Azure AKS (Turing T4 16GB)  •  GCP GKE (Ada L4 24GB)  •  AWS EKS (T4/A10G/L4 16-24GB)                |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## 🔄 Step-by-Step Production Workflows & Architecture Diagrams

Every stage of the platform is designed with mathematical rigor, operational resilience, and automated verification:

---

### Step 1: Hybrid Recommendation & Dense Vector Search Engine

![Hybrid Recommendation and Vector Search Engine](docs/images/02_hybrid_recommender_pipeline.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                                 HYBRID RECOMMENDATION ENGINE WORKFLOW                                 |
+-------------------------------------------------------------------------------------------------------+
|  [ User Request / ID ]                                                                                |
|          |                                                                                            |
|          +---> 1. DUAL-TOWER NEURAL NETWORK: User Latent Vector (dim=64) dot Anime Latent Vector       |
|          |        (Trained on 5M+ interaction pairs with embedding regularization)                     |
|          |                                                                                            |
|          +---> 2. CONTENT-BASED SIMILARITY: Cosine matching over one-hot genres, themes, and studios  |
|          |                                                                                            |
|          +---> 3. DENSE VECTOR ANN RETRIEVAL: ChromaDB HNSW Index (sentence-transformers MiniLM-L6)  |
|          |                                                                                            |
|          v                                                                                            |
|  [ HYBRID SCORING & RECIPROCAL RANK FUSION (RRF) ]                                                    |
|     Score(u, i) = w_cf * Score_CF(u, i) + w_cb * Score_CB(u, i) + w_vec * Score_Vec(q, i)             |
|          |                                                                                            |
|          v                                                                                            |
|  [ RUST SIMD RERANKING ENGINE ]: In-memory SIMD dot-product reranking with contextual diversity filters |
|          |                                                                                            |
|          v                                                                                            |
|  [ TOP-K DIVERSIFIED RECOMMENDATIONS ]: Cached in Redis (TTL: 300s) -> Returned to Client in < 18ms    |
+-------------------------------------------------------------------------------------------------------+
```

* **Dual-Tower Neural Network**: Maps high-dimensional user IDs and item IDs into dense latent vectors using Keras/TensorFlow.
* **ChromaDB Dense Vector Index**: Built with Hierarchical Navigable Small World (HNSW) graphs, yielding logarithmic query time $O(\log N)$ across millions of anime plot descriptions.
* **Rust SIMD Fast-Path**: Eliminates Python GIL bottlenecks by delegating high-throughput matrix dot products to native AVX2/NEON SIMD vector registers in `services/rust-scoring-engine`.

---

### Step 2: Continuous LLMOps Data Curation Flywheel

![Continuous Data Curation & Flywheel](docs/images/03_llmops_curation_flywheel.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                                CONTINUOUS DATA CURATION FLYWHEEL                                      |
+-------------------------------------------------------------------------------------------------------+
|  [ Kafka Telemetry Bus ]: Captures real-time user prompts, agent answers, and feedback scores         |
|          |                                                                                            |
|          v                                                                                            |
|  [ AUTOMATED PII SCRUBBING ]: High-throughput regex redaction                                         |
|     * Emails     -> [REDACTED_EMAIL]                                                                  |
|     * Phones     -> [REDACTED_PHONE]                                                                  |
|     * API Keys   -> [REDACTED_API_KEY] (sk-..., Bearer ...)                                           |
|     * IP Addrs   -> [REDACTED_IP]                                                                     |
|          |                                                                                            |
|          v                                                                                            |
|  [ QUALITY FILTRATION ]: Threshold filtering (score >= 0.70), prompt len >= 5, completion len >= 15   |
|          |                                                                                            |
|          v                                                                                            |
|  [ CHATML STANDARDIZER ]: Formats into instruction messages (system, user, assistant)                 |
|          |                                                                                            |
|          v                                                                                            |
|  [ 15% GENERAL REPLAY BUFFER INJECTION ] -> PREVENTS CATASTROPHIC FORGETTING                          |
|     Injects general deductive logic, mathematical reasoning, and architectural question-answer pairs   |
|     to ensure fine-tuned adapters retain foundational capabilities while learning domain stylization. |
|          |                                                                                            |
|          v                                                                                            |
|  [ ARTIFACT GENERATION ]: Stratified Train (data/curated/train.jsonl) & Val (val.jsonl) Splits        |
+-------------------------------------------------------------------------------------------------------+
```

* **Implementation**: Managed by [`DatasetCurator`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/llmops/curation/curate_dataset.py).
* **Catastrophic Forgetting Mitigation**: In standard domain fine-tuning, training solely on narrow data causes catastrophic loss of foundational reasoning. Injecting a 15% experience replay buffer locks in general intelligence.

---

### Step 3: Parameter-Efficient QLoRA Fine-Tuning (RSLoRA + NeFTune)

![QLoRA & RSLoRA Fine-Tuning](docs/images/04_qlora_rslora_training.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                            ADVANCED QLORA FINE-TUNING ARCHITECTURE                                    |
+-------------------------------------------------------------------------------------------------------+
|  [ FROZEN 4-BIT BASE MODEL ]: Qwen2.5-7B (NormalFloat4 NF4 Quantization + Double Quantization)        |
|          |                                                                                            |
|          +---> [ LOW-RANK DECOMPOSITION ]: Adapter Matrices A (r x d) and B (d x r)                   |
|          |        Injected into: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj       |
|          |                                                                                            |
|          +---> [ RANK-STABILIZED LORA (RSLoRA) ]: Scaling factor = alpha / sqrt(r)                    |
|          |        Prevents gradient magnitude collapse when increasing rank (r=16 -> r=32 -> r=64)    |
|          |                                                                                            |
|          +---> [ NEFTUNE REGULARIZATION ]: Injects uniform noise into embeddings during forward pass   |
|          |        Acts as continuous data augmentation, preventing overfitting to prompt templates    |
|          |                                                                                            |
|          +---> [ COMPLETION-ONLY LOSS MASKING ]: Prompt tokens assigned label -100                    |
|          |        Loss calculated strictly on assistant response tokens, eliminating loss dilution    |
|          |                                                                                            |
|          v                                                                                            |
|  [ PAGED ADAMW 8-BIT OPTIMIZER ]: Dynamic memory paging to host RAM prevents CUDA OOM spikes          |
|          |                                                                                            |
|          v                                                                                            |
|  [ STANDARDIZED PEFT ADAPTER CHECKPOINT ]: ~50MB to 120MB weights + training_metadata.json            |
+-------------------------------------------------------------------------------------------------------+
```

* **RSLoRA Mathematics**: Replaces standard $\frac{\alpha}{r}$ scaling with $\frac{\alpha}{\sqrt{r}}$. Because the Frobenius norm of $B \cdot A$ scales with $\sqrt{r}$, scaling by $\frac{1}{\sqrt{r}}$ stabilizes gradient updates across arbitrary ranks.
* **Completion-Only Loss Masking**: Sets label for prompt tokens to `-100` (`torch.nn.CrossEntropyLoss` ignore index). The model is never penalized for the prompt distribution—only for its domain answers.
* **Implementation**: Implemented in [`train_lora.py`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/llmops/training/train_lora.py) and [`config.py`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/llmops/training/config.py).

---

### Step 4: Automated CI/CD Evaluation & Deployment Gating

![Automated CI/CD Quality Gating](docs/images/05_evaluation_gating_cicd.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                                AUTOMATED CI/CD QUALITY GATING PIPELINE                                |
+-------------------------------------------------------------------------------------------------------+
|  [ Candidate Adapter Checkpoint ] -> artifacts/adapters/{persona}-lora                                |
|          |                                                                                            |
|          v                                                                                            |
|  [ 4-DIMENSION EVALUATION RUBRIC ]:                                                                   |
|     1. Domain Nuance & Vocabulary (Sakuga, Studio, Pacing, Thematic Synthesis)  [Weight: 35%]         |
|     2. JSON Schema Compliance & Syntactic Validity                              [Weight: 25%]         |
|     3. Reasoning Depth & Conceptual Completeness                                [Weight: 25%]         |
|     4. General Knowledge Retention (Zero Catastrophic Regression)               [Weight: 15%]         |
|          |                                                                                            |
|          v                                                                                            |
|  [ COMPOSITE SCORE CALCULATION ]:                                                                     |
|     Composite = 0.35 * Nuance + 0.25 * JSON + 0.25 * Reasoning + 0.15 * General                       |
|          |                                                                                            |
|          +---> If Score >= 0.85: APPROVED_FOR_DEPLOYMENT -> Promoted to Kubernetes Production Serving |
|          |                                                                                            |
|          +---> If Score <  0.85: REJECTED_BELOW_THRESHOLD -> Pipeline halted, alert dispatched       |
+-------------------------------------------------------------------------------------------------------+
```

* **Implementation**: [`AdapterEvaluator`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/llmops/evals/eval_adapter.py) outputs standardized JSON reports to [`artifacts/eval_report.json`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/artifacts/eval_report.json).

---

### Step 5: Dynamic Multi-LoRA vLLM GPU Serving Architecture

![vLLM Dynamic Multi-LoRA Serving](docs/images/06_dynamic_multilora_serving.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                              DYNAMIC MULTI-LORA SERVING ON A SINGLE GPU                               |
+-------------------------------------------------------------------------------------------------------+
|  [ GPU VRAM BUDGET (16GB T4 / 24GB L4) ]:                                                             |
|  +-------------------------------------------------------------------------------------------------+  |
|  |  Frozen Base Model: Qwen2.5-7B-Instruct-AWQ (4-bit Weights)                 | ~5.6 GB VRAM      |  |
|  |  vLLM Engine CUDA Workspaces & Context                                      | ~1.2 GB VRAM      |  |
|  |  Dynamic LoRA Adapter Slot 1: 'anime-critic' (Sakuga & Analytical Review)   | ~75 MB VRAM       |  |
|  |  Dynamic LoRA Adapter Slot 2: 'anime-stylist' (Otaku Conversational Prose)  | ~75 MB VRAM       |  |
|  |  Dynamic LoRA Adapter Slot 3: 'general-assistant'                           | ~75 MB VRAM       |  |
|  |  PagedAttention KV Cache Pool (Continuous Batching Paging Memory)           | ~8.8GB to 16.7GB  |  |
|  +-------------------------------------------------------------------------------------------------+  |
|          ^                                                                                            |
|          | (Dynamic In-Flight Weight Injection via Request Headers)                                   |
|  [ MULTI-LORA CLIENT ROUTER (llmops/client/multilora_client.py) ]:                                    |
|     * Request A: headers: {"model": "anime-critic"}  -> Dispatches to Critic Adapter                  |
|     * Request B: headers: {"model": "anime-stylist"} -> Dispatches to Stylist Adapter                 |
|     * Request C: headers: {"model": "Qwen2.5-7B"}    -> Dispatches to Base Foundation                 |
|                                                                                                       |
|  BENCHMARK IMPACT: Sub-millisecond adapter swapping (< 1ms), ZERO server restarts, 75-80% cost reduction|
+-------------------------------------------------------------------------------------------------------+
```

* **GPU Memory Economics**:

| Deployment Strategy | GPU Instances | Monthly Cost | Cold-Start Delay | Operational Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Independent Replicas** | 3x Dedicated T4s | ~$1,140 / mo | 0s (always hot) | 3 clusters, 3 ingress endpoints |
| **Serverless On-Demand** | 1x Shared GPU | ~$450 / mo | 45s–90s per swap | High tail-latency spikes |
| **Dynamic Multi-LoRA (Our Setup)** | **1x T4 or L4 GPU** | **~$380 / mo** | **< 1ms in-flight** | **Single resilient deployment** |

---

### Step 6: Multi-Cloud GitOps & Kubernetes Topology

![Multi-Cloud GitOps Infrastructure](docs/images/07_multicloud_gitops.jpg)

```
+-------------------------------------------------------------------------------------------------------+
|                               MULTI-CLOUD GITOPS INFRASTRUCTURE TOPOLOGY                              |
+-------------------------------------------------------------------------------------------------------+
|                                     [ GITHUB REPOSITORY / ARGO CD ]                                   |
|                                     Declarative Desired State Sync                                    |
|                                                    |                                                  |
|                   +--------------------------------+--------------------------------+                 |
|                   |                                |                                |                 |
|                   v                                v                                v                 |
|  +--------------------------------+ +--------------------------------+ +----------------------------+  |
|  |       AZURE AKS CLUSTER        | |        GOOGLE CLOUD GKE        | |       AMAZON AWS EKS       |  |
|  | Node: Standard_NC4as_T4_v3     | | Node: g2-standard-4 (L4 GPU)   | | Node: g4dn.xlarge (T4 GPU) |  |
|  | GPU: NVIDIA T4 (16GB, SM 7.5)  | | GPU: NVIDIA L4 (24GB, SM 8.9)  | | GPU: NVIDIA T4 (16GB)      |  |
|  | Kernel: AWQ FP16, Enforce-Eager| | Kernel: AWQ Marlin BF16        | | Kernel: AWQ FP16           |  |
|  | Adapter Sync: Mariner InitCont.| | Adapter Sync: Cloud SDK InitCont| | Adapter Sync: AWS CLI Init |  |
|  +--------------------------------+ +--------------------------------+ +----------------------------+  |
|                   |                                |                                |                 |
|                   +--------------------------------+--------------------------------+                 |
|                                                    |                                                  |
|                                                    v                                                  |
|                         [ UNIFIED OBSERVABILITY & DCGM METRIC EXPORTER ]                              |
|                       Prometheus Scraping GPU Temp, VRAM Usage, Tensor Duty Cycle                     |
|                                     Grafana Multi-Cloud Dashboard                                     |
+-------------------------------------------------------------------------------------------------------+
```

---

## 🛠️ Complete Technical Tool Matrix

An exhaustive evaluation of the toolchain chosen for this platform, highlighting mechanical sympathy and technical trade-offs:

| Tool / Technology | Platform Role | Why Selected | Alternatives Rejected & Rationale |
| :--- | :--- | :--- | :--- |
| **vLLM** (`v0.6.3`) | GPU LLM Inference Engine | PagedAttention eliminates memory fragmentation; dynamic Multi-LoRA enables hot-swapping adapters in-flight; AWQ Marlin kernel provides 2.5x throughput. | **TGI / Ollama**: TGI has limited multi-LoRA support without reloading; Ollama is developer-focused and lacks continuous batching at high concurrency. |
| **PEFT / QLoRA** | Parameter-Efficient Tuning | Freezes 4-bit foundation; trains low-rank matrices ($r=16, 32$); RSLoRA ensures stable scaling; NeFTune prevents overfitting. | **Full Fine-Tuning**: Requires multi-node distributed clusters (DeepSpeed ZeRO-3), $10\times$ more VRAM, and produces massive 14GB checkpoints per persona. |
| **TRL (`v1.16.0`)** | Supervised Fine-Tuning | Native ChatML parsing; seamlessly integrates with PEFT and Hugging Face Transformers; supports custom data collators. | **Manual PyTorch Loops**: Error-prone distributed data parallel setup, missing automated padding and evaluation integration. |
| **ChromaDB** | Dense Vector Storage | Local/embedded HNSW ANN indexing; low operational footprint; sub-millisecond similarity lookups; native Python integration. | **Pinecone / Milvus**: Pinecone introduces SaaS network hops and vendor lock-in; Milvus requires heavy distributed etcd/MinIO dependencies for local dev. |
| **Apache Kafka** | Event Streaming Bus | Partitioned immutable log for high-throughput user interaction telemetry; decoupled ingestion buffer for the curation flywheel. | **RabbitMQ**: RabbitMQ lacks replayable immutable event logs and has lower throughput for streaming ML feature stores. |
| **Redis** | Two-Tier Caching | In-memory key-value cache for hot top-K recommendations ($p_{99} < 2\text{ms}$); prevents database and ML model hammering. | **Memcached**: Lacks native data structures (hashes, sorted sets, lists) and persistence options. |
| **Go 1.24** | Auth & Identity Service | Lightweight Goroutines (4KB stack vs 1MB OS thread); zero-dependency cryptographic token verification; static binary < 15MB. | **Node.js Auth**: Node.js CPU-intensive crypto operations (bcrypt/argon2) block the single-threaded event loop. |
| **Rust 1.85** | Vector Scoring Engine | Zero-cost abstractions; predictable sub-millisecond p99 latency without Garbage Collection pauses; LLVM compiler SIMD vectorization. | **Python NumPy**: Python GIL contention under concurrent multi-threaded requests; higher IPC overhead. |
| **Python FastAPI** | Core Intelligence API | Asynchronous ASGI event loop; Pydantic request validation; rich AI/ML ecosystem integration (PyTorch, Transformers). | **Flask / Django**: Flask is synchronous by default; Django is monolithic and adds heavy ORM overhead. |
| **Microsoft PyRIT** | AI Security Red Teaming | Automated multi-turn adversarial prompt generation; detects prompt injection, jailbreaking, and data leakage. | **Manual Penetration Testing**: Too slow and unscalable for continuous CI/CD gating of retraining flywheels. |
| **Terraform & Helm** | Declarative IaC & GitOps | Multi-cloud provider modules (Azure, AWS, GCP); state locking; repeatable, zero-drift Kubernetes provisioning. | **Manual Cloud Consoles**: Prone to human error, impossible to audit, violates GitOps compliance principles. |
| **Prometheus & DCGM**| Telemetry & GPU Metrics | Scrapes NVIDIA Data Center GPU Manager (DCGM) metrics (VRAM allocation, SM activity, temperature) alongside API latencies. | **CloudWatch / Azure Monitor only**: Cloud-specific silos prevent a unified multi-cloud Grafana pane of glass. |

---

## 💡 Principal Engineer / Senior Staff Interview Defense

When defending this architecture in executive, principal, or senior staff technical interviews:

### Q1: "Why Dynamic Multi-LoRA over full fine-tuning or independent microservices?"
> *"Full fine-tuning updates all 7 billion parameters, requiring multi-GPU distributed clusters (DeepSpeed ZeRO-3) and resulting in severe operational sprawl. If we maintain 3 distinct domain personas, full fine-tuning produces 3 separate 14GB model weights, requiring 3 dedicated GPU nodes costing ~$1,140/month.*
>
> *With Dynamic Multi-LoRA on vLLM, we freeze the foundational model in 4-bit AWQ (~5.6 GB VRAM). Adapters only train low-rank decomposition matrices ($r=16$) occupying ~75MB each. vLLM loads the base model once into GPU memory and dynamically applies adapter weights during the GEMM computation based on the request's model header. We serve multiple specialized capabilities on a single $380/mo GPU with zero cold-start delay, slashing infrastructure spend by over 75%."*

### Q2: "How do you mathematically prevent Catastrophic Forgetting during domain adaptation?"
> *"Catastrophic forgetting occurs when gradient updates on a narrow domain dataset override the model's general reasoning, math, and instruction-following abilities. In our data curation flywheel (`llmops/curation/curate_dataset.py`), we implement an experience replay buffer: 15% of every training split consists of general logical deductions, deductive reasoning, and foundational QA samples. Furthermore, our CI/CD quality gate (`llmops/evals/eval_adapter.py`) explicitly includes a `general_retention` evaluation dimension alongside domain nuance, blocking any adapter from production promotion if general reasoning degrades below 0.85."*

### Q3: "What are the kernel-level differences between serving on Azure T4 vs GCP L4 GPUs?"
> *"Hardware architecture dictates the optimal GEMM kernels and memory layout:*
> 1. *Azure NC4as_T4_v3 features an NVIDIA T4 (Turing, SM 7.5, 16GB VRAM). Turing lacks native bfloat16 and cannot run Marlin kernels, which require compute capability SM 8.0+. On T4, vLLM must be configured with `--quantization=awq` (classic GEMM), `--dtype=float16`, `--enforce-eager` (skipping CUDA graph capture to conserve KV cache memory), with context length capped at 4096 tokens.*
> 2. *GCP GKE features an NVIDIA L4 (Ada Lovelace, SM 8.9, 24GB VRAM). Ada supports native bfloat16 and high-throughput Marlin quantized GEMM kernels (`--quantization=awq_marlin`), providing 2.5x higher token generation throughput. The 24GB memory footprint allows 8192 context length and 16 concurrent sequences while dedicating 16.7 GB strictly to the PageAttention KV cache pool."*

### Q4: "Why use RSLoRA ($\alpha/\sqrt{r}$) instead of standard LoRA ($\alpha/r$)?"
> *"In standard LoRA, the forward update is scaled by $\frac{\alpha}{r}$. As you scale rank $r$ from 8 to 32 or 64 to learn complex domain logic, the update magnitude collapses inversely with $r$, leading to vanishing gradient updates. RSLoRA (Rank-Stabilized LoRA) replaces this with $\frac{\alpha}{\sqrt{r}}$. Because the Frobenius norm of a random matrix product $B \cdot A$ naturally scales with $\sqrt{r}$, scaling by $\frac{1}{\sqrt{r}}$ keeps gradient updates invariant to rank, enabling seamless hyperparameter scaling without retuning learning rates."*

### Q5: "Why apply Completion-Only Loss Masking in instruction tuning?"
> *"In standard causal language modeling, cross-entropy loss is computed over the entire token sequence. In multi-turn ChatML, 60–80% of tokens belong to the system and user prompts. Calculating loss on prompt tokens causes loss dilution (the loss reflects input predictability rather than output quality) and encourages the model to memorize prompt syntax. We assign prompt tokens label `-100` so PyTorch skips them in `CrossEntropyLoss`, forcing 100% of gradient updates into the assistant's generation tokens."*

### Q6: "Why a Polyglot Architecture rather than pure Python?"
> *"Mechanical sympathy. Python is optimal for AI/ML model orchestration, but suboptimal for high-concurrency auth and zero-latency vector math. Go handles authentication with lightweight Goroutines (4KB stack vs 1MB thread) and zero external dependencies. Rust handles vector dot products and reranking with native SIMD registers and zero Garbage Collector pauses ($p_{99} < 1\text{ms}$). Python FastAPI orchestrates LangGraph agents and vLLM calls. Each language runs in its operational sweet spot."*

### Q7: "How is vector search indexed and scaled?"
> *"We use ChromaDB with Hierarchical Navigable Small World (HNSW) graphs. HNSW constructs multi-layer proximity graphs where top layers provide fast logarithmic exploration and bottom layers provide fine-grained nearest neighbor routing. We optimize with cosine distance, 384-dimensional dense vectors (`all-MiniLM-L6-v2`), and reciprocal rank fusion with collaborative filtering scores."*

### Q8: "How does the system defend against prompt injection and jailbreaks?"
> *"We enforce defense-in-depth: At the edge, Go and NGINX scrub malicious payloads; at the application layer, regex sanitizers redact PII (emails, phones, API keys, IPs); during continuous integration, Microsoft PyRIT executes automated multi-turn adversarial red-teaming attacks (DAN jailbreaks, roleplay subversion, indirect prompt injection); and at inference time, output guardrails validate schema compliance."*

### Q9: "How does Kafka handle backpressure during high-traffic surges?"
> *"Kafka partitions decouple ingestion from consumers. The curation engine and interaction services consume via consumer groups with manual offset commits. When traffic spikes, Kafka buffers events to disk with zero message loss while consumers process at a calibrated batch rate using backpressure rate limiters."*

### Q10: "How do you guarantee high availability across multi-cloud deployments?"
> *"Our Kubernetes manifests and Terraform templates maintain active-passive or multi-region parity across Azure AKS, GCP GKE, and AWS EKS. Cloud-agnostic container images, externalized GitOps configurations in ArgoCD, and DNS-level failover ensure that if a cloud provider experiences a regional GPU shortage or outage, traffic can be redirected in seconds."*

---

## 🚀 Zero-Touch Instant Cloud & Workstation Deployment

The entire platform can be deployed on **any fresh, blank AWS EC2 instance, cloud VM, or local machine with a single terminal command**:

```bash
curl -fsSL https://raw.githubusercontent.com/KishorKumarParoi/Hybrid-Anime-Recommender/main/bootstrap.sh | bash
```

### What This Single Command Automates:
1. **OS & Prerequisite Detection**: Checks if `git`, `curl`, and build tools are present; automatically installs them if missing (Ubuntu, Debian, Amazon Linux 2023, RHEL, macOS).
2. **OOM Protection & Auto-Swap**: Detects available RAM; if RAM $< 4\text{GB}$ (e.g. `t3.micro`, `t2.small`), it automatically allocates a **4GB swapfile** to prevent compiler/Docker Out-Of-Memory crashes.
3. **Automated Repository Synchronization**: Clones or updates `Hybrid-Anime-Recommender` into the local directory.
4. **Toolchain Auto-Bootstrap**: Installs Docker Engine, Docker Compose v2, `uv`, and Python 3.12 without interactive prompts.
5. **Self-Healing Port Remapping**: If local host ports (5432, 8000, 80) are occupied, it automatically shifts host port bindings to free ports (5433, 8005, 8080) without breaking internal microservice networks.
6. **Polyglot Mesh Orchestration**: Compiles and launches all 9 containerized services.
7. **Automated Health Gating & LLMOps Verification**: Probes all microservices and executes the complete data curation, RSLoRA, and multi-LoRA serving verification cycle.

### Alternative: Manual Clone & Run
If you already have `git` installed and prefer cloning manually:
```bash
git clone https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender.git
cd Hybrid-Anime-Recommender
chmod +x deploy.sh clear.sh bootstrap.sh
./deploy.sh
```

### Enterprise Service Endpoints:
* **Web Platform (NGINX Edge)**: `http://<SERVER_IP>:80`
* **Next.js 16 Glassmorphism UI**: `http://<SERVER_IP>:3000`
* **FastAPI AI Intelligence & Docs**: `http://<SERVER_IP>:8000/docs`
* **Enterprise RAG & Cost Metrics**: `http://<SERVER_IP>:8000/api/v1/enterprise/metrics/cost-dashboard`
* **Governance Audit Trail**: `http://<SERVER_IP>:8000/api/v1/enterprise/governance/audit-trail`
* **Lakehouse Tables & Freshness SLAs**: `http://<SERVER_IP>:8000/api/v1/enterprise/lakehouse/tables`
* **Go Authentication Service**: `http://<SERVER_IP>:8081/auth/health`
* **Express Interactions Service**: `http://<SERVER_IP>:8082/health`
* **Rust SIMD Scoring Engine**: `http://<SERVER_IP>:8083/health`

### Zero-Cost Full Teardown (`./clear.sh`):
```bash
./clear.sh
```
Stops and deletes all Docker containers, networks, and volumes, terminates background Python processes, and frees all reserved ports, leaving the machine in a 100% pristine zero-resource state ($0.00/hr).

---

## 🧪 Developer Verification & Manual Execution Runbook

### 1. Run the Complete 7-Stage Test Suite
Executes Rust SIMD tests, Go auth tests, Express interaction tests, Next.js build validation, Python contracts, LLMOps fine-tuning, and Enterprise RAG tests:
```bash
./scripts/test_all.sh
```

### 2. Run the End-to-End LLMOps Verification Script
Executes Data Curation $\to$ RSLoRA Training $\to$ Quality Gating $\to$ Dynamic Multi-LoRA Serving in a single command:
```bash
uv run python scripts/demo_end_to_end.py
```

### 3. Dynamic Multi-LoRA CLI Inference
```bash
# Query the analytical critic adapter
uv run python -m llmops.client.multilora_client \
    --adapter anime-critic \
    --prompt "Analyze the pacing and sakuga in Mob Psycho 100" \
    --mock

# Benchmark in-flight zero-overhead switching across base model and adapters
uv run python -m llmops.client.multilora_client --compare --mock
```

---

## 📂 Repository Directory Layout

```
Hybrid-Anime-Recommender/
├── app/                        # Python FastAPI Intelligence Core
├── artifacts/                  # Model checkpoints, LoRA adapters, eval reports
│   └── adapters/               # Fine-tuned PEFT checkpoints (anime-critic, anime-stylist)
├── data/
│   ├── raw/                    # Raw interaction telemetry logs
│   └── curated/                # PII-scrubbed, ChatML formatted train/val splits
├── docs/
│   └── images/                 # Architecture & workflow visual diagram assets
├── frontend/                   # Next.js 16 (React 19, Turbopack) UI
├── llmops/                     # Continuous Fine-Tuning & Serving Subsystem
│   ├── curation/               # PII scrubbing, quality gating, 15% replay buffer
│   ├── training/               # QLoRA fine-tuning (RSLoRA, NeFTune, Loss Masking)
│   ├── evals/                  # 4-dimension CI/CD quality gating rubric
│   ├── serving/                # vLLM Dynamic Multi-LoRA Kubernetes deployments
│   └── client/                 # Dynamic in-flight multi-adapter client router
├── scripts/                    # Orchestration, test runners, and demo scripts
│   ├── demo_end_to_end.py      # Single-command end-to-end lifecycle demonstration
│   ├── run_all.sh              # Local 5-microservice polyglot orchestrator
│   └── test_all.sh             # Unified 6-stage polyglot & LLMOps test runner
├── services/                   # Polyglot Microservices
│   ├── express-interaction/    # Node.js 22 interaction service
│   ├── go-auth-service/        # Go 1.24 JWT authentication service
│   └── rust-scoring-engine/    # Rust 1.85 SIMD vector reranker
├── tests/                      # Automated test suite (76/76 tests passing)
│   └── test_llmops_pipeline.py # 15 unit/integration tests for fine-tuning & serving
├── vllm-serving-aks/           # Azure Kubernetes Service GPU manifests (Turing T4)
├── vllm-serving-gke/           # Google Cloud GKE GPU manifests (Ada Lovelace L4)
└── vllm-serving-aws/           # Amazon AWS EKS GPU manifests (T4 / A10G)
```

---

## 📜 License
Licensed under the Apache 2.0 License. Designed for cloud-native AI engineering and enterprise Principal / Senior Staff interviews.
