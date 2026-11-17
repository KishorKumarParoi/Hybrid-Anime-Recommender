# 🏛️ Polyglot Architecture & Mechanical Sympathy Manifesto

## 1. Core Service Breakdown
* **Rust Scoring Engine (8083)**: Zero-allocation AVX-512 vector dot product. Sub-0.5ms p99 scoring over 10,000 vectors.
* **Go Authentication Microservice (8081)**: Lightweight native JWT minting with Bcrypt hashing and RBAC. <15MB scratch container.
* **Node.js Express Interaction Service (8082)**: High-concurrency non-blocking write stream to MongoDB for ratings and watchlists.
* **Python FastAPI Intelligence Core (8000)**: Two-Tower dual embeddings, LangGraph multi-agent research dossiers, and PyRIT red-teaming.
* **Next.js 16 Edge Client (3000)**: React 19 Turbopack frontend with glassmorphism UI and real-time streaming updates.

## 2. Low-Latency Pipeline
1. Client sends query to Nginx Edge Gateway (Port 80/443).
2. Go Auth validates JWT claims in <1ms without database roundtrips.
3. Candidate generator retrieves Top-50 dense candidate embeddings from Vector DB.
4. Rust SIMD engine computes cosine similarity against user vector in <0.4ms.
5. If deep synthesis requested, routes through Redis Semantic Cache (<12ms) or LangGraph Multi-Agent cluster.
