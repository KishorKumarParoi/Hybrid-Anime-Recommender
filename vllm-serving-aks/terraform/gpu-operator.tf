resource "helm_release" "gpu_operator" {
  count            = var.enable_gpu_node_pool ? 1 : 0
  name             = "gpu-operator"
  repository       = "https://helm.ngc.nvidia.com/nvidia"
  chart            = "gpu-operator"
  version          = "v26.3.2"
  namespace        = "gpu-operator"
  create_namespace = true

  # Unlike EKS (driver baked into the accelerated AMI), AKS GPU nodes are created with
  # gpu_driver = "None" and the Operator installs the driver itself — Ubuntu is a
  # supported OS for the Operator's driver container.
  set {
    name  = "driver.enabled"
    value = "true"
  }

  # AKS's base /etc/containerd/config.toml is version 2 and imports drop-ins from
  # /etc/containerd/conf.d/. By default the toolkit writes its NVIDIA runtime as a
  # drop-in with a HIGHER config version, and containerd 2.x refuses to start
  # ("drop-in config version N higher than root config version 2"). Point the toolkit
  # at the main config so it edits that single file in place — no version mismatch.
  set {
    name  = "toolkit.env[0].name"
    value = "CONTAINERD_CONFIG"
  }
  set {
    name  = "toolkit.env[0].value"
    value = "/etc/containerd/config.toml"
  }

  # Tolerate the custom GPU taint so the Operator's DaemonSets land on the GPU node.
  set {
    name  = "daemonsets.tolerations[0].key"
    value = "nvidia.com/gpu"
  }
  set {
    name  = "daemonsets.tolerations[0].operator"
    value = "Exists"
  }
  set {
    name  = "daemonsets.tolerations[0].effect"
    value = "NoSchedule"
  }

  depends_on = [azurerm_kubernetes_cluster_node_pool.gpu]
}
