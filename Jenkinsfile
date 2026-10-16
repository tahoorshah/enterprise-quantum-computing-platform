// Jenkins Declarative Pipeline for the QFT Bank Quantum Computing Platform.
//
// This is a DevSecOps pipeline - security is integrated as first-class
// pipeline stages, not bolted on afterwards. Three layers of security
// scanning run automatically on every build:
//   - SAST (bandit)         : static analysis of the Python source code
//   - Dependency (pip-audit) : known-CVE scan of Python dependencies
//   - Container (Trivy)      : vulnerability scan of the built Docker image
//   - Policy (OPA/Conftest)  : Kubernetes manifests validated against Rego
//                              policy - a build GATE, not advisory
//   - Signing (cosign)       : images pushed to the Minikube registry, signed
//                              by digest, then verified - a build GATE
//
// Full stage list: Checkout -> Backend Build & Test -> SAST -> Dependency
// Scan -> Frontend Build -> Policy as Code -> Docker Build -> Container
// Security Scan -> SBOM Generation -> Push & Sign -> Verify Signatures.

pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    parameters {
        // Minikube registry addon, as reached from the Jenkins host. Jenkins
        // must run with --network host so that "localhost" means the same
        // machine to both the host Docker daemon (docker push) and to cosign
        // (which runs inside the Jenkins container). See JENKINS_SETUP.md.
        string(name: 'REGISTRY', defaultValue: 'localhost:5000',
               description: 'Container registry to push and sign images in')
        // Demo switch: replaces the signed backend image with an unsigned,
        // modified one just before verification, to show the gate blocking it.
        booleanParam(name: 'SIMULATE_TAMPER', defaultValue: false,
                     description: 'DEMO ONLY: swap in an unsigned backend image before verify (build must fail)')
    }

    environment {
        BACKEND_IMAGE  = "qft-backend:ci-${BUILD_NUMBER}"
        FRONTEND_IMAGE = "qft-frontend:ci-${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Backend: Build & Test') {
            steps {
                echo 'Setting up Python environment and running the test suite...'
                dir('backend') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        python3 -m pip install --upgrade pip
                        python3 -m pip install -r requirements.txt
                        python3 -m pytest tests/ -v --junitxml=test-results.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Security: SAST (bandit)') {
            steps {
                echo 'Static application security testing on Python source...'
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        python3 -m pip install bandit
                        bandit -r app/ -f txt -o bandit-report.txt -ll || true
                        echo "--- Bandit summary ---"
                        cat bandit-report.txt || true
                    '''
                    archiveArtifacts artifacts: 'bandit-report.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Security: Dependency Scan (pip-audit)') {
            steps {
                echo 'Scanning Python dependencies for known vulnerabilities...'
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        python3 -m pip install pip-audit
                        pip-audit --desc 2>&1 | tee pip-audit-report.txt || true
                    '''
                    archiveArtifacts artifacts: 'pip-audit-report.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Frontend: Build') {
            steps {
                echo 'Building the React production bundle...'
                dir('frontend') {
                    sh '''
                        npm ci
                        npm run build
                    '''
                }
            }
        }

        stage('Security: Policy as Code (OPA/Conftest)') {
            steps {
                echo 'Validating Kubernetes manifests against OPA policy...'
                sh '''
                    # Conftest is the OPA tool for testing structured config
                    # files. Preferred over raw `opa eval` here because it
                    # parses multi-document YAML natively - no YAML->JSON
                    # conversion step per manifest.
                    if ! command -v conftest >/dev/null 2>&1; then
                        CONFTEST_VERSION=0.56.0
                        curl -sSL -o /tmp/conftest.tar.gz \
                            "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz"
                        tar -xzf /tmp/conftest.tar.gz -C /tmp conftest
                        chmod +x /tmp/conftest
                        export PATH="/tmp:$PATH"
                    fi

                    # Deliberately NOT suffixed with `|| true`. The three
                    # scanning stages above are advisory - they report CVEs
                    # that may have no available fix. This stage is a GATE:
                    # every deny rule describes a condition the manifests
                    # currently satisfy, so a failure here means a real
                    # regression was introduced and the build should stop.
                    conftest test --policy infra/policy infra/k8s/ | tee conftest-report.txt
                '''
                archiveArtifacts artifacts: 'conftest-report.txt', allowEmptyArchive: true
            }
        }

        stage('Docker: Build Images') {
            steps {
                echo 'Building Docker images...'
                sh '''
                    docker build -t ${BACKEND_IMAGE} ./backend
                    docker build -t ${FRONTEND_IMAGE} ./frontend
                '''
            }
        }

        stage('Security: Container Scan (Trivy)') {
            steps {
                echo 'Scanning the backend image for OS/library vulnerabilities...'
                sh '''
                    trivy image --exit-code 0 --severity HIGH,CRITICAL --no-progress ${BACKEND_IMAGE} | tee trivy-report.txt || true
                '''
                archiveArtifacts artifacts: 'trivy-report.txt', allowEmptyArchive: true
            }
        }

        stage('Security: SBOM Generation (Trivy CycloneDX)') {
            steps {
                echo 'Generating CycloneDX SBOMs for both images...'
                sh '''
                    trivy image --format cyclonedx --output sbom-backend.json ${BACKEND_IMAGE}
                    trivy image --format cyclonedx --output sbom-frontend.json ${FRONTEND_IMAGE}
                '''
                archiveArtifacts artifacts: 'sbom-*.json', allowEmptyArchive: false
            }
        }

        stage('Supply Chain: Push & Sign Images (cosign)') {
            steps {
                echo 'Pushing images to the registry and signing them by digest...'
                // The private key and its password exist only as Jenkins
                // credentials, injected for this stage alone and masked in logs.
                // cosign reads the key password from $COSIGN_PASSWORD.
                withCredentials([
                    file(credentialsId: 'cosign-private-key', variable: 'COSIGN_KEY'),
                    string(credentialsId: 'cosign-password', variable: 'COSIGN_PASSWORD')
                ]) {
                    sh '''
                        set -eu
                        COSIGN=$(scripts/install-cosign.sh)

                        curl -sSf "http://${REGISTRY}/v2/" >/dev/null || {
                            echo "Registry ${REGISTRY} is not reachable - is the Minikube registry addon enabled and forwarded?"
                            exit 1
                        }

                        : > image-digests.env
                        for name in backend frontend; do
                            remote="${REGISTRY}/qft-${name}:ci-${BUILD_NUMBER}"
                            docker tag "qft-${name}:ci-${BUILD_NUMBER}" "$remote"
                            docker push "$remote"

                            # Sign the immutable digest, never the tag: a tag can be
                            # re-pointed at a different image after signing; a
                            # digest is the hash of the image content itself.
                            ref=$(docker inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$remote" \
                                  | grep "^${REGISTRY}/qft-${name}@sha256:" | head -n1)
                            [ -n "$ref" ] || { echo "Could not resolve digest for $remote"; exit 1; }

                            # --tlog-upload=false: do not publish this private
                            # registry's image names/digests to Sigstore's public
                            # Rekor transparency log. Verify must therefore use
                            # --insecure-ignore-tlog=true (see next stage).
                            "$COSIGN" sign --yes --key "$COSIGN_KEY" --tlog-upload=false \
                                --allow-insecure-registry "$ref"

                            echo "$(echo "$name" | tr a-z A-Z)_REF=$ref" >> image-digests.env
                        done
                        cat image-digests.env
                    '''
                }
                archiveArtifacts artifacts: 'image-digests.env', allowEmptyArchive: false
            }
        }

        stage('Supply Chain: Verify Signatures (cosign)') {
            steps {
                echo 'Verifying image signatures against the committed public key...'
                sh '''
                    set -eu
                    COSIGN=$(scripts/install-cosign.sh)
                    [ -f infra/cosign/cosign.pub ] || {
                        echo "infra/cosign/cosign.pub is missing - refusing to skip verification (see infra/cosign/README.md)"
                        exit 1
                    }
                    . ./image-digests.env

                    if [ "${SIMULATE_TAMPER}" = "true" ]; then
                        # Simulates an attacker swapping the artifact between
                        # build and deploy: any change (here, one label) gives
                        # a new digest that the pipeline's key never signed.
                        echo "!!! SIMULATE_TAMPER: replacing backend with an unsigned, modified image"
                        tampered="${REGISTRY}/qft-backend:tampered-${BUILD_NUMBER}"
                        printf 'FROM %s\nLABEL tampered=true\n' "$BACKEND_REF" | docker build -t "$tampered" -
                        docker push "$tampered"
                        BACKEND_REF=$(docker inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$tampered" \
                                      | grep "^${REGISTRY}/qft-backend@sha256:" | head -n1)
                    fi

                    # Deliberately NOT suffixed with `|| true`: cosign exits
                    # non-zero on a missing or invalid signature, which fails
                    # this stage and the build. This is a GATE.
                    # --insecure-ignore-tlog=true pairs with --tlog-upload=false
                    # in the signing stage: no Rekor entry was created, so
                    # verify must not look for one (it would fail trying to
                    # reach/find it). The signature itself is still
                    # cryptographically checked against cosign.pub.
                    for ref in "$BACKEND_REF" "$FRONTEND_REF"; do
                        echo "--- verifying $ref"
                        "$COSIGN" verify --key infra/cosign/cosign.pub --insecure-ignore-tlog=true \
                            --allow-insecure-registry "$ref"
                    done
                '''
            }
        }
    }

    post {
        success {
            echo 'DevSecOps pipeline completed: build, tests, 3 security scans, policy gate and signature gate passed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
        always {
            sh 'rm -rf backend/venv || true'
        }
    }
}
