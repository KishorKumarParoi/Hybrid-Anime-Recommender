import pytest
import json
from application import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["app"] == "hybrid-anime-recommender"
    assert "model_loaded" in data


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.content_type
    assert (
        b"anime_rec_http_requests_total" in response.data
        or b"python_gc_objects_collected_total" in response.data
    )


def test_cache_stats_endpoint(client):
    response = client.get("/api/cache/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] in ("active", "disabled")


def test_api_hybrid_endpoint(client):
    response = client.post(
        "/api/hybrid",
        data=json.dumps({"user_id": 11880}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
