# 🏛️ Enterprise Polyglot Architecture & System Design Document
## Hybrid Anime AI Intelligence & Polyglot Microservices Platform

> **System Classification:** Production-Grade Polyglot Cloud-Native AI/ML Microservices Platform  
> **Target Audience:** Technical Interviewers, Lead Architects, Staff Engineers, and Engineering Directors  
> **Version:** 2.0.0 (Production Release)

---

## 1. Executive Summary

The **Hybrid Anime Intelligence Platform** is a globally distributed, resilient recommendation and generative AI research platform. Rather than relying on a monolithic backend, the platform leverages a **Polyglot Microservice Mesh** where each service is implemented in the language best suited for its operational constraints:

```
+----------------------------------------------------------------------------------------------------+
|                                      GLOBAL CLIENT TIER                                            |
|                  Next.js Latest (v16 Turbopack) • React 19 • Glassmorphism UI                      |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                     [ NGINX EDGE REVERSE PROXY ]
                            Rate Limiting (20r/s) • TLS 1.3 • Security Headers
                                                   |
        +-------------------------+----------------+-------------------------+
        |                         |                                          |
+-------+--------+       +--------+--------+       +----------------+        +-----------------------+
|  GO AUTH SVC   |       |  NODE.JS EXPR.  |       |  RUST SCORING  |        |  PYTHON FASTAPI CORE  |
|  (Port 8081)   |       |   (Port 8082)   |       |  (Port 8083)   |        |      (Port 8000)      |
|----------------|       |-----------------|       |----------------|        |-----------------------|
| * Native JWT   |       | * Reviews/Likes |       | * SIMD Dot Prod|        | * LangGraph Agents    |
| * Password Hash|       | * Watchlists    |       | * Zero-Alloc   |        | * Dual-Embedding Recs |
| * RBAC Engine  |       | * Event Emitter |       | * Sub-ms Lat.  |        | * PyRIT AI Red Team   |
+-------+--------+       +--------+--------+       +--------+-------+        +-----------+-----------+
        |                         |                         |                            |
        +------------+------------+                         |                            |
                     |                                      |                            |
        +------------+------------+                         |               +------------+-----------+
        |                         |                         |               |                        |
+-------+--------+       +--------+--------+                |        +------+-------+        +-------+-------+
|   POSTGRESQL   |       |     MONGODB     |                |        |  REDIS CACHE |        |  APACHE KAFKA |
| Relational DB  |       |  Document Store |                |        |  Port 6379   |        |  Port 9092    |
| Users & Auth   |       |  Reviews & Logs |                |        | Hot Recs/LTM |        | Event Bus     |
+----------------+       +-----------------+                |        +--------------+        +---------------+
                                                            |
                                        +-------------------+-------------------+
                                        |          VECTOR STORAGE TIER          |
                                        |    ChromaDB & Qdrant Dense Indices    |
                                        +---------------------------------------+
```

---

## 2. Polyglot Microservices Strategy: Language Rationale

| Microservice | Technology | Rationale & Mechanical Sympathy |
| :--- | :--- | :--- |
| **Edge Frontend** | **Next.js 16 + React 19** | Zero-waterfall Server Components, sub-second Turbopack compilation (358ms), edge route pre-rendering, modern glassmorphism UX. |
| **Auth & Identity** | **Go 1.27** | Concurrency via lightweight Goroutines (4KB stack vs 1MB thread), native zero-dependency crypto (`crypto/hmac`), static zero-overhead binary (<15MB container). |
| **User Interactions** | **Node.js 22 (Express)** | Non-blocking event loop ideal for high-throughput write-heavy interactions (ratings, comments, likes), native JSON impedance match with MongoDB. |
| **Similarity Scoring** | **Rust 1.99** | Zero-cost abstractions, predictable sub-millisecond p99 latency without Garbage Collector stop-the-world pauses, compiler SIMD vectorization. |
| **AI & ML Intelligence** | **Python 3.12 (FastAPI)** | State-of-the-art ML/AI ecosystem: LangGraph multi-agent orchestration, HuggingFace embeddings, PyRIT red-teaming, TensorFlow dual-embeddings. |

