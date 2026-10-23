# 🏛️ Enterprise Polyglot Architecture & System Design Document
## Hybrid Anime AI Intelligence & Polyglot Microservices Platform

> **System Classification:** Production-Grade Polyglot Cloud-Native AI/ML Microservices Platform  
> **Target Audience:** Technical Interviewers, Lead Architects, Staff Engineers, and Engineering Directors  
> **Version:** 2.5.0 (Enterprise Release)

---

## 🧭 System Overview & 7-Stage Architecture Flow

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
| * Password Hash|       | * Watchlists    |       | * Zero-Alloc   |        | * Hybrid RAG (RRF)    |
| * RBAC Engine  |       | * Event Emitter |       | * Sub-ms Lat.  |        | * Enterprise Suite    |
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

### Visual Workflow Blueprints
- **01. System Architecture**: [01_architecture_overview.jpg](images/01_architecture_overview.jpg)
- **02. Hybrid Recommender**: [02_hybrid_recommender_pipeline.jpg](images/02_hybrid_recommender_pipeline.jpg)
- **03. Curation Flywheel**: [03_llmops_curation_flywheel.jpg](images/03_llmops_curation_flywheel.jpg)
- **04. RSLoRA Training**: [04_qlora_rslora_training.jpg](images/04_qlora_rslora_training.jpg)
- **05. Evaluation Gate**: [05_evaluation_gating_cicd.jpg](images/05_evaluation_gating_cicd.jpg)
- **06. Multi-LoRA Serving**: [06_dynamic_multilora_serving.jpg](images/06_dynamic_multilora_serving.jpg)
- **07. Multi-Cloud GitOps**: [07_multicloud_gitops.jpg](images/07_multicloud_gitops.jpg)

---

## 1. Polyglot Microservices Strategy: Mechanical Sympathy

| Microservice | Technology | Port | Rationale & Architectural Constraints |
| :--- | :--- | :--- | :--- |
| **Edge Frontend** | **Next.js 16 + React 19** | 3000 | Zero-waterfall React Server Components, 358ms Turbopack compilation, Glassmorphism UX design system. |
| **Auth & Identity** | **Go 1.24** | 8081 | 4KB Goroutines vs 1MB OS threads, zero-dependency crypto (`crypto/hmac`), static <15MB binary handling 100k+ auth requests/sec. |
| **User Interactions** | **Node.js 22 (Express)** | 8082 | Non-blocking event loop ideal for high-throughput write-heavy interactions (ratings, comments, likes), direct JSON impedance match with MongoDB. |
| **Similarity Scoring** | **Rust 1.82** | 8083 | Zero-cost abstractions, predictable sub-millisecond p99 latency without Garbage Collector stop-the-world pauses, AVX2/NEON SIMD vectorization. |
| **AI & ML Intelligence** | **Python 3.12 (FastAPI)** | 8000 | LangGraph multi-agent orchestration, HuggingFace embeddings, Hybrid RAG, G-Eval harness, Enterprise Governance, Saga & Lakehouse. |

---

## 2. Enterprise AI Platform Suite (`src/enterprise/`)

```
+----------------------------------------------------------------------------------------------------+
|                                 ENTERPRISE AI PLATFORM SUITE                                       |
+----------------------------------------------------------------------------------------------------+
|  1. Prompt & Policy Guardrails    | Reversible PII Filter Vault + Canary & Shannon Entropy Defense  |
|  2. G-Eval Evaluation Harness     | 5-Dimension LLM-as-a-Judge + Token/Cost Attribution Engine     |
|  3. Production Hybrid RAG         | Dense Vector + BM25 Sparse + Reciprocal Rank Fusion (k=60)      |
|  4. Resilience & Event Patterns   | Kafka Event-Driven, CQRS, Saga Orchestrator, Transaction Outbox |
|  5. Scalable Lakehouse Tier       | Medallion Bronze/Silver/Gold on Delta/Iceberg + Freshness SLAs |
|  6. Security & Governance         | KMS Envelope Encryption (AES-256-GCM), Multi-Tenant RLS, Audit  |
+----------------------------------------------------------------------------------------------------+
```

