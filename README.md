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

## 📂 Project Architecture

```
Hybrid-Anime-Recommender/
├── artifacts/                  # Generated raw, processed, and model artifacts
│   ├── raw/                    # anime.csv, anime_with_synopsis.csv, animelist.csv
│   ├── processed/              # Feature matrices, encodings, and split datasets
│   ├── weights/                # Extracted user and anime embedding weights
│   ├── model/                  # Trained RecommenderNet (.h5)
│   └── chroma_db/              # Persistent Chroma vector store for AI Agent
├── config/
│   ├── config.yaml             # Model hyperparameters and bucket config
│   └── paths_config.py         # Centralized file and directory paths
├── pipeline/
│   ├── training_pipeline.py    # Training orchestrator (ingestion -> processing -> training)
│   ├── prediction_pipeline.py  # Hybrid recommendation inference logic
│   └── ai_agent_pipeline.py    # AI Agent vector store builder & RAG pipeline
├── src/
│   ├── ai_agent/               # AI Agent subsystem
│   │   ├── data_loader.py      # Combines curated & catalog anime synopsis data
│   │   ├── prompt_template.py  # Expert anime recommender prompt
│   │   ├── vector_store.py     # Chroma & HuggingFace vector index
│   │   └── agent_recommender.py# Groq LLM + semantic retrieval engine
│   ├── base_model.py           # Keras RecommenderNet architecture
│   ├── custom_exception.py     # Detailed traceback exception handler
│   ├── data_ingestion.py       # Multi-tier data downloader with local fallback
│   ├── data_processing.py      # Vectorized preprocessing and encoding
│   ├── logger.py               # Rotating date-stamped file logger
│   └── model_training.py       # Training loop, callbacks, and Comet ML logger
├── static/
│   └── style.css               # Modern glassmorphism UI styling
├── templates/
│   └── index.html              # Dual-tab frontend interface
├── application.py              # Flask web server & REST API
├── main.py                     # Master end-to-end execution script
├── tester.py                   # Quick dual-mode CLI verification script
├── pyproject.toml              # UV / PEP 621 project configuration
└── uv.lock                     # UV deterministic lockfile
```
