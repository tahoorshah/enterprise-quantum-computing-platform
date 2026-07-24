# Policy-as-code gate for the QFT Bank Kubernetes manifests.
#
# Evaluated by Conftest (Open Policy Agent) as a Jenkins pipeline stage, so
# a manifest that violates baseline security or reliability expectations
# fails the build rather than reaching the cluster. This is the "shift left"
# principle applied to infrastructure: the same class of check a cluster
# admission controller would perform, run at commit time instead.
#
# Rule severity is deliberate:
#   deny  - a violation the project genuinely does not have; blocks the build
#   warn  - a known, documented trade-off; visible but non-blocking
#
# Standards mapping: CIS Kubernetes Benchmark 5.x, NIST CSF 2.0 PR.AC-6
# (least privilege) and PR.IP-1 (baseline configuration), ISO/IEC 27001
# A.8.9 (configuration management).

package main

import rego.v1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Workload kinds that carry a pod template we care about.
workload_kinds := {"Deployment", "StatefulSet", "DaemonSet"}

is_workload if {
	input.kind in workload_kinds
}

containers contains container if {
	is_workload
	container := input.spec.template.spec.containers[_]
}

name := input.metadata.name

# ---------------------------------------------------------------------------
# DENY: resource limits must be set
#
# A container without limits can consume every byte on the node and evict its
# neighbours. On a single-node Minikube running seven workloads this is not
# theoretical - one runaway pod takes down the whole demonstration.
# ---------------------------------------------------------------------------

deny contains msg if {
	container := containers[_]
	not container.resources.limits.memory
	msg := sprintf("%s/%s: container '%s' has no memory limit", [input.kind, name, container.name])
}

deny contains msg if {
	container := containers[_]
	not container.resources.limits.cpu
	msg := sprintf("%s/%s: container '%s' has no CPU limit", [input.kind, name, container.name])
}

# ---------------------------------------------------------------------------
# DENY: resource requests must be set
#
# Without requests the scheduler has no basis for placement decisions and
# every pod lands in the BestEffort QoS class - first to be killed under
# memory pressure.
# ---------------------------------------------------------------------------

deny contains msg if {
	container := containers[_]
	not container.resources.requests.memory
	msg := sprintf("%s/%s: container '%s' has no memory request", [input.kind, name, container.name])
}

# ---------------------------------------------------------------------------
# DENY: liveness and readiness probes on the application tier
#
# Scoped to the application workloads rather than every container: the
# nginx crash-loop incident earlier in this project was precisely a case
# where the frontend was Running-but-broken. Probes are what turn that into
# an automatic restart instead of a silent outage.
# ---------------------------------------------------------------------------

app_workloads := {"backend", "frontend"}

deny contains msg if {
	name in app_workloads
	container := containers[_]
	not container.readinessProbe
	msg := sprintf("%s/%s: container '%s' has no readinessProbe", [input.kind, name, container.name])
}

deny contains msg if {
	name in app_workloads
	container := containers[_]
	not container.livenessProbe
	msg := sprintf("%s/%s: container '%s' has no livenessProbe", [input.kind, name, container.name])
}

# ---------------------------------------------------------------------------
# DENY: the backend must run as a non-root user
#
# The backend image builds an explicit UID-1000 user. Asserting it here means
# a regression in the Dockerfile fails the pipeline rather than silently
# restoring root. CIS Kubernetes Benchmark 5.2.6.
# ---------------------------------------------------------------------------

deny contains msg if {
	name == "backend"
	container := containers[_]
	not container.securityContext.runAsNonRoot
	msg := sprintf("%s/%s: container '%s' must set securityContext.runAsNonRoot", [input.kind, name, container.name])
}

deny contains msg if {
	name == "backend"
	container := containers[_]
	container.securityContext.allowPrivilegeEscalation
	msg := sprintf("%s/%s: container '%s' must not allow privilege escalation", [input.kind, name, container.name])
}

# ---------------------------------------------------------------------------
# WARN: mutable image tags
#
# ':latest' means the running image cannot be identified from the manifest
# and a rollback is not reproducible. This is a KNOWN, ACCEPTED trade-off in
# this project: images are built directly into the Minikube Docker daemon
# with imagePullPolicy: Never, so there is no registry to pin a digest
# against. A production deployment would push to a registry and pin by
# digest. Recorded as a warning so the trade-off is visible in every build
# log rather than forgotten.
# ---------------------------------------------------------------------------

warn contains msg if {
	container := containers[_]
	endswith(container.image, ":latest")
	msg := sprintf("%s/%s: container '%s' uses mutable tag ':latest' - acceptable for local Minikube builds, pin by digest in production", [input.kind, name, container.name])
}

# ---------------------------------------------------------------------------
# WARN: containers other than the backend lack a securityContext
#
# The frontend serves via nginx, which binds port 80 and therefore requires
# either root or an explicit port change plus Service retargeting. Hardening
# it is correct but carries deployment risk that was not accepted during the
# assessment window. Third-party images (postgres, redis, prometheus,
# grafana, loki, promtail) run their upstream defaults. Both cases are
# surfaced rather than hidden.
# ---------------------------------------------------------------------------

warn contains msg if {
	container := containers[_]
	name != "backend"
	not container.securityContext.runAsNonRoot
	msg := sprintf("%s/%s: container '%s' has no runAsNonRoot securityContext", [input.kind, name, container.name])
}
