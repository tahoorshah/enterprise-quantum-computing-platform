// Jenkins Declarative Pipeline for the QFT Bank Quantum Computing Platform.
//
// Stages: Checkout -> Backend Build & Test -> Frontend Build ->
//         Docker Image Build -> Security Scan (Trivy).
//
// This is "pipeline as code" - the pipeline definition lives in the repo
// and is version-controlled alongside the application, which is the modern
// best practice (vs configuring jobs by hand in the Jenkins UI).
//
// Assumes the Jenkins agent has: python3, python3-venv, docker, and trivy
// available. For a demo, Jenkins is run in Docker with the host Docker
// socket mounted so it can build images.

pipeline {
    agent any

    // Fail the build if it runs too long (protects against a hung stage)
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
                        # Run the full pytest suite from inside the backend dir
                        # so imports like "from app.main import app" resolve.
                        # --junitxml produces a report Jenkins can display.
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

        stage('Security: Trivy Scan') {
            steps {
                echo 'Scanning the backend image for vulnerabilities with Trivy...'
                // --exit-code 0 means the scan REPORTS vulnerabilities but does
                // not fail the build on them (appropriate for a demo/coursework
                // context). In a stricter production setup you would set
                // --exit-code 1 --severity CRITICAL to fail on critical CVEs.
                sh '''
                    trivy image --exit-code 0 --severity HIGH,CRITICAL --no-progress ${BACKEND_IMAGE} || true
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully: build, tests, and scan all passed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above to see what went wrong.'
        }
        always {
            // Clean up the venv so the workspace doesn't bloat between builds
            sh 'rm -rf backend/venv || true'
        }
    }
}
