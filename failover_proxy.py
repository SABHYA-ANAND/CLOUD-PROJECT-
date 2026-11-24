#!/usr/bin/env python3
"""
Hybrid Cloud Failover Load Balancer
Routes incoming requests to the Primary (Private Cluster on port 30081).
If the Private Cluster is unreachable or stopped, seamlessly fails over
to the Standby (Public Cloud on port 30082).
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import sys
import time

PRIMARY_URL = "http://127.0.0.1:30081"
BACKUP_URL = "http://127.0.0.1:30082"
PORT = 8080

class FailoverProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Attempt Primary (Private Cluster)
        target_cluster = "Private Cluster (On-Premises)"
        target_base = PRIMARY_URL
        response_data = None
        status_code = 502
        headers_to_send = {}

        try:
            req = urllib.request.Request(
                PRIMARY_URL + self.path,
                headers={k: v for k, v in self.headers.items() if k.lower() != 'host'},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                status_code = resp.status
                response_data = resp.read()
                headers_to_send = dict(resp.getheaders())
                headers_to_send["X-Active-Cluster"] = "Private Cluster"
        except Exception as primary_err:
            # Primary failed! Trigger Failover to Public Cloud
            target_cluster = "Public Cloud (Failover Active)"
            target_base = BACKUP_URL
            try:
                req = urllib.request.Request(
                    BACKUP_URL + self.path,
                    headers={k: v for k, v in self.headers.items() if k.lower() != 'host'},
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    status_code = resp.status
                    response_data = resp.read()
                    headers_to_send = dict(resp.getheaders())
                    headers_to_send["X-Active-Cluster"] = "Public Cloud"
                    headers_to_send["X-Failover-Notice"] = f"Primary failed ({str(primary_err)[:40]})"
            except Exception as backup_err:
                status_code = 503
                response_data = f'{{"error": "All clusters unreachable: {backup_err}"}}'.encode("utf-8")
                headers_to_send = {"Content-Type": "application/json"}

        # Send response back to client
        self.send_response(status_code)
        for h, v in headers_to_send.items():
            if h.lower() not in ["content-length", "transfer-encoding", "server", "date"]:
                self.send_header(h, v)
        self.send_header("Content-Length", str(len(response_data)))
        self.end_headers()
        self.wfile.write(response_data)

    def do_POST(self):
        # Same logic for POST (e.g. /reset)
        self.do_GET()

    def log_message(self, format, *args):
        # Suppress verbose default logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] Proxy -> {args[0]}\n")

if __name__ == "__main__":
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, FailoverProxyHandler)
    print(f"Hybrid Failover Proxy listening on http://localhost:{PORT}")
    print(f"  - Primary: {PRIMARY_URL} (Private Cluster)")
    print(f"  - Standby: {BACKUP_URL} (Public Cloud)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping proxy.")