### A. Prompt & Policy Guardrails (`src/enterprise/guardrails.py`)
- **Reversible PII Filter Vault**: Identifies and scrubs sensitive data (email addresses, US/international phone numbers, credit cards, high-entropy API keys `sk-...`, and IPv4 addresses) replacing them with cryptographically unique surrogate UUIDs (`[EMAIL_UUID_...]`). It persists a bi-directional mapping vault allowing secure downstream restoration only for authorized recipients.
- **Canary Token Prompt-Injection Guard**: Injects cryptographically signed canary tokens (`__CANARY_UUID__`) between system instructions and untrusted user input using XML sandwiching (`<user_untrusted_input>...</user_untrusted_input>`). If an LLM completion leaks or exposes the canary token, the prompt injection defense triggers an instant violation alert.
- **Shannon Entropy Anomaly Detector**: Computes character Shannon entropy:
  $$H(X) = -\sum_{i=1}^n P(x_i) \log_2 P(x_i)$$
  detecting automated GCG (Greedy Coordinate Gradient) adversarial suffix injection attacks (entropy threshold $> 4.8$).

### B. G-Eval Style Evaluation Harness (`src/enterprise/eval_harness.py`)
- **LLM-as-a-Judge 5-Dimension Rubrics**:
  1. *Faithfulness* (0.0–1.0): Evaluates whether claims in completion are strictly grounded in provided context.
  2. *Relevancy* (0.0–1.0): Evaluates direct alignment with user query intent.
  3. *Context Recall* (0.0–1.0): Validates that critical source facts are retained.
  4. *Hallucination Score* (0.0–1.0): Penalizes ungrounded or speculative statements.
  5. *Safety & Policy* (0.0–1.0): Enforces compliance against jailbreaks and toxic content.
- **Offline Batch Evaluation Runner**: Runs automated test suites across benchmark datasets (`OfflineEvalDataset`), generating pass/fail decisions (`passed = composite_score >= 0.85`).
- **Real-Time Token & Cost Attribution**: Calculates prompt and completion token expenditures using dynamic model pricing ($0.59/1M prompt, $0.79/1M completion for Llama-3.3-70B), tracking aggregate platform costs down to the micro-cent.

### C. Production Hybrid RAG Service (`src/enterprise/rag_service.py`)
- **Dense + Sparse Hybrid Search**:
  - *Dense Semantic Retrieval*: Normalized vector cosine similarity against domain embeddings.
  - *Sparse Lexical Retrieval*: BM25 keyword matching with term frequency-inverse document frequency weighting.
- **Reciprocal Rank Fusion (RRF)**:
  $$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{k + \text{rank}_m(d)} \quad (k = 60)$$
- **A/B Testing Deterministic Router**: Deterministically assigns queries to variant branches (`A: baseline_rag` vs `B: hybrid_rrf_cross_encoder`) using SHA-256 modulo hashing on query/user ID, guaranteeing reproducible user experiences.

### D. Distributed Systems & Transactional Patterns (`src/enterprise/patterns.py`)
- **Idempotency Manager**: Atomically registers request keys with configured TTLs, preventing duplicate processing of financial, rating, or model deployment requests.
- **Transactional Outbox (Exactly-Once Semantics)**: Saves domain mutations and Kafka events within a single atomic database transaction. An asynchronous background poller publishes records to Kafka topics (`anime.interactions.v1`, `anime.research.v1`, `security.audit.v1`) and marks them delivered only upon ACK receipt, eliminating dual-write race conditions.
- **Saga Orchestrator with Compensating Rollbacks**: Coordinates multi-step distributed workflows (e.g., automated model deployment: Validate Weights $\to$ Allocate GPU VRAM $\to$ Register Model $\to$ Switch Traffic). If any intermediate step fails, it executes compensating actions in reverse order (`LIFO`), guaranteeing system consistency.

### E. Scalable Lakehouse Architecture (`src/enterprise/lakehouse.py`)
- **Medallion Data Architecture**:
  - *Bronze*: Append-only raw ingestion log capturing telemetry events.
  - *Silver*: Deduplicated, validated, PII-scrubbed records with strict schema enforcement.
  - *Gold*: Aggregated analytical feature store and training-ready datasets for continuous QLoRA/RSLoRA tuning.
- **Feature Freshness SLA Monitor**: Tracks event ingestion timestamps against defined SLAs ($< 5\text{ min}$ for real-time recommendations, $< 1\text{ hr}$ for batch catalog embeddings), alerting on data staleness.

### F. Security, Governance & Audit (`src/enterprise/security.py`)
- **Tenant Security Context (Row-Level Security)**: Enforces strict logical data isolation by injecting tenant IDs into query predicates (`WHERE tenant_id = :current_tenant`), preventing cross-tenant data leakage.
- **KMS Envelope Encryption**: Implements AES-256-GCM envelope encryption. Data is encrypted using single-use symmetric Data Encryption Keys (DEKs), which are in turn encrypted under a root Key Encryption Key (KEK) managed by AWS KMS or HashiCorp Vault.
- **Tamper-Evident Audit Trail**: Every sensitive administrative and security operation is recorded in a cryptographically chained audit log using HMAC-SHA256, where each record incorporates the hash of the preceding block (`prev_hash`), making post-hoc tampering computationally detectable.

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