---

## 3. End-to-End Request Lifecycles & Data Flow

### A. Authentication & Zero-Trust Token Flow
```
User Client                Nginx (Port 80)           Go Auth (Port 8081)           Postgres / Fallback
   |                              |                          |                             |
   |--- 1. POST /api/auth/signin->|--- Route /auth/signin -->|                             |
   |                              |                          |--- 2. Fetch User Record --->|
   |                              |                          |<-- Hash Verification -------|
   |                              |                          |                             |
   |                              |                          |--- 3. Mint HS256 JWT -------+
   |                              |                          |   (email, role, exp: 24h)   |
   |                              |<-- 200 OK + JWT Token ---|                             |
   |<-- Return JWT + Claims ------|                          |                             |
```

### B. Sub-Millisecond Recommendation & Vector Scoring Flow
```
User Client               Next.js Edge               Rust Engine (8083)           Python FastAPI (8000)
   |                           |                             |                              |
   |--- 1. Request Recs ------>|                             |                              |
   |                           |--- 2. Fetch Candidates ----------------------------------->|
   |                           |                                                            | (Dual-Embedding)
   |                           |<-- 50 Top Candidate Vectors -------------------------------|
   |                           |                             |                              |
   |                           |--- 3. POST /batch-sim ----->|                              |
   |                           |   (user_vec + 50 candidates)|                              |
   |                           |                             | (SIMD Cosine Dot Product)    |
   |                           |<-- Ranked Array (sub-1ms) --|                              |
   |<-- Render Ranked Grid ----|
```

### C. Autonomous LangGraph Research Dossier Flow
```
User Query: "Dark time-travel anime like Steins;Gate"
   |
   v
[NeMo / Guardrails Layer] ---------> Block Prompt Injection? ---> (If Yes: Return 400 Safe Violation)
   | (Safe)
   v
[Semantic Cache (Redis)] ----------> Cache Hit? -----------------> (If Yes: Return Cached Dossier in 4ms)
   | (Cache Miss)
   v
[LangGraph Multi-Agent Orchestrator]
   ├── Node 1: Decompose Query (Entities: "Steins;Gate", "Time-Travel", "Sci-Fi", "Dark")
   ├── Node 2: Dense Vector Retrieval (Qdrant / ChromaDB dense embeddings)
   ├── Node 3: LLM Synthesis Agent (ChatGroq / Llama-3.1-8b / TensorZero Gateway)
   └── Node 4: Hallucination & Factuality Self-Correction Reflection Loop
   |
   v
[Storage & Stream] ────────────────> Store in MongoDB & Publish to Kafka topic: anime.research.v1
   |
   v
[Client Response] ─────────────────> Render Live Markdown Dossier with Confidence Metrics
```

---

## 4. Multi-Database Data Architecture

### 1. PostgreSQL (Relational & Identity Store)
* **Tables**:
  * `users`: `(id UUID, email VARCHAR UNIQUE, password_hash VARCHAR, role VARCHAR, created_at TIMESTAMP)`
  * `anime_catalog`: `(anime_id INT PRIMARY KEY, title VARCHAR, score NUMERIC, episodes INT, year INT)`
* **ACID Guarantees**: Enforces referential integrity, unique constraints, and RBAC roles.

### 2. MongoDB (Document & Unstructured Intelligence Store)
* **Collections**:
  * `interactions`: `{ _id, anime_id, user_id, action: "like"|"bookmark"|"rating", rating: 9.5, timestamp }`
  * `research_dossiers`: `{ _id, topic, confidence_score, executive_summary, agent_steps: [], created_at }`
* **Scalability**: Shardable by `user_id` or `topic` for linear write scalability.

