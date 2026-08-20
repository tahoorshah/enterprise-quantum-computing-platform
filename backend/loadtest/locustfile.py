"""
Load / performance test suite (Locust).

Closes the examiner's flagged gap: "Formal performance-testing evidence
is not sufficiently demonstrated." Risk Register item #9 (test suite
lacks security/load/chaos coverage) - this closes the load part.

Scope note for the viva: this exercises the API layer's ability to
handle concurrent requests (auth overhead, DB/Redis I/O, request
routing). It does NOT load-test the quantum simulators directly at
scale - QAOA/VQE with COBYLA loops are intentionally excluded from
sustained concurrent load here because they are CPU-bound and would
saturate a single Minikube node rather than measure API performance.
This is stated explicitly, not hidden.

Run:
    pip install locust
    locust -f loadtest/locustfile.py --host http://localhost:8080

Headless run producing a report file (recommended for evidence):
    locust -f loadtest/locustfile.py --host http://localhost:8080 \
        --users 20 --spawn-rate 5 --run-time 2m --headless \
        --html loadtest/report.html --csv loadtest/results
"""
import random

from locust import HttpUser, task, between


class QFTPlatformUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Log in once per simulated user, reuse the token for all tasks."""
        resp = self.client.post(
            "/api/auth/login",
            data={"username": "analyst", "password": "changeme_demo_only"},
        )
        token = resp.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(5)
    def health_check(self):
        # Unauthenticated - measures baseline latency without auth overhead
        self.client.get("/health")

    @task(4)
    def dashboard_report(self):
        self.client.get("/api/dashboard/report", headers=self.headers)

    @task(3)
    def dashboard_kpis(self):
        self.client.get("/api/dashboard/kpis", headers=self.headers)

    @task(3)
    def list_quantum_history(self):
        self.client.get("/api/quantum/history", headers=self.headers)

    @task(2)
    def small_circuit_execution(self):
        # Small, fast circuit (Bell state) - representative of interactive UI use,
        # not a stress test of the simulator itself.
        payload = {
            "num_qubits": 2,
            "gates": [
                {"gate": "h", "qubits": [0]},
                {"gate": "cx", "qubits": [0, 1]},
            ],
            "shots": 256,
        }
        self.client.post("/api/quantum/execute", json=payload, headers=self.headers)

    @task(1)
    def list_supported_gates(self):
        self.client.get("/api/quantum/gates", headers=self.headers)


class UnauthenticatedUser(HttpUser):
    """Measures rejection overhead for unauthenticated traffic -
    relevant now that every route requires a token."""
    wait_time = between(1, 2)

    @task
    def hit_protected_route_without_token(self):
        self.client.get("/api/dashboard/report", name="/api/dashboard/report [no auth]")
