#!/usr/bin/env python3
"""
Load Generator and HPA Scaling Monitor
Sends concurrent requests to /cpu-stress to elevate CPU usage and triggers
the Kubernetes Horizontal Pod Autoscaler from min 2 to max 6 replicas.
"""

import sys
import time
import subprocess
import threading
import urllib.request
import urllib.error
import json
from datetime import datetime

stop_event = threading.Event()

def send_load(target_url, worker_id):
    """Worker thread generating continuous requests."""
    success_count = 0
    fail_count = 0
    while not stop_event.is_set():
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": f"LoadTester-{worker_id}"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    success_count += 1
                else:
                    fail_count += 1
        except Exception:
            fail_count += 1
        time.sleep(0.05)

def monitor_hpa(context="kind-private-cluster", duration=90):
    """Monitors HPA status and pod counts in the background."""
    print(f"\n[MONITOR] Starting HPA and Replica count monitoring on context: {context}")
    print(f"{'Time':<10} | {'Replicas':<10} | {'CPU Utilization':<18} | {'Active Pods'}")
    print("-" * 75)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        try:
            # Get HPA info
            hpa_cmd = f"kubectl --context {context} get hpa web-hpa -o json"
            res = subprocess.run(hpa_cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                hpa_data = json.loads(res.stdout)
                current_replicas = hpa_data.get("status", {}).get("currentReplicas", "N/A")
                metrics = hpa_data.get("status", {}).get("currentMetrics", [])
                cpu_util = "Unknown"
                if metrics:
                    for m in metrics:
                        if m.get("type") == "Resource" and m.get("resource", {}).get("name") == "cpu":
                            cpu_util = f"{m.get('resource', {}).get('current', {}).get('averageUtilization', 'N/A')}% / 50%"
            else:
                current_replicas = "N/A"
                cpu_util = "Waiting"

            # Get Pod names
            pod_cmd = f"kubectl --context {context} get pods -l app=visitor-counter-web --no-headers -o custom-columns=NAME:.metadata.name,STATUS:.status.phase"
            pod_res = subprocess.run(pod_cmd, shell=True, capture_output=True, text=True)
            pods = [p.split()[0] for p in pod_res.stdout.strip().split("\n") if p.strip()]
            pod_str = f"{len(pods)} pods: " + ", ".join(pods[:3]) + ("..." if len(pods) > 3 else "")

            print(f"{elapsed:>3}s       | {str(current_replicas):<10} | {cpu_util:<18} | {pod_str}")
        except Exception as e:
            print(f"{elapsed:>3}s       | Error fetching metrics: {e}")
        time.sleep(5)

def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:30081/cpu-stress?duration=0.4"
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    context = sys.argv[4] if len(sys.argv) > 4 else "kind-private-cluster"

    print("=" * 75)
    print("      KUBERNETES HORIZONTAL POD AUTOSCALER (HPA) LOAD TEST")
    print("=" * 75)
    print(f"Target URL:     {target_url}")
    print(f"Concurrency:    {num_threads} worker threads")
    print(f"Load Duration:  {duration} seconds")
    print(f"Cluster:        {context}")
    print("=" * 75)

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_hpa, args=(context, duration + 40), daemon=True)
    monitor_thread.start()

    # Give monitor 5s baseline check
    time.sleep(5)
    print(f"\n[LOAD] Launching {num_threads} threads to generate CPU stress...")
    workers = []
    for i in range(num_threads):
        t = threading.Thread(target=send_load, args=(target_url, i), daemon=True)
        t.start()
        workers.append(t)

    # Let load run for duration
    time.sleep(duration)
    print("\n[LOAD] Stopping load generation threads. Cooling down...")
    stop_event.set()

    # Wait for monitor thread to finish observing cooldown
    monitor_thread.join()
    print("\n[COMPLETE] HPA load test finished.")

if __name__ == "__main__":
    main()
