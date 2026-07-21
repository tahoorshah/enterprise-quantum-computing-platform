# Redis: Deployment + Service (no PVC - cache data is disposable)
# Mirrors infra/k8s/02-redis.yaml.

resource "kubernetes_deployment" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "redis" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "redis" }
    }
    template {
      metadata {
        labels = { app = "redis" }
      }
      spec {
        container {
          name              = "redis"
          image             = "redis:7-alpine"
          image_pull_policy = "Never"
          port {
            container_port = 6379
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
}

resource "kubernetes_service" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace.qft.metadata[0].name
    labels    = { app = "redis" }
  }
  spec {
    selector = { app = "redis" }
    port {
      port        = 6379
      target_port = 6379
    }
    type = "ClusterIP"
  }
}
