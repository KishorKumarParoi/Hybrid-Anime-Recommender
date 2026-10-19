resource "azurerm_resource_group" "this" {
  name     = "rg-${var.cluster_name}"
  location = var.location

  tags = {
    project = var.cluster_name
  }
}

resource "azurerm_kubernetes_cluster" "this" {
  name                = var.cluster_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version
  sku_tier            = "Free" # control plane costs $0 (no uptime SLA — fine for a demo)

  identity {
    type = "SystemAssigned"
  }

  # Required system pool — CPU only; runs CoreDNS and the GPU Operator controllers.
  default_node_pool {
    name       = "system"
    vm_size    = var.system_vm_size
    node_count = 1
  }

  tags = {
    project = var.cluster_name
  }
}

# GPU pool: 1x T4 serving the single vLLM pod.
# gpu_driver = "None" skips AKS's own NVIDIA driver install so the GPU Operator
# owns the full stack (driver + device plugin + toolkit) without conflicts.
resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  count                 = var.enable_gpu_node_pool ? 1 : 0
  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = var.gpu_vm_size
  node_count            = 1
  gpu_driver            = "None"

  # Pin to Ubuntu 22.04 (containerd 1.7). On the default 24.04 image (containerd 2.3),
  # the GPU Operator toolkit writes a version-4 containerd drop-in that AKS's version-2
  # root config rejects ("drop-in config version 4 higher than root config version 2"),
  # and containerd fails to start -> node NotReady. containerd 1.7 has no such version
  # check and accepts the toolkit's config, so the node comes up clean.
  os_sku = "Ubuntu2204"

  node_labels = {
    workload = "gpu"
  }

  node_taints = ["nvidia.com/gpu=present:NoSchedule"]

  tags = {
    project = var.cluster_name
  }
}