### 3. Redis (Sub-Millisecond In-Memory Tier)
* **Keyspaces**:
  * `cache:recs:<user_id>`: Precomputed candidate ranking lists (TTL: 1 hour).
  * `cache:semantic:<hash>`: Embedding semantic cache for repetitive agent queries (TTL: 24 hours).
  * `rate:limit:<ip>`: Token bucket rate limiter counters.

### 4. Apache Kafka (Real-Time Event Streaming)
* **Topics**:
  * `anime.interactions.v1`: Real-time user clickstream and rating events.
  * `anime.research.v1`: Agent research dossiers broadcast to analytics consumers.
  * `security.audit.v1`: AI safety violations and PyRIT red-teaming alerts.

---

## 5. Security Architecture & AI Red-Teaming (PyRIT)

```
+------------------------------------------------------------------------------------+
|                         ENTERPRISE AI DEFENSE IN DEPTH                             |
+------------------------------------------------------------------------------------+
| 1. Network Edge      | Nginx rate limiting (20 req/s), TLS 1.3, strict CSP headers |
| 2. Identity Tier     | Zero-trust JWT tokens (HS256/RS256), Keycloak SSO, RBAC     |
| 3. Input Guardrails  | Regex + Semantic embedding filter blocking jailbreak tokens |
| 4. Red Teaming Engine| PyRIT (Python Risk Identification Toolkit) fuzzing engine   |
| 5. Output Sanitizer  | PII anonymization mask (regex redaction of emails, API keys)|
+------------------------------------------------------------------------------------+
```

---

## 6. GitOps Branching Model

The project adheres to a 5-tier enterprise GitOps workflow:

```
feature/*  ────────>  test  ────────>  dev  ────────>  stage  ────────>  production / main
(Local work)       (Unit CI)      (Integration)    (Pre-Prod UAT)        (Live Production)
```

1. **`feature/*`**: Individual developer branches for atomic features or bug fixes.
2. **`test`**: Automated scratch test runner and experimental validation branch.
3. **`dev`**: Active integration branch where all microservices are assembled and tested via Docker Compose.
4. **`stage`**: Pre-production staging environment mirrored to cloud staging clusters.
5. **`production` / `main`**: Production-ready code released with automated semantic tags and Docker container images.

---

## 7. Interview Presentation Guide (How to Pitch This Project)

### A. The 2-Minute Elevator Pitch
> *"I built an enterprise-grade Hybrid Anime Recommendation and AI Research platform utilizing a polyglot microservices architecture. Instead of putting everything in a single Python container, I decoupled the workloads by mechanical sympathy:*
> - *A **Next.js 16 (React 19)** frontend with sub-second Turbopack compilation and glassmorphism UI.*
> - *A **Go** service handling authentication and JWT issuance with zero runtime dependencies and sub-millisecond response times.*
> - *A **Node.js Express** service handling high-throughput asynchronous user interactions and reviews.*
> - *A **Rust** scoring engine executing SIMD-accelerated vector cosine distance computations with zero garbage-collection latency.*
> - *A **Python FastAPI** core orchestrating LangGraph multi-agent research and TensorFlow dual-embedding models.*
> *The system persists to **PostgreSQL** and **MongoDB**, streams real-time events via **Apache Kafka**, enforces AI safety via **PyRIT red-teaming**, and is deployed via **Docker Compose** and **Terraform** across AWS, GCP, and Azure."*

### B. Key Technical Questions You Can Confidently Answer

1. **"Why use Rust for scoring instead of doing it in Python with NumPy?"**
   * *Answer:* *"While NumPy uses C/BLAS under the hood, calling Python for high-frequency individual or micro-batch requests incurs Python interpreter overhead, GIL contention, and garbage collection pauses. Our Rust scoring engine runs as a dedicated daemon on port 8083, compiling with native CPU SIMD instructions (`-C target-cpu=native`), allocating zero heap memory per request, and guaranteeing deterministic sub-millisecond p99 latency without GC jitter."*

