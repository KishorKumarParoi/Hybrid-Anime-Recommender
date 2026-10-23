# 🎓 Master Step-by-Step Learning Guide: Hybrid Anime Intelligence & Continuous LLMOps Platform

**Standard**: Principal AI Systems Architect & Senior Staff Engineer  
**Scope**: Polyglot Microservices (Python, Rust, Go, Node.js) • Hybrid Recommender • Continuous LLMOps Flywheel • Dynamic Multi-LoRA on vLLM • Multi-Cloud Kubernetes (AKS/GKE/EKS) • AI Red Teaming (PyRIT)

---

## 🗺️ Curriculum Blueprint

Follow this step-by-step curriculum to master the platform from mathematical foundations to cloud production:

```
+-------------------------------------------------------------------------------------------------------------+
|                                        CURRICULUM BLUEPRINT ROADMAP                                         |
+-------------------------------------------------------------------------------------------------------------+
|  [ Module 0: Architecture ]  -->  [ Module 1: Polyglot Mesh ]     -->  [ Module 2: Vector Scoring & HNSW ]  |
|                                                                                                             |
|  [ Module 3: Continuous LLMOps ] --> [ Module 4: RSLoRA & NeFTune ] --> [ Module 5: Dynamic Multi-LoRA vLLM] |
|                                                                                                             |
|  [ Module 6: Multi-Cloud GitOps ] -> [ Module 7: PyRIT AI Security ] -> [ Module 8: Principal Interview ]   |
+-------------------------------------------------------------------------------------------------------------+
```

---

## Module 0: System Architecture & Problem Formulation

### 1. Problem Statement
Modern recommendation systems face the **Cold-Start Problem** and the **Semantic Gap**:
- Collaborative filtering alone fails when new anime titles or new users enter the system.
- Content-based filtering alone fails to capture emergent community preferences and latent tastes.
- Generative AI explanation agents are traditionally too expensive ($0.03/query) and slow (3,000ms latency) to serve at scale.

### 2. The Hybrid Solution
Our platform bridges three complementary paradigms:
1. **Dual-Tower Neural Collaborative Filtering (NCF)**: User and item embedding towers trained on historical rating matrices.
2. **Dense Vector Search (ChromaDB HNSW)**: 1536-dimensional semantic representations of anime synopsis, genres, and themes.
3. **Dynamic Multi-LoRA vLLM Serving**: A single frozen 4-bit base model (`Qwen2.5-7B-Instruct-AWQ`) with dynamically swappable LoRA adapters (`anime-critic`, `anime-stylist`) running in under 25ms.

Review the architectural flow diagram in [`docs/images/01_architecture_overview.jpg`](docs/images/01_architecture_overview.jpg).

---

## Module 1: Polyglot Event-Driven Microservices

### 1. Architectural Philosophy
Different programming languages excel at different tasks:
- **Go 1.24**: Concurrency, lightweight goroutines, and secure JWT authentication.
- **Rust 1.85**: SIMD hardware-accelerated vector dot-product scoring with zero garbage collection pauses.
- **Node.js 22**: Event-driven asynchronous user interaction logging to MongoDB.
- **Python 3.12**: PyTorch, Hugging Face transformers, and FastAPI orchestration.

### 2. Service Layout: `services/`
1. **Go Auth Service (`services/go-auth-service/`)**:
   - Listens on port `8081`.
   - Validates HMAC-SHA256 JWT tokens with sub-millisecond overhead.
2. **Rust Vector Scoring Engine (`services/rust-scoring-engine/`)**:
   - Listens on port `8083`.
   - Uses AVX2 / NEON SIMD intrinsics to compute cosine similarity across 50,000 candidates in `< 1.2 milliseconds`.
3. **Apache Kafka Event Bus**:
   - Topic `anime.telemetry.interactions`: Ingests clicks, watch time, and ratings at 10,000+ events/sec.

---

## Module 2: Vector Embeddings & Dense Search (ChromaDB HNSW)

