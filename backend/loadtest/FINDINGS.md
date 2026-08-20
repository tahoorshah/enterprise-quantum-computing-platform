# Performance Test Evidence

**Run:** 10 concurrent users (5 authenticated, 5 unauthenticated), 30s, against the live
backend deployed on Kubernetes (Minikube on AWS EC2), reached via `kubectl port-forward`
through the nginx frontend service.

**Tool:** Locust (`backend/loadtest/locustfile.py`). Raw output in this file; reproduce with
the command below for a fresh HTML/CSV report.

## Results (175 total requests, 30s)

| Endpoint | Requests | Failures | Median | 95th %ile | Max |
|---|---|---|---|---|---|
| POST /api/auth/login | 5 | 0 | 680ms | 930ms | 932ms |
| GET /api/dashboard/kpis | 14 | 0 | 5ms | 12ms | 11ms |
| GET /api/dashboard/report | 20 | 0 | 6ms | 290ms | 292ms |
| GET /api/quantum/history | 10 | 0 | 6ms | 16ms | 16ms |
| GET /api/quantum/gates | 6 | 0 | 6ms | 7ms | 7ms |
| POST /api/quantum/execute | 4 | 0 | 11ms | 760ms | 762ms |
| GET /health | 18 | 0 | 5ms | 290ms | 290ms |
| GET /api/dashboard/report [no auth] | 98 | 98 (100%, by design) | - | - | - |

## What this demonstrates
- **0 unexpected failures** across every authenticated/legitimate request path (77 requests,
  0 errors) - the API layer holds up correctly under concurrent load.
- **Authentication enforcement works under load, not just in unit tests**: 98/98 unauthenticated
  requests were correctly rejected with 401 - this is the `UnauthenticatedUser` test class
  working exactly as designed, not a system failure. The 56% "failure rate" Locust reports is
  this intentional negative test, not a defect.
- Most endpoints respond in single-digit milliseconds at the median.

## What this does NOT demonstrate (stated explicitly, not hidden)
- **Not tested at scale.** 10 concurrent users is proof-of-concept scale. No conclusion should
  be drawn about maximum production throughput.
- **Quantum simulation excluded from sustained load.** Only a single small Bell-state circuit
  is exercised per user; QAOA/VQE with COBYLA loops are intentionally excluded from concurrent
  load since they are CPU-bound and would saturate the node rather than measure API performance.
- **Single 30-second run**, not a regression-tracked baseline over time.

## Notable findings
1. **Login latency (median 680ms, up to 932ms)** is the clear outlier against every other
   endpoint (single-digit ms). This is bcrypt's intentional computational cost, not a bug -
   but it is the first bottleneck under concurrent load and should be named as a known,
   understood trade-off (security cost vs latency) in the viva.
2. **A handful of `/health` and `/api/dashboard/report` requests spiked to ~290ms** (visible at
   the 90th-95th percentile) while the median stayed low - likely cold-start/scheduling jitter
   on a resource-constrained Minikube node rather than an application-level issue. Worth
   monitoring rather than treating as resolved.
3. **`/api/quantum/execute` max latency (762ms)** on only 4 requests is too small a sample to
   draw conclusions from - flagged as needing a larger, dedicated run if quantum-endpoint
   performance is examined directly.

## How to reproduce
```bash
cd backend
# ensure kubectl port-forward svc/frontend 8080:80 is running
locust -f loadtest/locustfile.py --host http://localhost:8080 \
    --users 20 --spawn-rate 5 --run-time 2m --headless \
    --html loadtest/report.html --csv loadtest/results
```
