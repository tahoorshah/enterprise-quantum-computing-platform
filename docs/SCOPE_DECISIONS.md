# Scope Decisions and Engineering Trade-offs

**Project:** Enterprise Quantum Computing Platform — QFT Bank
**Student:** Syed Muhammad Tahoor Ali
**Diploma:** EduQual Level 6, Diploma in Artificial Intelligence Operations (ANPP-OP)

---

## 1. Purpose of This Document

Section 6 of the project specification lists an approved open-source technology
stack. Not every listed technology was implemented. This document records which
were not, why, what was implemented instead, and what a production deployment
would do differently.

These are engineering decisions made against real constraints, not omissions.
Each is stated plainly, including the one item that remains partially
unresolved, because an accurate account of what does and does not work is more
useful than a claim of total coverage.

---

## 2. The Constraint That Drives Most of These Decisions

The entire platform is developed and demonstrated on a single laptop:

| Resource | Capacity |
|---|---|
| Total system memory | 15 GiB |
| Available with cluster stopped | ~11 GiB |
| Consumed with full cluster running | ~7.6–8.4 GiB |
| Remaining headroom during demonstration | ~7 GiB |

The cluster is single-node Minikube running eight workloads (PostgreSQL,
Redis, backend, frontend, Prometheus, Grafana, Loki, Promtail). The
demonstration itself must also run a browser, a code editor, and screen
sharing.

This budget is why the heaviest candidates were excluded. A platform that
crashes during the live demonstration scores nothing, regardless of what is
installed on it.

---

## 3. Items Not Implemented

### 3.1 Keycloak — Identity and Access Management

**What it provides:** centralised authentication and authorisation via OIDC/SAML,
with user federation, role mapping, and single sign-on.

**Why not built:** approximately 700 MiB resident, plus a dedicated database and
realm/client configuration. More significantly, no deliverable in Section 4 or
Section 10 requires authenticated multi-user access. The platform is
specified as a proof-of-concept for a single analyst evaluating quantum
methods, not a multi-tenant production service. Adding an identity layer
would demonstrate Keycloak configuration, not quantum computing competency,
which Section 2 of the specification identifies as the primary assessment
domain.

**What exists instead:** the platform has a single entry point — the frontend
NodePort. The backend, database, and cache are ClusterIP-only and
unreachable from outside the cluster. This is network-level access control:
a reduced attack surface by design rather than by authentication.

**Production approach:** Keycloak or a managed identity provider (Entra ID,
Okta) issuing OIDC tokens, validated by FastAPI middleware, with role-based
authorisation distinguishing analysts (who run simulations) from executives
(who read dashboards only).

---

### 3.2 OpenTelemetry — Distributed Tracing

**What it provides:** vendor-neutral instrumentation emitting traces, metrics,
and logs, showing how a single request propagates across service boundaries.

**Why not built:** a functioning tracing stack requires an OpenTelemetry
Collector plus a trace backend (Jaeger or Tempo) — two further pods on an
already-constrained node. The deeper reason is architectural: distributed
tracing earns its cost when a request crosses many services and the latency
source is unclear. This platform has one application service. A trace would
show a single span, restating what Prometheus already reports.

**What exists instead:** Prometheus scrapes application metrics, including
per-endpoint request counts and latencies, visualised in Grafana. For a
single-service architecture this answers the same questions.

**Production approach:** as the platform decomposes into separate services —
circuit execution, optimisation, PQC assessment — tracing becomes necessary
to attribute latency correctly. OpenTelemetry auto-instrumentation on FastAPI
exporting to Tempo, correlated with existing Loki logs by trace ID.

---

### 3.3 Wazuh — Security Information and Event Management

**What it provides:** host intrusion detection, file integrity monitoring, log
analysis, and compliance reporting across a fleet.

**Why not built:** this is the single heaviest item in the approved stack. A
minimal Wazuh deployment — manager, indexer, and dashboard — requires
4 GiB or more, with the indexer (an OpenSearch derivative) dominating.
Against roughly 7 GiB of headroom during demonstration, this represents an
unacceptable risk of memory pressure and pod eviction at the exact moment the
platform must be shown working.

Wazuh is also designed to monitor a fleet of hosts over time. Its value
emerges from baselines and anomaly detection across many machines, neither of
which a single-node development cluster can meaningfully provide.

**What exists instead:** the security function is addressed at build time
rather than runtime, through three scanning layers in the CI/CD pipeline:
Bandit for static analysis of Python source, pip-audit for known CVEs in
dependencies, and Trivy for vulnerabilities in the built container image.
This is detection shifted left — vulnerabilities are found before deployment
rather than after intrusion.

**Production approach:** Wazuh or a managed SIEM deployed on dedicated
infrastructure, ingesting Kubernetes audit logs, container runtime events,
and application logs, with alerting mapped to NIST CSF 2.0 Detect functions.

---

### 3.4 GitLab Community Edition

**What it provides:** an integrated DevOps platform combining Git hosting,
issue tracking, a container registry, and CI/CD.

