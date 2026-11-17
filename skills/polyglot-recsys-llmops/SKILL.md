---
name: polyglot-recsys-llmops
description: |
  Enterprise architect skill for designing, scaffolding, and deploying high-throughput polyglot recommendation engines and continuous LLMOps platforms.
  Use when:
  - Designing or benchmarking sub-millisecond vector similarity scoring engines using Rust SIMD (AVX-512 / AVX2).
  - Architecting polyglot microservices (Rust math engine, Go auth, Node.js clickstream/interactions, Python FastAPI AI core).
  - Setting up Continuous LLMOps with RSLoRA (Rank-Stabilized LoRA) fine-tuning and dynamic Multi-LoRA serving on vLLM.
  - Implementing multi-stage candidate retrieval (dense dual-embeddings + sparse lexical BM25 + FlashRank re-ranking).
  - Deploying autonomous LangGraph research dossiers with NeMo safety guardrails and Redis semantic caching (<12ms).
  - Configuring cloud-native MLOps orchestration (Kubeflow, ArgoCD, KEDA auto-scaling, Terraform IaC across AWS, Azure, GCP).
  - Hardening AI systems with Microsoft PyRIT automated adversarial red-team testing.
  Don't use when:
  - Building simple monolithic single-script ML demos with no latency, scaling, or security constraints.
  - Performing basic database CRUD without vector search, recommendation, or LLM serving.
license: MIT
metadata:
  version: 2.1.0
  publisher: Kishor Kumar Paroi
  author: Kishor Kumar Paroi (Principal AI Systems Architect)
  tags:
    - recommender-systems
    - llmops
    - rust-simd
    - vllm-multilora
    - polyglot-microservices
    - langgraph
    - pyrit-security
---

# 🚀 Polyglot Recommender Systems & Continuous LLMOps Architect

An enterprise-grade agent skill for engineering, optimizing, and operating high-throughput recommendation systems and continuous LLM fine-tuning pipelines. This skill equips AI coding agents (Claude Code, Cursor, Windsurf, Antigravity) with principal engineer patterns for mechanical sympathy, sub-millisecond vector math, dynamic Multi-LoRA inference, and enterprise governance.

---

## 🏛️ Architectural Directives & Mechanical Sympathy

When designing or reviewing recommender systems and AI inference backends, enforce **language-specific hardware allocation**:

```
                                  [ CLIENT TIER ]
                           Next.js 16 (React 19) / Mobile
                                         │
                             [ NGINX REVERSE PROXY ]
                                         │
     ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
     │                   │                               │                   │
┌────▼──────────┐ ┌──────▼────────────┐ ┌────────────────▼──────┐ ┌──────────▼──────────────┐
│  Go Auth Svc  │ │ Node.js Express   │ │   Rust SIMD Scoring   │ │   Python FastAPI Core   │
│  (Port 8081)  │ │   (Port 8082)     │ │      (Port 8083)      │ │       (Port 8000)       │
├───────────────┤ ├───────────────────┤ ├───────────────────────┤ ├─────────────────────────┤
│ • Native JWT  │ │ • Likes/Reviews   │ │ • AVX2/AVX-512 SIMD   │ │ • LangGraph Multi-Agent │
│ • Bcrypt Hash │ │ • Watchlists      │ │ • Zero GC pauses      │ │ • Dual-Embedding Recs   │
│ • RBAC Engine │ │ • Non-blocking IO │ │ • Sub-millisecond p99 │ │ • PyRIT AI Red Team     │
│ • <15MB Image │ │ • JSON streaming  │ │ • Actix-web async     │ │ • vLLM Multi-LoRA Router│
└───────┬───────┘ └───────┬───────────┘ └───────────┬───────────┘ └────────────┬────────────┘
        │                 │                         │                          │
   [PostgreSQL]      [MongoDB]               [Candidate Cache]            [Vector DB]
   Relational DB   Document Store             Redis (Port 6379)         Qdrant / ChromaDB
```

### Microservice Decision Matrix
1. **Rust (`services/rust-scoring-engine`)**:
   - Compute-bound vector arithmetic (Dot-product cosine similarity, Euclidean distance, Top-K heap selection).
   - Use AVX2/AVX-512 vector intrinsics (`std::arch::x86_64`) or zero-alloc iterators with `#[inline(always)]`.
   - Never introduce Garbage Collector pauses in the critical hot-path scoring loop.
2. **Go (`services/go-auth-service`)**:
   - Identity verification, native HS256/RS256 JWT minting, role-based access control (RBAC).
   - Concurrency with lightweight 2KB–4KB Goroutines instead of heavyweight OS threads.
3. **Node.js Express (`services/express-interaction-service`)**:
   - Write-heavy interaction streaming (ratings, bookmarks, clicks, impression logs).
   - Non-blocking event loop provides zero impedance mismatch with document stores (MongoDB).
