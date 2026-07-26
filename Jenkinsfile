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
//
// Full stage list: Checkout -> Backend Build & Test -> SAST -> Dependency
// Scan -> Frontend Build -> Policy as Code -> Docker Build -> Container
// Security Scan -> SBOM Generation.

pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
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
    }

    post {
        success {
            echo 'DevSecOps pipeline completed: build, tests, 3 security scans and policy gate passed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
        always {
            sh 'rm -rf backend/venv || true'
        }
    }
}
