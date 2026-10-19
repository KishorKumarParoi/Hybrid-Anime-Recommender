resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  # Enable Kubernetes control plane audit logging for enterprise security
  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy
  ]
}

# CPU System Managed Node Group (CoreDNS, kube-system controllers, Ingress)
resource "aws_eks_node_group" "system" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "system"
  node_role_arn   = aws_iam_role.nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = var.system_instance_types
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = 1
    min_size     = 1
    max_size     = 2
  }

  labels = {
    workload = "system"
  }

  depends_on = [
    aws_iam_role_policy_attachment.worker_node_policy,
    aws_iam_role_policy_attachment.cni_policy,
    aws_iam_role_policy_attachment.ecr_read_only,
  ]
}

# Dedicated GPU Managed Node Group (NVIDIA T4 or A10G) with EKS GPU Optimized AMI
resource "aws_eks_node_group" "gpu" {
  count           = var.enable_gpu_node_group ? 1 : 0
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "gpu"
  node_role_arn   = aws_iam_role.nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = var.gpu_instance_types
  ami_type       = "AL2_x86_64_GPU" # Pre-baked NVIDIA driver + container toolkit
  capacity_type  = var.spot_gpu ? "SPOT" : "ON_DEMAND"

  # Cost Optimization: Scale to 0 when idle
  scaling_config {
    desired_size = 1
    min_size     = 0
    max_size     = 1
  }

  taint {
    key    = "nvidia.com/gpu"
    value  = "present"
    effect = "NO_SCHEDULE"
  }

  labels = {
    workload = "gpu"
  }

  depends_on = [
    aws_iam_role_policy_attachment.worker_node_policy,
    aws_iam_role_policy_attachment.cni_policy,
    aws_iam_role_policy_attachment.ecr_read_only,
  ]
}
