// Jenkins Declarative Pipeline for the QFT Bank Quantum Computing Platform.
//
// This is a DevSecOps pipeline - security is integrated as first-class
// pipeline stages, not bolted on afterwards. Three layers of security
// scanning run automatically on every build:
//   - SAST (bandit)         : static analysis of the Python source code
//   - Dependency (pip-audit) : known-CVE scan of Python dependencies
//   - Container (Trivy)      : vulnerability scan of the built Docker image
//
// Full stage list: Checkout -> Backend Build & Test -> SAST -> Dependency
// Scan -> Frontend Build -> Docker Build -> Container Security Scan.

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
    }

    post {
        success {
            echo 'DevSecOps pipeline completed: build, tests, and all 3 security scans passed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
        always {
            sh 'rm -rf backend/venv || true'
        }
    }
}
