import os
import socket
import time
import math
import hashlib
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import redis

app = Flask(__name__)

# Configuration from Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
ENVIRONMENT = os.getenv("ENVIRONMENT", "Local Development")
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "Local")

START_TIME = time.time()
HOSTNAME = socket.gethostname()

def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True
    )

@app.route("/")
def index():
    visitor_count = 0
    redis_status = "Connected"
    error_msg = None
    
    try:
        r = get_redis_client()
        visitor_count = r.incr("visitor_counter")
    except Exception as e:
        redis_status = "Disconnected"
        error_msg = str(e)
        visitor_count = -1

    # Check if client requested JSON
    if request.headers.get("Accept") == "application/json" or request.args.get("format") == "json":
        return jsonify({
            "visitor_count": visitor_count,
            "hostname": HOSTNAME,
            "environment": ENVIRONMENT,
            "cluster_name": CLUSTER_NAME,
            "redis_host": REDIS_HOST,
            "redis_status": redis_status,
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return render_template(
        "index.html",
        visitor_count=visitor_count,
        hostname=HOSTNAME,
        environment=ENVIRONMENT,
        cluster_name=CLUSTER_NAME,
        redis_host=REDIS_HOST,
        redis_status=redis_status,
        error_msg=error_msg,
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

@app.route("/healthz")
def liveness():
    """Liveness probe: verifies the web process is running."""
    return jsonify({
        "status": "healthy",
        "hostname": HOSTNAME,
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }), 200

@app.route("/ready")
def readiness():
    """Readiness probe: verifies Redis connectivity before serving traffic."""
    try:
        r = get_redis_client()
        r.ping()
        return jsonify({
            "status": "ready",
            "redis": "connected",
            "hostname": HOSTNAME
        }), 200
    except Exception as e:
        return jsonify({
            "status": "not ready",
            "redis": "unreachable",
            "error": str(e),
            "hostname": HOSTNAME
        }), 503

@app.route("/cpu-stress")
def cpu_stress():
    """
    Simulates CPU intensive load to demonstrate HPA (Horizontal Pod Autoscaler).
    Accepts 'duration' (seconds) or 'iterations' query parameters.
    """
    duration = float(request.args.get("duration", 0.3))
    # Cap duration to max 5s per request to avoid hanging indefinitely
    duration = min(duration, 5.0)
    
    start = time.time()
    count = 0
    while time.time() - start < duration:
        # Compute SHA-256 hashes in a tight loop to burn CPU
        data = f"load-test-seed-{count}-{time.time()}".encode("utf-8")
        hashlib.sha256(data).hexdigest()
        count += 1

    actual_duration = round(time.time() - start, 4)
    return jsonify({
        "message": "CPU stress completed",
        "hostname": HOSTNAME,
        "iterations": count,
        "duration_seconds": actual_duration
    }), 200

@app.route("/reset", methods=["POST", "GET"])
def reset():
    """Resets the visitor counter."""
    try:
        r = get_redis_client()
        r.set("visitor_counter", 0)
        return jsonify({"message": "Counter reset to 0", "hostname": HOSTNAME}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats")
def api_stats():
    """Returns application runtime statistics."""
    try:
        r = get_redis_client()
        count = r.get("visitor_counter") or 0
        redis_status = "Connected"
    except Exception as e:
        count = -1
        redis_status = f"Disconnected ({str(e)})"

    return jsonify({
        "visitor_count": int(count),
        "hostname": HOSTNAME,
        "environment": ENVIRONMENT,
        "cluster_name": CLUSTER_NAME,
        "redis_host": REDIS_HOST,
        "redis_status": redis_status,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
