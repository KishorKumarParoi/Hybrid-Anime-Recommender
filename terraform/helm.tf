data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  }
}

resource "helm_release" "hybrid_anime_recommender" {
  count = var.deploy_helm ? 1 : 0

  name             = "hybrid-anime-recommender"
  chart            = "${path.module}/../helm/hybrid-anime-recommender"
  namespace        = "default"
  create_namespace = true
  timeout          = 600

  values = [
    file("${path.module}/../helm/hybrid-anime-recommender/values-${var.environment}.yaml")
  ]

  set {
    name  = "image.tag"
    value = var.image_tag
  }

  depends_on = [
    google_container_cluster.primary,
    google_compute_router_nat.nat,
  ]
}
