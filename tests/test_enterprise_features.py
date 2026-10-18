"""
Unit and Integration Tests for Enterprise Platform Features:
  - MongoDB / Amazon DocumentDB Modeling & CRUD
  - Authentication (JWT, OAuth2, Keycloak OIDC, RBAC)
  - FastAPI Microservices Endpoints (/api/v1/*)
  - LLM Serving (vLLM, RunPod, BentoML)
  - Observability (OpenTelemetry, Langfuse, ClickHouse OLAP)
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from src.database.document_store import (
    AnimeDoc,
    UserInteractionDoc,
    ResearchDossierDoc,
    SecurityAuditDoc,
    DocumentStore,
    get_document_store,
)
from src.security.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    validate_keycloak_token,
    RoleChecker,
    UserPayload,
)
from src.serving.vllm_client import VLLMClient
from src.serving.runpod_handler import runpod_inference_handler
from src.serving.bentoml_service import RecommendationRequest, bento_predict_recommendations
from src.observability.telemetry import trace_span, get_tracer
from src.observability.langfuse_tracer import LangfuseTracer
from src.observability.clickhouse_analytics import ClickHouseAnalytics
from app.main import app

client = TestClient(app)


# ─── 1. DocumentDB / MongoDB Data Modeling & Repository Tests ─────────────────

def test_document_store_anime_crud():
    def _run():
        store = DocumentStore(uri="mongodb://localhost:27017")
        anime = AnimeDoc(
            anime_id="test_9999",
            title="Neon Genesis Evangelion",
            genres=["Mecha", "Psychological", "Sci-Fi"],
            type="TV",
            episodes=26,
            rating=8.5,
            synopsis="In 2015, the world stands on the brink of destruction.",
            tags=["EVA", "Angels", "Shinji"]
        )
        saved = asyncio.run(store.upsert_anime(anime))
        assert saved["anime_id"] == "test_9999"

        fetched = asyncio.run(store.get_anime("test_9999"))
        assert fetched is not None
        assert fetched["title"] == "Neon Genesis Evangelion"
        assert "Mecha" in fetched["genres"]

    _run()


def test_document_store_interactions_and_dossiers():
    def _run():
        store = DocumentStore(uri="mongodb://localhost:27017")

        # User Interaction
        inter = UserInteractionDoc(
            user_id="user_enterprise_1",
            anime_id="5114",
            rating=9.8,
            interaction_type="rating",
            metadata={"source": "fastapi"}
        )
        asyncio.run(store.record_interaction(inter))
        history = asyncio.run(store.get_user_interactions("user_enterprise_1"))
        assert len(history) >= 1
        assert history[0]["anime_id"] == "5114"

        # Research Dossier
        dossier = ResearchDossierDoc(
            dossier_id="dos_enterprise_1",
            topic="Cowboy Bebop Jazz & Noir Themes",
            report="Comprehensive research report on space noir.",
            quality_score=0.95
        )
        asyncio.run(store.save_dossier(dossier))
        fetched_dossier = asyncio.run(store.get_dossier("dos_enterprise_1"))
        assert fetched_dossier is not None
        assert fetched_dossier["quality_score"] == 0.95

    _run()


# ─── 2. Authentication & Authorization (JWT, OAuth2, Keycloak, RBAC) ─────────

def test_password_hashing():
    raw_pass = "SecureP@ssw0rd2026!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_access_and_refresh_tokens():
    payload = {"sub": "alice", "roles": ["researcher"], "email": "alice@anime.ai"}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    decoded_access = decode_token(access_token)
    assert decoded_access["sub"] == "alice"
    assert decoded_access["type"] == "access"
    assert "researcher" in decoded_access["roles"]

    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == "alice"
    assert decoded_refresh["type"] == "refresh"


def test_keycloak_token_validation():
    # Simulate standard Keycloak JWT structure
    fake_keycloak_jwt = create_access_token({
        "preferred_username": "keycloak_john",
        "email": "john@enterprise.com",
        "realm_access": {"roles": ["admin", "viewer"]},
        "iss": "http://localhost:8080/realms/hybrid-anime"
    })
    user = validate_keycloak_token(fake_keycloak_jwt)
    assert user is not None
    assert user.username == "keycloak_john"
    assert "admin" in user.roles
    assert user.auth_provider == "keycloak"


def test_rbac_role_checker():
    admin_user = UserPayload(username="admin_user", roles=["admin"])
    viewer_user = UserPayload(username="viewer_user", roles=["viewer"])

    admin_checker = RoleChecker(["admin"])
    assert admin_checker(admin_user).username == "admin_user"

    with pytest.raises(Exception):
        admin_checker(viewer_user)


# ─── 3. FastAPI Microservices Endpoints (/api/v1/*) ───────────────────────────

def test_fastapi_oauth2_login_and_me():
    # Login as seeded user
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "admin" in tokens["roles"]

    # Access /api/v1/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["username"] == "admin"
    assert "admin" in profile["roles"]

    # Access admin-only endpoint
    admin_resp = client.get("/api/v1/auth/admin-only", headers=headers)
    assert admin_resp.status_code == 200


def test_fastapi_documents_endpoints():
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    headers = {"Authorization": f"Bearer {token}"}

    # Upsert anime
    anime_payload = {
        "anime_id": "8008",
        "title": "Samurai Champloo",
        "genres": ["Action", "Adventure", "Comedy", "Historical"],
        "rating": 8.5
    }
    resp = client.post("/api/v1/documents/anime", json=anime_payload, headers=headers)
    assert resp.status_code == 200

    # Retrieve anime
    get_resp = client.get("/api/v1/documents/anime/8008")
    assert get_resp.status_code == 200
    assert get_resp.json()["anime"]["title"] == "Samurai Champloo"

    # Database health status
    status_resp = client.get("/api/v1/documents/status")
    assert status_resp.status_code == 200


def test_fastapi_streaming_endpoints():
    token = create_access_token({"sub": "user", "roles": ["viewer"]})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": "user_fastapi_10",
        "anime_id": "5114",
        "rating": 9.7,
        "interaction_type": "bookmark"
    }
    resp = client.post("/api/v1/streaming/interaction", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


def test_fastapi_observability_endpoints():
    # Metrics
    resp_metrics = client.get("/api/v1/observability/metrics")
    assert resp_metrics.status_code == 200
    assert resp_metrics.json()["status"] == "success"

    # Traces
    resp_traces = client.get("/api/v1/observability/traces")
    assert resp_traces.status_code == 200
    assert "recent_spans" in resp_traces.json()

    # Serving Engines
    resp_serving = client.get("/api/v1/observability/serving")
    assert resp_serving.status_code == 200
    assert "engines" in resp_serving.json()


# ─── 4. LLM Serving & GPU Inference (vLLM, RunPod, BentoML) ───────────────────

def test_vllm_client_resilience():
    client_vllm = VLLMClient(base_url="http://127.0.0.1:59998/v1")
    health = asyncio.run(client_vllm.check_health())
    assert health["online"] is False

    result = asyncio.run(client_vllm.generate("Top recommendations for dark fantasy anime."))
    assert result["status"] in ("success", "fallback")
    assert "content" in result


def test_runpod_inference_handler():
    job = {
        "id": "job_runpod_test",
        "input": {"prompt": "Analyze Attack on Titan season finale.", "max_tokens": 128}
    }
    response = runpod_inference_handler(job)
    assert response["status"] == "success"
    assert "metrics" in response
    assert response["metrics"]["gpu_device"] == "NVIDIA-A100-SXM4-80GB"


def test_bentoml_recommendation_service():
    req = RecommendationRequest(user_id=11880, top_k=2)
    resp = bento_predict_recommendations(req)
    assert resp.user_id == 11880
    assert len(resp.recommendations) == 2
    assert resp.model_version == "v1.2.0-pytorch"


# ─── 5. Observability (OpenTelemetry, Langfuse, ClickHouse OLAP) ───────────────

def test_opentelemetry_tracing():
    tracer = get_tracer()
    with trace_span("unit_test_trace", {"test_key": "test_val"}) as span:
        span.set_attribute("nested_status", "completed")

    recent = tracer.recent_spans
    assert len(recent) >= 1
    assert any(s["span_name"] == "unit_test_trace" for s in recent)


def test_langfuse_llm_tracking():
    langfuse = LangfuseTracer()
    rec = langfuse.record_generation(
        trace_id="trace_test_123",
        name="writer_agent_generation",
        model="meta-llama/Llama-3.1-70B-Instruct",
        input_prompt="Draft research findings on Steins;Gate.",
        output_completion="Steins;Gate explores the psychological weight of causality.",
        prompt_tokens=45,
        completion_tokens=60,
        latency_ms=350.5
    )
    assert rec["total_tokens"] == 105
    assert rec["estimated_cost_usd"] > 0.0
    assert len(langfuse.get_recent_traces()) >= 1


def test_clickhouse_olap_analytics():
    ch = ClickHouseAnalytics()
    ch.record_recommendation_event(
        user_id=101, recommender_type="hybrid", candidate_count=10, latency_ms=15.2, cached=True
    )
    ch.record_recommendation_event(
        user_id=102, recommender_type="hybrid", candidate_count=10, latency_ms=45.8, cached=False
    )
    summary = ch.get_summary_metrics()
    assert summary["total_events"] == 2
    assert summary["avg_latency_ms"] > 0
    assert summary["p95_latency_ms"] >= 45.8
    assert summary["cache_hit_pct"] == 50.0
