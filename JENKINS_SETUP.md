# Jenkins CI/CD Setup

This project uses a Jenkins **declarative pipeline** defined in the
`Jenkinsfile` at the repository root. The pipeline is version-controlled
alongside the code ("pipeline as code").

## Pipeline stages

1. **Checkout** - pull the source code
2. **Backend: Build & Test** - create a Python venv, install dependencies,
   run the full pytest suite (29 tests), publish results to Jenkins
3. **Frontend: Build** - `npm ci` + `npm run build` (React production build)
4. **Docker: Build Images** - build backend and frontend images
5. **Security: Trivy Scan** - scan the backend image for HIGH/CRITICAL CVEs

## Running Jenkins for a demo (in Docker)

Jenkins doesn't need to run 24/7. Spin it up only when demonstrating the
pipeline, then tear it down to free resources.

```bash
# Start Jenkins in Docker, mounting the host Docker socket so pipeline
# stages can build images. Data persists in a named volume.
docker run -d \
  --name jenkins \
  -p 8080:8080 -p 50000:50000 \
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
5. Click **Build Now** to run the pipeline

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

## Why Jenkins (viva talking point)

Jenkins was chosen from the approved stack (Jenkins / GitLab CE) because it
is significantly lighter than a self-hosted GitLab CE instance (which needs
4GB+ RAM), making it feasible on the development hardware, while still
providing a full pipeline-as-code CI/CD workflow. In production, the same
`Jenkinsfile` would run on a dedicated Jenkins server or agents with the
deploy stage pushing to the Kubernetes cluster.