### 1. Hierarchical Navigable Small World (HNSW)
Open [`src/recommender/`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/src/recommender/):
- **Graph Construction**: HNSW builds a multi-layer geometric graph where upper layers have long-range skips and bottom layers perform greedy local search.
- **Distance Metric**: Cosine similarity normalized over L2 unit spheres:
  $$\text{sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
- **Metadata Filters**: Combining dense similarity with categorical SQL-style filters (e.g. `genre IN ['Action', 'Sci-Fi'] AND rating >= 8.0`).

---

## Module 3: Continuous LLMOps Flywheel & Data Curation

### 1. The Autonomous Retraining Flywheel
Review [`docs/images/03_llmops_curation_flywheel.jpg`](docs/images/03_llmops_curation_flywheel.jpg):
1. **Telemetry Ingestion**: Real-time interactions stream from Kafka to the curation pipeline.
2. **PII Scrubbing**: Presidio regex strips user emails, usernames, and payment info.
3. **Quality Gate (LLM-as-a-Judge)**: Evaluates interaction transcripts for helpfulness, tone, and factual grounding ($G \ge 4.2 / 5.0$).
4. **15% General Reasoning Replay Buffer**: Mixes domain-specific anime chat pairs with general mathematical and logical reasoning pairs to **prevent catastrophic forgetting**.

---

## Module 4: Advanced Fine-Tuning Mathematics & RSLoRA

### 1. Rank-Stabilized LoRA (RSLoRA)
Traditional LoRA scales weight updates as $\Delta W = \frac{\alpha}{r} (B \times A)$. When scaling rank $r$ from 8 to 64, this causes gradient shrinkage.
**RSLoRA** normalizes scaling by the square root of rank:
$$\Delta W = \frac{\alpha}{\sqrt{r}} (B \times A)$$
This stabilizes optimization dynamics and preserves learning capacity across wide adapters.

### 2. NeFTune (Noisy Embedding Fine-Tuning)
Adds uniform random noise to input embedding layers during forward passes:
$$e' = e + \epsilon, \quad \epsilon \sim \text{Uniform}\left(-\frac{\alpha}{\sqrt{L \cdot d}}, \frac{\alpha}{\sqrt{L \cdot d}}\right)$$
Prevents the model from overfitting to superficial token phrasing and dramatically improves conversational fluency.

### 3. Completion-Only Loss Masking
Tokens in the system prompt and user query have their labels set to `-100`, ensuring cross-entropy loss is computed **only on assistant response tokens**.

---

## Module 5: Dynamic Multi-LoRA Serving on vLLM

### 1. The Multi-GPU Problem vs. Single-GPU vLLM
Hosting 3 fine-tuned 7B models traditionally requires 3 separate GPU instances ($3 \times \$1,100 = \$3,300/\text{mo}$).
**Dynamic Multi-LoRA on vLLM**:
- Loads one frozen base model in 4-bit AWQ (5.6 GB VRAM).
- Dynamic LoRA adapters (150 MB each) are loaded into host RAM and dynamically scheduled into GPU VRAM in `< 1ms`.
- **Compute Savings**: Reduces GPU footprint by **75–87.5%**, running on a single NVIDIA A10G (24 GB) or T4 (16 GB).

Review [`docs/images/06_dynamic_multilora_serving.jpg`](docs/images/06_dynamic_multilora_serving.jpg).

---

## Module 6: Multi-Cloud Kubernetes & GitOps

### 1. Infrastructure as Code: `terraform/`
Inspect Terraform configurations across 3 major cloud providers:
- **Azure AKS (`terraform/azure/`)**: GPU nodepool with NVIDIA Turing T4 instances.
- **Google Cloud GKE (`terraform/gcp/`)**: GKE Autopilot / Standard nodepool with NVIDIA Ada Lovelace L4 instances.
- **AWS EKS (`terraform/aws/`)**: EKS managed nodepool with NVIDIA A10G (`g5.xlarge`) instances.

### 2. GitOps with ArgoCD (`argocd/`)
Declarative Kubernetes state synced from git repository:
```bash
kubectl apply -f argocd/application.yaml
```

---

## Module 7: AI Security & Red Teaming (Microsoft PyRIT)

### 1. Defense-in-Depth AI Security: `src/security/`
- **Adversarial Jailbreak Detection**: Microsoft PyRIT automated red-teaming orchestrator simulating Crescendo and DAN jailbreak prompts.
- **Semantic Prompt Shield**: Cosine distance embedding boundary rejecting adversarial injections before token generation.
- **PyRIT Dashboard (`pyrit_dashboard/`)**: Streamlit portal monitoring jailbreak attempt rates, blocked attack vectors, and vulnerability heatmaps.

---

## Module 8: Principal Engineer Interview & Comp Playbook

### 1. Systems Design Whiteboarding
Review [`docs/INTERVIEW_COMP_PLAYBOOK.md`](file:///Users/kishorkumarparoi/Desktop/Hybrid-Anime-Recommender/docs/INTERVIEW_COMP_PLAYBOOK.md):
- Clarify functional vs non-functional requirements.
- Whiteboard data plane (low latency) vs control plane (batch training).
- Trade-off matrix: Latency vs Cost vs VPC Privacy.

### 2. Behavioral STAR Stories & Comp Negotiation
- High-severity incident triage under live traffic.
- Zero-downtime multi-cloud Kubernetes migrations.
- Total compensation negotiation scripts for Bengaluru, Hyderabad, and global tech hubs.
