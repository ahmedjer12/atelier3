import os
import redis
from unittest.mock import patch, MagicMock

from app import alert_threshold, sanitize_input, app


def test_alert_threshold():
    assert alert_threshold() == 25


def test_sanitize_input_escapes_html():
    assert sanitize_input("<script>") == "&lt;script&gt;"


def test_health_endpoint_ok():
    with patch("app.get_redis_client") as mock_get_redis_client:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_get_redis_client.return_value = mock_client

        client = app.test_client()
        response = client.get("/health")

        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"
        assert response.get_json()["redis"] == "ok"


def test_health_endpoint_redis_down():
    with patch("app.get_redis_client") as mock_get_redis_client:
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.RedisError("Redis unavailable")
        mock_get_redis_client.return_value = mock_client

        client = app.test_client()
        response = client.get("/health")

        assert response.status_code == 503
        assert response.get_json()["status"] == "error"
        assert response.get_json()["redis"] == "unavailable"


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/status")

    assert response.status_code == 200
    assert response.get_json()["service"] == "projet-devops-groupe-demo"


def test_metrics_endpoint():
    client = app.test_client()
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"http_requests_total" in response.data
    assert b"http_request_duration_seconds" in response.data
    assert b"app_deployment_info" in response.data


def test_visits_endpoint_with_real_redis():
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    redis_client.delete("visits")

    client = app.test_client()

    response1 = client.get("/visits")
    response2 = client.get("/visits")

    assert response1.status_code == 200
    assert response1.get_json()["visits"] == 1

    assert response2.status_code == 200
    assert response2.get_json()["visits"] == 2

    redis_client.delete("visits")
