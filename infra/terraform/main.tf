# Terraform configuration for the QFT Bank Quantum Computing Platform.
#
# Uses the Kubernetes provider to manage the platform's cluster resources
# as code (Infrastructure as Code). Instead of running `kubectl apply` on
# raw YAML by hand, Terraform declares the desired state and manages the
# full lifecycle:
#   terraform init     - download the provider
#   terraform plan     - preview what will change
#   terraform apply    - create/update the resources
#   terraform destroy  - tear everything down
#
# To keep this isolated from the existing kubectl-deployed stack (which
# runs in the "default" namespace), Terraform deploys everything into its
# own dedicated namespace, "qft-terraform". This demonstrates full IaC
# provisioning without disturbing the running demo.
#
# In a cloud production deployment, the same Terraform workflow would also
# provision the underlying cluster itself (e.g. EKS/GKE).

terraform {
  required_version = ">= 1.5"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

variable "namespace" {
  description = "Kubernetes namespace Terraform deploys into"
  type        = string
  default     = "qft-terraform"
}

variable "postgres_user" {
  type    = string
  default = "qft_admin"
}

variable "postgres_password" {
  type    = string
  default = "changeme_local_dev_only"
}

variable "postgres_db" {
  type    = string
  default = "qft_quantum_db"
}

# Create the dedicated namespace first; all other resources depend on it.
resource "kubernetes_namespace" "qft" {
  metadata {
    name = var.namespace
  }
}