2. **"Why have both PostgreSQL and MongoDB?"**
   * *Answer:* *"Polyglot persistence solves two fundamentally different data models: PostgreSQL enforces strict ACID compliance, relational schemas, foreign keys, and RBAC roles for users and credentials. MongoDB provides an agile, schema-less document structure for deeply nested, variable-length LLM research dossiers, user reviews, and unstructured JSON event payloads."*

3. **"How does the system handle an outage of external databases?"**
   * *Answer:* *"Every microservice in our platform implements an **Offline Resilience Fallback pattern**. If PostgreSQL or MongoDB is unreachable, the services transparently fall back to thread-safe in-memory maps (`sync.RWMutex` in Go, in-memory structures in Node.js and Python), allowing health probes and core read/write interactions to remain responsive without crashing the client tier."*

---

## 8. Continuous Fine-Tuning & Dynamic Multi-LoRA Serving Tier

```
+------------------------------------------------------------------------------------+
|                      CONTINUOUS LLMOPS & MULTI-LORA LIFECYCLE                      |
+------------------------------------------------------------------------------------+
| 1. Ingestion Flywheel | Kafka Telemetry -> PII Scrubbing -> 15% General Replay Buffer|
| 2. Parameter Tuning   | QLoRA (4-bit NF4) + RSLoRA (alpha/sqrt(r)) + NeFTune Noise |
| 3. Loss Masking       | Completion-Only Token Masking (-100 for prompt tokens)     |
| 4. Quality Gating     | 4-Dimension Rubric (Domain, JSON, Reasoning, Retention >=0.85) |
| 5. In-Flight Serving  | vLLM Dynamic Multi-LoRA on single GPU (< 1ms swap latency)  |
+------------------------------------------------------------------------------------+
```

### Visual Workflow Blueprints
- **System Architecture**: `docs/images/01_architecture_overview.jpg`
- **Recommender Engine**: `docs/images/02_hybrid_recommender_pipeline.jpg`
- **Curation Flywheel**: `docs/images/03_llmops_curation_flywheel.jpg`
- **RSLoRA Tuning**: `docs/images/04_qlora_rslora_training.jpg`
- **Quality Gating**: `docs/images/05_evaluation_gating_cicd.jpg`
- **Multi-LoRA GPU Serving**: `docs/images/06_dynamic_multilora_serving.jpg`
- **Multi-Cloud GitOps**: `docs/images/07_multicloud_gitops.jpg`

---

## 9. Multi-Cloud GPU Serving Matrix & Memory Allocation

| Resource Dimension | Azure AKS (NC4as_T4_v3) | GCP GKE (g2-standard-4) | AWS EKS (g4dn.xlarge / g5) |
| :--- | :--- | :--- | :--- |
| **Physical GPU** | NVIDIA T4 (16GB VRAM) | NVIDIA L4 (24GB VRAM) | NVIDIA T4 / A10G (16–24GB) |
| **Compute Capability** | Turing (SM 7.5) | Ada Lovelace (SM 8.9) | Turing / Ampere |
| **Quantization Kernel** | AWQ Classic (FP16) | AWQ Marlin (BF16) | AWQ Classic (FP16) |
| **Base Weights (4-bit)**| 5.6 GB VRAM | 5.6 GB VRAM | 5.6 GB VRAM |
| **LoRA Adapters (x2)** | 150 MB VRAM | 150 MB VRAM | 150 MB VRAM |
| **KV Cache Headroom** | ~8.8 GB VRAM | ~16.7 GB VRAM | ~8.8–16.0 GB VRAM |
| **Max Context / Concurrency** | 4,096 tokens / 8 seqs | 8,192 tokens / 16 seqs | 4,096 tokens / 8 seqs |
| **Monthly Compute Cost** | ~$380 / month | ~$410 / month | ~$390 / month |

