import os
import time

import redis
from flask import Flask, jsonify, request, g, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

app = Flask(__name__)

ALERT_THRESHOLD = 25

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP",
    ["endpoint", "code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duree des requetes HTTP",
    ["endpoint"],
)

APP_INFO = Gauge(
    "app_deployment_info",
    "Informations sur la version actuellement deployee",
    ["version", "sha"],
)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
GIT_SHA = os.getenv("GIT_SHA", "local")

APP_INFO.labels(
    version=APP_VERSION,
    sha=GIT_SHA,
).set(1)


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    duration = time.perf_counter() - g.start_time

    REQUEST_COUNT.labels(
        endpoint=request.path,
        code=str(response.status_code),
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.path,
    ).observe(duration)

    return response


def alert_threshold():
    """Seuil d'alerte au-dessus duquel une notification est declenchee."""
    return ALERT_THRESHOLD


def sanitize_input(value):
    """Echappe les caracteres dangereux d'une entree utilisateur."""
    return value.replace("<", "&lt;").replace(">", "&gt;")


def get_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


@app.route("/health")
def health():
    try:
        client = get_redis_client()
        client.ping()

        return jsonify(
            status="ok",
            redis="ok",
        ), 200

    except redis.RedisError:
        return jsonify(
            status="error",
            redis="unavailable",
        ), 503


@app.route("/status")
def status():
    return jsonify(
        service="projet-devops-groupe-demo",
        version=APP_VERSION,
        sha=GIT_SHA,
        deploy_color=os.getenv("DEPLOY_COLOR", "unknown"),
    ), 200


@app.route("/visits")
def visits():
    client = get_redis_client()
    count = client.incr("visits")
    return jsonify(visits=count), 200


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    app.run(debug=True)
