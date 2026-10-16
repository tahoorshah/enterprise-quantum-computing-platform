# Jenkins CI/CD Setup

This project uses a Jenkins **declarative pipeline** defined in the
`Jenkinsfile` at the repository root. The pipeline is version-controlled
alongside the code ("pipeline as code").

## Pipeline stages

1. **Checkout** - pull the source code
2. **Backend: Build & Test** - create a Python venv, install dependencies,
   run the full pytest suite (108 tests), publish JUnit results to Jenkins
3. **Security: SAST (bandit)** - static analysis of Python source (advisory)
4. **Security: Dependency Scan (pip-audit)** - known-CVE scan of Python
   dependencies (advisory)
5. **Frontend: Build** - `npm ci` + `npm run build` (React production build)
6. **Security: Policy as Code (OPA/Conftest)** - validate Kubernetes
   manifests against Rego policy; this is a **gate** (build fails on
   violation)
7. **Docker: Build Images** - build backend and frontend images
8. **Security: Container Scan (Trivy)** - scan both images for
   HIGH/CRITICAL CVEs (advisory)
9. **Security: SBOM Generation (Trivy CycloneDX)** - generate SBOMs for
   both images
10. **Supply Chain: Push & Sign Images (cosign)** - push both images to the
    Minikube registry and sign each one **by digest** with the private key
    held in Jenkins credentials; digests archived as `image-digests.env`
11. **Supply Chain: Verify Signatures (cosign)** - verify both digests
    against the committed `infra/cosign/cosign.pub`; this is a **gate**
    (build fails on a missing or invalid signature). The `SIMULATE_TAMPER`
    build parameter swaps in an unsigned image here to demo the gate failing.

## Running Jenkins for a demo (in Docker)

Jenkins doesn't need to run 24/7. Spin it up only when demonstrating the
pipeline, then tear it down to free resources.

```bash
# Start Jenkins in Docker, mounting the host Docker socket so pipeline
# stages can build images. Data persists in a named volume.
# --network host: the signing stages push with the HOST Docker daemon but run
# cosign INSIDE this container; sharing the host network makes
# "localhost:5000" (the forwarded Minikube registry) mean the same to both.
# (Ports 8080/50000 are then bound on the host directly, so no -p flags.)
docker run -d \
  --name jenkins \
  --network host \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

# Get the initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Then:
1. Open http://localhost:8080
2. Paste the initial admin password
3. Install suggested plugins
4. Create a **Pipeline** job -> "Pipeline script from SCM" -> point it at
   this GitHub repo -> it auto-detects the `Jenkinsfile`
5. Add the two cosign credentials (Manage Jenkins -> Credentials):
   `cosign-private-key` (Secret file) and `cosign-password` (Secret text).
   Generation steps and where each key lives: `infra/cosign/README.md`
6. Click **Build Now** to run the pipeline (the first run registers the
   `REGISTRY` and `SIMULATE_TAMPER` parameters; later runs use
   **Build with Parameters**)

### Registry for the signing stages (on the Minikube host)

```bash
minikube addons enable registry
# Forward host localhost:5000 to the in-cluster registry service:
kubectl port-forward -n kube-system service/registry 5000:80 --address 127.0.0.1 &
curl -s http://localhost:5000/v2/_catalog   # expect {"repositories":[...]}
```

**Note:** the default `jenkins/jenkins:lts` image doesn't include python3,
node, docker CLI, or trivy. For a full run you'd either use a custom Jenkins
image with those tools installed, or configure Jenkins agents that have them.
For coursework, running the pipeline stages that the base image supports and
explaining the rest is acceptable - the `Jenkinsfile` demonstrates the
complete intended pipeline regardless.

## Tearing down after the demo

```bash
docker stop jenkins && docker rm jenkins
# (keeps the jenkins_home volume; add 'docker volume rm jenkins_home' to fully reset)
```

## Why Jenkins

Jenkins was chosen from the approved stack (Jenkins / GitLab CE) because it
is significantly lighter than a self-hosted GitLab CE instance (which needs
4GB+ RAM), making it feasible on the development hardware, while still
providing a full pipeline-as-code CI/CD workflow. In production, the same
`Jenkinsfile` would run on a dedicated Jenkins server or agents with the
deploy stage pushing to the Kubernetes cluster.
