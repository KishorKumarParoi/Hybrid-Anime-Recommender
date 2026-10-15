import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, jsonify, Response
from pipeline.prediction_pipeline import hybrid_recommendation
from pipeline.ai_agent_pipeline import get_agent_recommendation
from config.paths_config import MODEL_PATH, USER_WEIGHTS_PATH, ANIME_WEIGHTS_PATH

# Prometheus Metrics Client
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────
# REDIS IN-MEMORY PREDICTION CACHE & TELEMETRY
# ──────────────────────────────────────────────────────────────
REDIS_HOST = os.environ.get("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
redis_client = None

try:
    import redis

    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        socket_timeout=0.5,
        decode_responses=True,
    )
    redis_client.ping()
    logger.info(f"[✓] Connected to Redis Cache at {REDIS_HOST}:{REDIS_PORT}")
except Exception as _e:
    redis_client = None
    logger.info(f"[i] Redis not connected ({_e}) - running in standalone memory mode")

# ──────────────────────────────────────────────────────────────
# PROMETHEUS METRICS DEFINITIONS
# ──────────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "anime_rec_http_requests_total",
    "Total HTTP requests handled by endpoint and HTTP status",
    ["endpoint", "status"],
)
INFERENCE_COUNT = Counter(
    "anime_rec_inference_total",
    "Total AI recommendation inferences executed",
    ["recommender_type"],
)
INFERENCE_LATENCY = Histogram(
    "anime_rec_inference_latency_seconds",
    "Inference execution latency in seconds",
    ["recommender_type"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
MODEL_LOADED_GAUGE = Gauge(
    "anime_rec_model_loaded_status",
    "Model loaded status (1=loaded, 0=not loaded)",
)
CACHE_HIT_COUNTER = Counter(
    "anime_rec_cache_hits_total",
    "Total recommendation cache hits served from Redis",
)


def check_models_present() -> bool:
    return (
        os.path.exists(MODEL_PATH)
        and os.path.exists(USER_WEIGHTS_PATH)
        and os.path.exists(ANIME_WEIGHTS_PATH)
    )


MODEL_LOADED_GAUGE.set(1 if check_models_present() else 0)


# ──────────────────────────────────────────────────────────────
# FLASK WEB UI ROUTES
# ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def home():
    active_tab = "hybrid"
    hybrid_results = None
    agent_results = None
    user_id_val = ""
    query_val = ""
    api_key_val = ""
    error_message = None

    if request.method == "POST":
        action = request.form.get("action", "hybrid")
        active_tab = action

        if action == "hybrid":
            start_time = time.time()
            try:
                user_id_raw = request.form.get("userID", "").strip()
                user_id_val = user_id_raw
                if user_id_raw:
                    user_id = int(user_id_raw)
                    # Check Redis cache first
                    cache_key = f"rec:hybrid:{user_id}"
                    cached_data = None
                    if redis_client:
                        try:
                            cached_data = redis_client.get(cache_key)
                        except Exception:
                            cached_data = None

                    if cached_data:
                        hybrid_results = json.loads(cached_data)
                        CACHE_HIT_COUNTER.inc()
                    else:
                        hybrid_results = hybrid_recommendation(user_id)
                        if redis_client and hybrid_results:
                            try:
                                redis_client.setex(
                                    cache_key, 3600, json.dumps(hybrid_results)
                                )
                            except Exception:
                                pass

                    latency = time.time() - start_time
                    INFERENCE_COUNT.labels(recommender_type="hybrid").inc()
                    INFERENCE_LATENCY.labels(recommender_type="hybrid").observe(latency)
                    REQUEST_COUNT.labels(endpoint="/", status="200").inc()
                else:
                    error_message = "Please enter a valid numeric User ID."
                    REQUEST_COUNT.labels(endpoint="/", status="400").inc()
            except Exception as e:
                error_message = f"Error generating hybrid recommendations: {e}"
                REQUEST_COUNT.labels(endpoint="/", status="500").inc()

        elif action == "agent":
            start_time = time.time()
            try:
                query_val = request.form.get("query", "").strip()
                api_key_val = request.form.get("apiKey", "").strip()
                if query_val:
                    agent_results = get_agent_recommendation(
                        query_val, api_key=api_key_val
                    )
                    latency = time.time() - start_time
                    INFERENCE_COUNT.labels(recommender_type="agent").inc()
                    INFERENCE_LATENCY.labels(recommender_type="agent").observe(latency)
                    REQUEST_COUNT.labels(endpoint="/", status="200").inc()
                else:
                    error_message = "Please enter your anime preferences or a question for the AI Agent."
                    REQUEST_COUNT.labels(endpoint="/", status="400").inc()
            except Exception as e:
                error_message = f"Error in AI Agent: {e}"
                REQUEST_COUNT.labels(endpoint="/", status="500").inc()
    else:
        REQUEST_COUNT.labels(endpoint="/", status="200").inc()

    return render_template(
        "index.html",
        active_tab=active_tab,
        hybrid_results=hybrid_results,
        agent_results=agent_results,
        user_id_val=user_id_val,
        query_val=query_val,
        api_key_val=api_key_val,
        error_message=error_message,
    )


# ──────────────────────────────────────────────────────────────
# REST API ENDPOINTS
# ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    """Kubernetes liveness and readiness probe endpoint."""
    is_loaded = check_models_present()
    MODEL_LOADED_GAUGE.set(1 if is_loaded else 0)
    REQUEST_COUNT.labels(endpoint="/health", status="200").inc()
    from datetime import timezone
    return (
        jsonify(
            {
                "status": "healthy",
                "app": "hybrid-anime-recommender",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_loaded": is_loaded,
                "redis_connected": redis_client is not None,
            }
        ),
        200,
    )


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus telemetry scraping endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Redis cache telemetry stats."""
    if not redis_client:
        return jsonify({"status": "disabled", "message": "Redis not connected"}), 200
    try:
        info = redis_client.info()
        keys_count = redis_client.dbsize()
        return (
            jsonify(
                {
                    "status": "active",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "total_keys": keys_count,
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/hybrid", methods=["POST"])
def api_hybrid():
    start_time = time.time()
    try:
        data = request.get_json(force=True) or {}
        user_id = int(data.get("user_id", 11880))

        cache_key = f"rec:hybrid:{user_id}"
        cached_data = None
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
            except Exception:
                cached_data = None

        if cached_data:
            CACHE_HIT_COUNTER.inc()
            recommendations = json.loads(cached_data)
        else:
            recommendations = hybrid_recommendation(user_id)
            if redis_client and recommendations:
                try:
                    redis_client.setex(cache_key, 3600, json.dumps(recommendations))
                except Exception:
                    pass

        latency = time.time() - start_time
        INFERENCE_COUNT.labels(recommender_type="hybrid").inc()
        INFERENCE_LATENCY.labels(recommender_type="hybrid").observe(latency)
        REQUEST_COUNT.labels(endpoint="/api/hybrid", status="200").inc()

        return jsonify(
            {
                "status": "success",
                "user_id": user_id,
                "recommendations": recommendations,
                "latency_ms": round(latency * 1000, 2),
                "cached": cached_data is not None,
            }
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/api/hybrid", status="400").inc()
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/agent", methods=["POST"])
def api_agent():
    start_time = time.time()
    try:
        data = request.get_json(force=True) or {}
        query = data.get("query", "").strip()
        api_key = data.get("api_key", "").strip() or None
        if not query:
            REQUEST_COUNT.labels(endpoint="/api/agent", status="400").inc()
            return jsonify({"status": "error", "message": "query is required"}), 400

        response = get_agent_recommendation(query, api_key=api_key)
        latency = time.time() - start_time
        INFERENCE_COUNT.labels(recommender_type="agent").inc()
        INFERENCE_LATENCY.labels(recommender_type="agent").observe(latency)
        REQUEST_COUNT.labels(endpoint="/api/agent", status="200").inc()

        return jsonify(
            {
                "status": "success",
                "query": query,
                "response": response,
                "latency_ms": round(latency * 1000, 2),
            }
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/api/agent", status="500").inc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