4. **Python FastAPI (`app/`)**:
   - Dense candidate retrieval (Two-Tower embeddings), LangGraph agent dossiers, PyRIT red-teaming, and continuous fine-tuning pipelines.

---

## ⚡ Rust SIMD Vector Dot Product Blueprint

When implementing or optimizing vector candidate scoring, follow this zero-allocation pattern:

```rust
#[inline(always)]
pub fn cosine_similarity_simd(a: &[f32], b: &[f32]) -> f32 {
    assert_eq!(a.len(), b.len(), "Vectors must have identical dimensions");
    
    let mut dot_prod = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;

    // Process 8 floats per cycle using AVX2 or auto-vectorized chunks
    let chunks_a = a.chunks_exact(8);
    let chunks_b = b.chunks_exact(8);
    let rem_a = chunks_a.remainder();
    let rem_b = chunks_b.remainder();

    for (ca, cb) in chunks_a.zip(chunks_b) {
        for i in 0..8 {
            dot_prod += ca[i] * cb[i];
            norm_a += ca[i] * ca[i];
            norm_b += cb[i] * cb[i];
        }
    }

    // Remainder tail loop
    for (va, vb) in rem_a.iter().zip(rem_b.iter()) {
        dot_prod += va * vb;
        norm_a += va * va;
        norm_b += vb * vb;
    }

    let denominator = norm_a.sqrt() * norm_b.sqrt();
    if denominator == 0.0 { 0.0 } else { dot_prod / denominator }
}
```

---

## 🧠 Continuous LLMOps & Dynamic Multi-LoRA Serving

### 1. Rank-Stabilized LoRA (RSLoRA) Fine-Tuning
Standard LoRA uses scaling factor $\frac{\alpha}{r}$, which degrades training stability when scaling to high ranks ($r \ge 32$). Enforce **RSLoRA** with scaling factor:
$$\alpha_{r} = \frac{\gamma}{\sqrt{r}}$$

```python
from peft import LoraConfig

def get_rslora_config(rank: int = 16, lora_alpha: int = 32) -> LoraConfig:
    return LoraConfig(
        r=rank,
        lora_alpha=lora_alpha,
        use_rslora=True,  # Scales by 1/sqrt(r) to prevent gradient collapse
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
```

### 2. vLLM Multi-LoRA Dynamic Routing
Instead of provisioning separate 8B/70B model replicas for specialized tasks:
- Maintain **one base model** (e.g. `Meta-Llama-3.1-8B-Instruct`) in GPU VRAM.
- Enable `--enable-lora` and `--max-loras 8` in the vLLM server launch arguments.
- Pass the adapter dynamically per request header `X-LoRA-Adapter: anime_genre_expert`:

```python
import httpx

async def invoke_multilora(prompt: str, adapter_name: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://vllm-serving:8000/v1/completions",
            json={
                "model": adapter_name,  # Dynamically points to loaded LoRA
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.3
            },
            timeout=10.0
        )
        return resp.json()["choices"][0]["text"]
```

---

## 🛡️ Enterprise AI Red-Teaming (PyRIT) & Safety Architecture

Before routing queries to the multi-agent synthesis layer:
1. **Semantic Cache Filter (<12ms)**:
   - Query embedding calculated via small dense encoder.
   - Lookup in Redis vector index: If cosine similarity $\ge 0.96$, return cached dossier immediately.
2. **PyRIT & NeMo Guardrails**:
   - Probe incoming queries for jailbreaks, persona hijacking, and instruction-tuning override attempts.
   - Enforce programmatic output schemas with zero hallucinations.

---

## 📦 Bundled Production Utilities

This skill includes standalone runnable scripts in `./scripts/` and reference templates in `./references/`:
* `scripts/simd_bench.py`: Benchmarks SIMD dot-product throughput vs Python loops.
* `scripts/rslora_config_gen.py`: Generates verified Hugging Face PEFT RSLoRA YAML configs.
* `scripts/vllm_multilora_router.py`: Production async router for dynamic LoRA requests.
* `references/architecture_manifesto.md`: Full architectural reference and data flows.
* `references/production_docker_compose.yml`: Zero-touch containerized mesh config.

---

## 🎯 Verification Checklist

Before deploying any production recommendation or LLMOps service:
- [ ] **Scoring Latency**: Hot-path vector candidate scoring p99 $< 1\text{ms}$.
- [ ] **Memory Footprint**: Auth and interaction services under 25MB container idle memory.
- [ ] **Multi-LoRA Overhead**: Base model VRAM $+ \sum \text{LoRA buffers} < 85\%$ total GPU VRAM.
- [ ] **Zero-Allocation**: No dynamic memory re-allocations inside vector dot-product inner loops.
- [ ] **Deterministic Teardown**: System includes both single-command bootstrap and complete `$0.00` teardown scripts.