**Why not built:** Section 6 lists Jenkins and GitLab CE together under a single
heading, "Continuous Integration and Continuous Deployment" — two options
within one capability, not two independent requirements. That capability is
implemented in full: an eight-stage Jenkins DevSecOps pipeline comprising
checkout, backend build and test, static analysis, dependency scanning,
frontend build, policy-as-code enforcement, image build, and container
scanning.

GitLab CE would duplicate two capabilities already satisfied. Version control
is on GitHub, which Section 6 and Section 10 both mandate. CI/CD is Jenkins.
GitLab CE additionally requires 4 GiB or more before Runners are considered.

Implementing one tool per capability thoroughly is a sounder engineering
decision than operating two overlapping platforms shallowly.

**Production approach:** a single platform chosen deliberately. If an
organisation standardises on GitLab, the pipeline stages port directly to
`.gitlab-ci.yml`; the stage logic is platform-independent.

---

### 3.5 Open Policy Agent — Implemented, With a Deliberate Architectural Choice

OPA **is** implemented, but at a specific point in the lifecycle, and the
reasoning matters.

**What was built:** a Rego policy (`infra/policy/kubernetes.rego`) evaluated by
Conftest as a Jenkins pipeline stage. It validates every Kubernetes manifest
before any image is built.

**Why at CI time rather than as an admission controller:** OPA can also run
in-cluster as a Gatekeeper admission webhook, rejecting non-compliant
resources at apply time. That is runtime enforcement. The CI-time approach is
shift-left enforcement: violations are caught at commit, in seconds, before a
multi-minute image build, and before anything reaches the cluster at all.
Gatekeeper additionally requires a controller deployment and CRDs, adding
resident cost to the node.

For a single-operator platform where all changes flow through the pipeline,
CI-time enforcement covers the same failure modes at lower cost. In a
multi-team cluster where operators can apply manifests directly, an admission
controller becomes necessary because the pipeline is no longer the only path
to the cluster.

**Evidence the policy is functional rather than decorative:** on first
execution it identified a genuine defect — the frontend Deployment declared a
readiness probe but no liveness probe. Readiness only removes an unhealthy
pod from service; liveness restarts it. Given that this same container had
previously suffered a startup crash-loop, the omission was material. It was
fixed rather than exempted.

The policy distinguishes two severities deliberately. `deny` rules describe
conditions the manifests satisfy, so any failure indicates a real regression
and blocks the build. `warn` rules record accepted trade-offs, keeping them
visible in every build log rather than forgotten.

---

## 4. Known Limitation: Promtail Log Shipping

This section records something that does not fully work.

**Working:** Loki is deployed and operational. Its logs confirm successful
startup with all internal modules active. It is registered as a second
datasource in Grafana alongside Prometheus and is queryable.

**Not working:** Promtail, the log-shipping agent, is deployed and running as a
DaemonSet but is not discovering log targets. The metric
`promtail_targets_active_total` remains at zero.

**Diagnostics performed, all confirming correct configuration:**

- RBAC verified directly — the service account can list pods
- Configuration syntax validated
- The `__path__` pattern corrected to match Minikube's actual on-disk layout
  (`/var/log/pods/<namespace>_<pod>_<uid>/<container>/*.log`)
- A malformed `__host__` relabel rule identified and removed
- The `cri: {}` pipeline stage added for Minikube's container runtime log format
- Promtail's own target endpoint queried — returns empty
- Promtail logs inspected — no errors reported at any level

**Decision:** debugging was stopped and the current state retained. The
remaining cause appears specific to this Minikube environment's log path
mounting rather than to the configuration itself, and further investigation
carried an unbounded time cost against deliverables with fixed deadlines.

**Assessment:** the log-aggregation capability is partially delivered. The
aggregation backend works and is integrated; the collection agent is deployed
with correct configuration but is not yet shipping. Recording this accurately
is preferable to either removing the component or overstating its status.

---

## 5. Summary

| Technology | Status | Basis |
|---|---|---|
| Keycloak | Not built | No deliverable requires authentication; network-level isolation instead |
| OpenTelemetry | Not built | Single service; Prometheus answers the same questions |
| Wazuh | Not built | 4 GiB+ on a 7 GiB budget; build-time scanning covers detection |
| GitLab CE | Not built | Same capability as Jenkins, already fully implemented |
| Plotly | **Built** | Interactive analytics layer, distinct from static Matplotlib export |
| Open Policy Agent | **Built** | CI-time policy gate; found a real defect on first run |
| Scikit-learn | **Built** | Classical ML comparison module |
| Loki | **Built** | Deployed, Grafana-integrated |
| Promtail | **Partial** | Deployed, correctly configured, target discovery unresolved |

---

## 6. Standards Context

These decisions align with recognised guidance rather than being ad hoc:

- **NIST CSF 2.0** treats risk management as a matter of prioritising controls
  against resources, not implementing every available control.
- **ISO/IEC 27001** requires that control selection follow from risk
  assessment, with exclusions justified — which is the function of this
  document.
- **CIS Critical Security Controls** are explicitly tiered by implementation
  group, acknowledging that organisations implement what their resources
  support.
- **ITIL 4** frames this as the "start where you are" and "optimise" guiding
  principles: deliver working capability within constraints rather than
  deferring delivery pending complete tooling.
