# Frontend (nginx serving React + proxying /api): Deployment + Service
# Mirrors infra/k8s/04-frontend.yaml. Exposed via NodePort (30081 to avoid
# clashing with the kubectl-deployed frontend's 30080).

resource "kubernetes_deployment" "frontend" {
  metadata {
    name      = "frontend"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "frontend" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "frontend" }
    }
    template {
      metadata {
        labels = { app = "frontend" }
      }
      spec {
        container {
          name              = "frontend"
          image             = "qft-frontend:latest"
          image_pull_policy = "Never"
          port {
            container_port = 80
          }
          resources {
            requests = {
              memory = "32Mi"
              cpu    = "50m"
            }
            limits = {
              memory = "128Mi"
              cpu    = "250m"
            }
          }
        }
      }
    }
  }

  depends_on = [kubernetes_deployment.backend]
}

resource "kubernetes_service" "frontend" {
  metadata {
    name      = "frontend"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "frontend" }
  }
  spec {
    selector = { app = "frontend" }
    port {
      port        = 80
      target_port = 80
      node_port   = 30081
    }
    type = "NodePort"
  }
}

# Output the command to reach the Terraform-deployed frontend.
output "frontend_access" {
  value = "Run: minikube service frontend -n ${var.namespace} --url"
}
