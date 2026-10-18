# 🎬 Hybrid Anime Recommender & Conversational AI Agent Platform

A production-grade, state-of-the-art anime recommendation platform that fuses **Deep Collaborative Filtering** (dual-embedding neural network with Keras/TensorFlow), **Content-Based Filtering** (cosine similarity on metadata), and an **Interactive AI Anime Agent** (Retrieval-Augmented Generation using LangChain, ChromaDB, HuggingFace Embeddings, and Groq LLM).

Fully managed with `uv`, tracked with Comet ML, and served via an interactive Flask web application.

---

## 📌 Key Capabilities

### 1. 🔮 Hybrid Profile Recommender (Collaborative + Content)
- **Neural Collaborative Filtering:** Deep user and anime embeddings trained to learn user latent preferences.
- **Content-Based Cosine Similarity:** Mathematical matching over genre vectors, scores, and popularity metrics.
- **Adaptive Cold-Start Guard:** Graceful fallback to trending high-rated catalog titles for new or cold-start users.

### 2. 🤖 Conversational AI Anime Agent (RAG + Semantic Search)
- **Natural Language Understanding:** Query the agent with free-form preferences (e.g., *"dark psychological thriller with intense mind games like Death Note"* or *"wholesome high school romance with comedy"*).
- **Dense Vector Search:** High-dimensional vector search powered by `sentence-transformers` (`all-MiniLM-L6-v2`) and persistent ChromaDB.
- **LLM Synthesis & Fallback:** Uses `ChatGroq` (`llama-3.1-8b-instant`) when an API key is available, with an automatic semantic synthesis fallback if running offline or without an API key.

---

## 🚀 Quickstart with `uv`

### 1. Prerequisites
Ensure `uv` is installed on your system:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Sync Environment & Dependencies
```bash
uv sync
```

---

## ⚙️ Running End-to-End

### 1. Run the Full Dual-Engine Pipeline
Trains the neural recommender, verifies embeddings, indexes the vector store, and evaluates sample queries across both engines:
```bash
uv run python main.py
```

