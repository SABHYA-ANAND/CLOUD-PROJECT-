#!/usr/bin/env python3
"""
Hybrid Cloud Failover Test Demonstration
Tests continuous availability through the hybrid load balancer while
stopping the private cluster to trigger seamless failover to public cloud.
"""

import time
import json
import urllib.request
import urllib.error

PROXY_URL = "http://localhost:8080/?format=json"

def make_request(req_id):
    start = time.time()
    try:
        req = urllib.request.Request(PROXY_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed_ms = round((time.time() - start) * 1000, 1)
            active_cluster = resp.getheader("X-Active-Cluster", "Unknown")
            env_name = data.get("environment", "Unknown")
            hostname = data.get("hostname", "Unknown")
            visitor_count = data.get("visitor_count", -1)
            return {
                "id": req_id,
                "status": "SUCCESS (200 OK)",
                "active_cluster": active_cluster,
                "environment": env_name,
                "pod": hostname,
                "visitor_count": visitor_count,
                "latency_ms": elapsed_ms
            }
    except Exception as e:
        elapsed_ms = round((time.time() - start) * 1000, 1)
        return {
            "id": req_id,
            "status": f"FAILED ({str(e)})",
            "active_cluster": "None",
            "environment": "N/A",
            "pod": "N/A",
            "visitor_count": -1,
            "latency_ms": elapsed_ms
        }

def run_test(num_requests=5, label="Test Phase"):
    print(f"\n--- {label} ---")
    for i in range(1, num_requests + 1):
        res = make_request(i)
        print(f"Req #{res['id']:02d} | Status: {res['status']} | Active: {res['active_cluster']} | Env: {res['environment']} | Latency: {res['latency_ms']}ms")
        time.sleep(0.5)

if __name__ == "__main__":
    run_test(5, "PHASE 1: Normal Operation (Private Cluster Active)")
