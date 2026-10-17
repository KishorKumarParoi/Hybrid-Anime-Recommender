# Hybrid Anime Recommender Helm Chart

Enterprise Helm Chart for deploying the **Hybrid Anime Recommender & AI Agent Platform** on Kubernetes (Minikube, KinD, GKE, EKS).

---

## 📦 Features

- **Hardened Security**: Runs as unprivileged user (`UID 10001`), `readOnlyRootFilesystem: true`, drops all Linux capabilities.
- **Auto-Scaling**: Integrated HorizontalPodAutoscaler (`HPA`) supporting CPU and Memory utilization targets.
- **Observability**: Built-in Prometheus scraping annotations (`/metrics` on port 5000).
- **Embedded Caching**: Optional self-contained Redis cache deployment (`redis.enabled: true`).
- **Multi-Environment Support**: Clean configuration separation via `values-dev.yaml` and `values-prod.yaml`.

---

## 🚀 Quickstart

### 1. Lint the Chart
```bash
helm lint helm/hybrid-anime-recommender
```

### 2. Dry-Run / Template
```bash
helm template anime-rec helm/hybrid-anime-recommender -f helm/hybrid-anime-recommender/values-dev.yaml
```

### 3. Install or Upgrade in Kubernetes

#### Local / Development (Minikube / KinD):
```bash
helm upgrade --install anime-rec helm/hybrid-anime-recommender \
  -f helm/hybrid-anime-recommender/values-dev.yaml \
  --namespace default \
  --create-namespace
```

#### Production (GKE Autopilot / Cloud):
```bash
helm upgrade --install anime-rec helm/hybrid-anime-recommender \
  -f helm/hybrid-anime-recommender/values-prod.yaml \
  --set image.tag="v1.0.0" \
  --namespace production \
  --create-namespace
```

### 4. Check Status
```bash
helm status anime-rec
kubectl get pods -l app=hybrid-anime-recommender
```

### 5. Uninstall
```bash
helm uninstall anime-rec
```