### C. Enterprise RAG Query Lifecycle
```
User Query: "Find cyberpunk anime with deep philosophical undertones"
   |
   v
[Input Guardrail: PII Filter & Prompt Injection Scanner]
   ├── Check 1: PII Scrubbing -> Reversible surrogate tokens in vault
   ├── Check 2: Canary token injection with XML boundary delimiter
   └── Check 3: Shannon Entropy scan (Threshold: 4.8) -> Safe
   |
   v
[A/B Test Traffic Router]
   ├── Variant A: Baseline Dense Vector Search
   └── Variant B: Hybrid Dense + Sparse BM25 + Reciprocal Rank Fusion (k=60)
   |
   v
[Cross-Encoder Reranker & Context Assembly]
   |
   v
[LLM Inference (vLLM / Groq) with Dynamic Multi-LoRA Persona Header]
   |
   v
[Output Guardrail: PII De-Anonymization & G-Eval Faithfulness Check]
   |
   v
[Transactional Outbox: Log Query & Stream Event to Kafka `anime.research.v1`]
   |
   v
[Client Response: Rendered Markdown + Cost Attribution Dashboard Metrics]
```

---

## 4. Multi-Database Data Architecture

### 1. PostgreSQL (Relational & Identity Store)
- Enforces strict ACID compliance, relational schemas, foreign keys, and RBAC roles for users and credentials.
- Schema:
  - `users`: `(id UUID, email VARCHAR UNIQUE, password_hash VARCHAR, role VARCHAR, created_at TIMESTAMP)`
  - `anime_catalog`: `(anime_id INT PRIMARY KEY, title VARCHAR, score NUMERIC, episodes INT, year INT)`
  - `outbox_events`: `(id UUID, aggregate_type VARCHAR, payload JSONB, status VARCHAR, created_at TIMESTAMP)`

### 2. MongoDB (Document & Unstructured Intelligence Store)
- Agility and schema flexibility for deeply nested LLM research dossiers, user reviews, and unstructured JSON event payloads.
- Collections:
  - `interactions`: `{ _id, anime_id, user_id, action, rating, timestamp }`
  - `research_dossiers`: `{ _id, topic, confidence_score, executive_summary, agent_steps: [], created_at }`

### 3. Redis (Sub-Millisecond In-Memory Tier)
- Keyspaces:
  - `cache:recs:<user_id>`: Precomputed candidate ranking lists (TTL: 300s).
  - `cache:semantic:<hash>`: Embedding semantic cache for repetitive agent queries (TTL: 24h).
  - `rate:limit:<ip>`: Token bucket rate limiter counters.

### 4. Apache Kafka (Real-Time Event Streaming)
- Topics:
  - `anime.interactions.v1`: Real-time user clickstream and rating events.
  - `anime.research.v1`: Agent research dossiers broadcast to analytics consumers.
  - `security.audit.v1`: AI safety violations and PyRIT red-teaming alerts.

---

## 5. One-Click Zero-Friction Cloud Deployment

The entire architecture is deployable with a single bash command on any local workstation (macOS / Linux) or fresh cloud VM (AWS EC2, Google Cloud Compute Engine, Azure VM):

```bash
# 1. Clone repository
git clone https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender.git
cd Hybrid-Anime-Recommender

# 2. Single-command deployment (Zero manual configuration needed)
./deploy.sh
```

### What `./deploy.sh` Automates:
1. **Host Topology & IP Auto-Discovery**: Probes AWS IMDSv2/IMDSv1 or external resolvers to detect public IP.
2. **Automated Toolchain Bootstrap**: Installs Docker, Docker Compose, `uv`, and Python 3.12 idempotently.
3. **macOS Daemon Auto-Start**: Detects if Docker Desktop is closed and starts it automatically.
4. **Port Conflict Auto-Remapper**: Checks for host port collisions (e.g., existing Postgres on 5432 or Uvicorn on 8000) and maps external ports to free bindings without breaking internal container networking.
5. **Polyglot Mesh Orchestration**: Builds and launches all 9 containerized services.
6. **Automated Health Probes**: Validates every service endpoint before routing traffic.
7. **Continuous LLMOps Verification**: Executes end-to-end data curation, RSLoRA training, quality gating, and dynamic multi-LoRA serving verification.

### Teardown to Zero Cost ($0.00/hr):
```bash
./clear.sh
```
Stops all containers, purges networks and volumes, frees all ports, and kills background processes, ensuring zero lingering costs.
