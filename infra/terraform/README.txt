=== TERRAFORM IaC FOR QFT PLATFORM ===

These files deploy the full platform to a dedicated Kubernetes namespace
(qft-terraform) using Terraform's Kubernetes provider - demonstrating
Infrastructure as Code without disturbing your existing kubectl deployment
(which stays in the "default" namespace).

Files:
  main.tf      - provider config, variables, namespace
  postgres.tf  - Postgres PVC + Deployment + Service
  redis.tf     - Redis Deployment + Service
  backend.tf   - Backend Deployment + Service
  frontend.tf  - Frontend Deployment + Service (NodePort 30081)

PREREQUISITES:
  - Minikube running
  - The images already loaded into Minikube:
      qft-backend:latest, qft-frontend:latest, postgres:16-alpine, redis:7-alpine
    (you loaded all of these earlier)

USAGE:
  cd infra/terraform
  terraform init          # downloads the kubernetes provider
  terraform plan          # preview - shows all resources to be created
  terraform apply         # type 'yes' to deploy
  # ... resources come up in namespace qft-terraform ...
  kubectl get pods -n qft-terraform
  minikube service frontend -n qft-terraform --url   # open in browser
  terraform destroy       # tear it all down cleanly

WHY TERRAFORM:
  The entire platform (database, cache, backend, frontend) is declared
  as code and provisioned with a single `terraform apply`, giving
  reproducible, version-controlled deployments. `terraform plan` previews
  changes, and `terraform destroy` tears everything down. In a cloud
  production setup the same workflow would also provision the cluster
  itself (EKS/GKE).
