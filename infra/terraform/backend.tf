# Backend (FastAPI): Deployment + Service
# Mirrors infra/k8s/03-backend.yaml. Connects to postgres/redis via their
# in-namespace service names.

resource "kubernetes_deployment" "backend" {
  metadata {
    name      = "backend"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "backend" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "backend" }
    }
    template {
      metadata {
        labels = { app = "backend" }
      }
      spec {
        container {
          name              = "backend"
          image             = "qft-backend:latest"
          image_pull_policy = "Never"

          port {
            container_port = 8000
          }

          env {
            name  = "DATABASE_URL"
            value = "postgresql://${var.postgres_user}:${var.postgres_password}@postgres:5432/${var.postgres_db}"
          }
          env {
            name  = "REDIS_URL"
            value = "redis://redis:6379/0"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "150m"
            }
            limits = {
              memory = "1Gi"
              cpu    = "1000m"
            }
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_deployment.postgres,
    kubernetes_deployment.redis,
  ]
}

resource "kubernetes_service" "backend" {
  metadata {
    name      = "backend"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "backend" }
  }
  spec {
    selector = { app = "backend" }
    port {
      port        = 8000
      target_port = 8000
    }
    type = "ClusterIP"
  }
}