### 2. Start the Interactive Web Application
```bash
uv run python application.py
```
Open [http://localhost:5000](http://localhost:5000) to access the dual-mode web UI:
- **🔮 Hybrid Recommender:** Enter user IDs (e.g., `11880`, `12141`, `12756`) to get personalized ranked suggestions.
- **🤖 Ask AI Anime Agent:** Enter natural language queries or click sample prompt chips to get rich recommendations with plot overviews and match explanations!

### 3. Run the CLI Tester
```bash
uv run python tester.py
```

---

## 🔬 Individual Components

You can execute any individual subsystem on demand:

- **AI Agent Pipeline:**
  ```bash
  uv run python pipeline/ai_agent_pipeline.py
  ```
- **Hybrid Training Pipeline:**
  ```bash
  uv run python pipeline/training_pipeline.py
  ```
- **Data Ingestion:**
  ```bash
  uv run python -m src.data_ingestion
  ```
- **Data Processing:**
  ```bash
  uv run python -m src.data_processing
  ```
- **Model Training:**
  ```bash
  uv run python -m src.model_training
  ```

---

## 🌐 REST API Endpoints

The web application exposes JSON endpoints for programmatic integration:

- **Hybrid Recommendation:**
  ```bash
  curl -X POST http://localhost:5000/api/hybrid \
    -H "Content-Type: application/json" \
    -d '{"user_id": 11880}'
  ```

- **AI Agent Recommendation:**
  ```bash
  curl -X POST http://localhost:5000/api/agent \
    -H "Content-Type: application/json" \
    -d '{"query": "cyberpunk anime with dark themes and great action"}'
  ```

---

## 🌐 Next.js Latest & Polyglot Microservices Architecture

The platform features an enterprise polyglot microservice combo combining **Next.js Latest (v16 Turbopack)**, **React 19**, **Go**, **Express (Node.js)**, **Rust**, and **Python (FastAPI)** with **PostgreSQL** and **MongoDB** storage:

```
+-----------------------------------------------------------------------------------+
|                        NEXT.JS LATEST FRONTEND (PORT 3000)                        |
|                  React 19 • Turbopack Engine • Glassmorphism UI                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                        [ NGINX REVERSE PROXY / PORT 80 ]
                                          |
     +-------------------+----------------+--------------------+--------------------+
     |                   |                                     |                    |
+----+------------+ +----+------------------+ +----------------+-----+ +------------+-----+
| GO AUTH SERVICE | | EXPRESS INTERACTIONS  | | RUST SCORING ENGINE | | PYTHON FASTAPI    |
|   (Port 8081)   | |     (Port 8082)       | |     (Port 8083)     | |   (Port 8000)     |
|-----------------| |-----------------------| |---------------------| |-------------------|
| * Native JWT    | | * Real-time Reviews   | | * SIMD Cosine Dist  | | * LangGraph Agent |
| * Password Hash | | * Ratings & Bookmarks | | * Candidate Ranking | | * Hybrid Models   |
| * RBAC Engine   | | * MongoDB Documents   | | * Sub-ms Latency    | | * Qdrant Vectors  |
+--------+--------+ +----------+------------+ +---------------------+ +---------+---------+
         |                     |                                                |
         +----------+----------+------------------------------------------------+
                    |
+-------------------+--------------------+--------------------+
|               POSTGRESQL               |      MONGODB       |
|    Relational Users & Auth Schema      |  Interaction Docs  |
+----------------------------------------+--------------------+
```

### Microservice Ecosystem
1. **Next.js Latest Frontend (`/frontend`, Port 3000):**
   - High-fidelity dark mode with glassmorphism styling, responsive layouts, and micro-animations.
   - Interactive Sign In (`/signin`) and Sign Up (`/signup`) with RBAC role selection.
   - Live Polyglot Microservices Health Bar monitoring Go, Express, Rust, and Python.
   - Interactive candidate catalog with bookmarking, real-time ratings, and Rust SIMD vector distance calculator.

2. **Go Authentication Service (`services/go-auth-service/`, Port 8081):**
   - Native zero-dependency HMAC-SHA256 JWT issuance and validation.
   - User registration and login with PostgreSQL schema persistence and graceful in-memory fallback.
   - Role-Based Access Control (Viewer, Researcher, Admin).

3. **Express Interaction Service (`services/express-interaction-service/`, Port 8082):**
   - Node.js 22 service managing real-time ratings, reviews, bookmarks, and community analytics.
   - MongoDB document persistence with resilient fallback store.

4. **Rust Scoring Engine (`services/rust-scoring-engine/`, Port 8083):**
   - Sub-millisecond vector similarity calculation using SIMD cosine dot-product kernels.
   - Candidate re-ranking across high-dimensional latent space.

5. **Python FastAPI Intelligence Core (`app/`, Port 8000):**
   - LangGraph multi-agent anime research state machines, semantic vector caching, and neural collaborative filtering.

---

## 🐳 Docker Compose Polyglot Orchestration

To run the entire ecosystem (Next.js, Go, Express, Rust, Python, PostgreSQL, MongoDB, Redis, and Nginx) in unified containers:

```bash
docker-compose up --build
```

Access services:
- **Next.js Application Gateway:** [http://localhost:3000](http://localhost:3000) or [http://localhost](http://localhost) (via Nginx)
- **Go Auth API:** [http://localhost:8081/auth/health](http://localhost:8081/auth/health)
- **Express Interaction API:** [http://localhost:8082/api/v1/interactions/health](http://localhost:8082/api/v1/interactions/health)
- **Rust Scoring API:** [http://localhost:8083/health](http://localhost:8083/health)
- **FastAPI Core:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌿 GitOps Branching Model

The project is governed by a 5-tier enterprise branching architecture:

```
feature/*  ────────>  test  ────────>  dev  ────────>  stage  ────────>  production / main
(Atomic work)      (Unit CI)      (Integration)    (Pre-Prod UAT)        (Live Production)
```

- **`production` / `main`**: Stable, battle-tested production deployments with semantic releases.
- **`stage`**: Pre-production staging environment matching multi-cloud production topologies.
- **`dev`**: Main development integration branch running continuous automated microservice tests.
- **`test`**: Automated test-runner branch for regression and stress test suites.
- **`feature`**: Active feature development branch for modular pull requests.

---

## 📋 Comprehensive System Architecture Document

For a deep-dive technical presentation, system design rationale, and interview talking points, refer to:
👉 **[ARCHITECTURE.md](ARCHITECTURE.md)** (Contains full ASCII topology diagrams, database modeling, and interview scripts).

---

## ✅ Polyglot Test Suites (100% Pass Rate)

| Technology | Suite | Command | Result |
| :--- | :--- | :--- | :--- |
| **Python** | Full Pytest Suite | `uv run pytest tests/ -v` | **61/61 PASSED (100%)** |
| **Go** | Native Go Test | `cd services/go-auth-service && go test -v ./...` | **3/3 PASSED (100%)** |
| **Express** | Node 22 Test Runner | `cd services/express-interaction-service && npm test` | **4/4 PASSED (100%)** |
| **Rust** | Cargo Test | `cd services/rust-scoring-engine && cargo test` | **3/3 PASSED (100%)** |
| **Next.js** | Turbopack Production Build | `cd frontend && npm run build` | **COMPILED (100%)** |

