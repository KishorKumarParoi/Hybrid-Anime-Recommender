terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment to enable remote S3 state storage & locking:
  # backend "s3" {
  #   bucket         = "hybrid-anime-recommender-tfstate"
  #   key            = "aws/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "hybrid-anime-recommender-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project
      ManagedBy   = "Terraform"
      Environment = "Production"
    }
  }
}

# ─── Data & Locals ────────────────────────────────────────────────────────────

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs           = slice(data.aws_availability_zones.available.names, 0, 2)
  https_enabled = var.acm_certificate_arn != ""
}

# ─── VPC & Networking ─────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project}-vpc" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = local.azs[count.index]
  tags              = { Name = "${var.project}-private-${count.index}" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.project}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ─── VPC Endpoints (Private subnet access without NAT Gateway egress cost) ────

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id, aws_route_table.private.id]
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "cloudwatch_logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# ─── Security Groups ──────────────────────────────────────────────────────────

resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.project}-vpc-endpoints"
  description = "Security group for private interface VPC endpoints"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.project}-alb"
  description = "Application Load Balancer ingress rules"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  dynamic "ingress" {
    for_each = local.https_enabled ? [1] : []
    content {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
  ingress {
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project}-ecs-tasks"
  description = "ECS tasks ingress only from Application Load Balancer"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port       = 8000
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "${var.project}-redis"
  description = "ElastiCache Redis ingress strictly from ECS tasks"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project}-rds"
  description = "RDS PostgreSQL ingress strictly from ECS tasks"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}

# ─── AWS Bedrock Content & Injection Safety Guardrail ─────────────────────────

resource "aws_bedrock_guardrail" "main" {
  name                      = "${var.project}-guardrail"
  description               = "Content safety and prompt injection guardrail for the Hybrid Anime Research Agent"
  blocked_input_messaging   = "Your anime query or prompt was blocked by our content safety and injection defense policy."
  blocked_outputs_messaging = "The generated recommendation was blocked by our content safety policy."

  content_policy_config {
    filters_config {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "INSULTS"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "MISCONDUCT"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  topic_policy_config {
    topics_config {
      name       = "weapons"
      definition = "Any discussion about creating, obtaining, or using weapons, firearms, explosives, or other means of physical harm."
      examples   = ["How do I build an explosive", "Where can I buy illegal weapons", "How to synthesize toxic substances"]
      type       = "DENY"
    }
    topics_config {
      name       = "illegal_activities"
      definition = "Discussions about engaging in illegal activities including fraud, hacking anime platform databases, or criminal acts."
      examples   = ["How to crack API keys", "How to dump PostgreSQL user credentials", "How to perform DDoS on recommendations"]
      type       = "DENY"
    }
    topics_config {
      name       = "self_harm"
      definition = "Content that promotes, encourages, or provides instructions for self-harm, suicide, or hurting others."
      examples   = ["How to hurt myself", "Methods of self-harm"]
      type       = "DENY"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "AWS_ACCESS_KEY"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "PHONE"
      action = "ANONYMIZE"
    }
  }

  word_policy_config {
    managed_word_lists_config {
      type = "PROFANITY"
    }
  }
}

resource "aws_bedrock_guardrail_version" "main" {
  guardrail_arn = aws_bedrock_guardrail.main.guardrail_arn
  description   = "v1 - deployed by Terraform for Hybrid Anime Recommender"
}

# ─── ElastiCache Redis (Semantic Vector Cache & Session Memory) ───────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_cache_nodes
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ─── RDS PostgreSQL (Research Dossier & Long-Term Memory Vector Store) ────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-postgres"
  engine                  = "postgres"
  engine_version          = "15.8"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  max_allocated_storage   = 100
  db_name                 = "animeresearchdb"
  username                = "dbadmin"
  password                = random_password.db_password.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  multi_az                = var.db_multi_az
  deletion_protection     = false
  skip_final_snapshot     = true
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:05:00-sun:06:00"
  tags                    = { Name = "${var.project}-postgres" }
}

# ─── Application Load Balancer (ALB) ──────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "app" {
  name        = "${var.project}-app-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }
}

resource "aws_lb_target_group" "pyrit" {
  name        = "${var.project}-pyrit-tg"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = local.https_enabled ? "redirect" : "forward"
    dynamic "redirect" {
      for_each = local.https_enabled ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
    dynamic "forward" {
      for_each = local.https_enabled ? [] : [1]
      content {
        target_group {
          arn = aws_lb_target_group.app.arn
        }
      }
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = local.https_enabled ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_lb_listener" "pyrit" {
  load_balancer_arn = aws_lb.main.arn
  port              = 8001
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.pyrit.arn
  }
}

# ─── ECS Fargate Cluster & IAM Roles ──────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project}-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_basic" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${var.project}-execution-secrets"
  role = aws_iam_role.ecs_task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project}/*"
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.project}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project}-task-policy"
  role = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:ApplyGuardrail"]
        Resource = aws_bedrock_guardrail.main.guardrail_arn
      }
    ]
  })
}

# ─── CloudWatch Logging ───────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project}-app"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "pyrit" {
  name              = "/ecs/${var.project}-pyrit"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "tensorzero" {
  name              = "/ecs/${var.project}-tensorzero"
  retention_in_days = var.log_retention_days
}

# ─── Secrets Manager (Enterprise Configuration JSON) ──────────────────────────

resource "aws_secretsmanager_secret" "config" {
  name = "${var.project}/config"
}

resource "aws_secretsmanager_secret_version" "config" {
  secret_id = aws_secretsmanager_secret.config.id
  secret_string = jsonencode({
    # LLM Providers
    GROQ_API_KEY   = var.groq_api_key
    OPENAI_API_KEY = var.openai_api_key

    # Observability
    LANGSMITH_API_KEY = var.langsmith_api_key
    LANGCHAIN_PROJECT = var.project
    LANGSMITH_DATASET = "${var.project}-reports"

    # Authentication
    API_KEY = var.api_key

    # AWS Infrastructure
    AWS_REGION                = var.aws_region
    BEDROCK_GUARDRAIL_ID      = aws_bedrock_guardrail.main.guardrail_id
    BEDROCK_GUARDRAIL_VERSION = aws_bedrock_guardrail_version.main.version

    # Database & Storage Endpoints
    REDIS_URL      = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
    TENSORZERO_URL = "http://localhost:3000"
    DATABASE_URL   = "postgresql://dbadmin:${random_password.db_password.result}@${aws_db_instance.postgres.endpoint}/animeresearchdb"

    # Semantic Cache & Agent Tunables
    CACHE_TTL                  = "3600"
    CACHE_SIMILARITY_THRESHOLD = "0.85"
    SESSION_TTL                = "1800"
    SESSION_MAX_MESSAGES       = "5"
    SESSION_CONTENT_TRUNCATE   = "500"
    LTM_DAYS                   = "7"
    LTM_THRESHOLD              = "0.88"
    LTM_DIFF_THRESHOLD         = "0.7"
    LTM_DIFF_LIMIT             = "5"
    IVFFLAT_LISTS              = "100"
    STREAM_KEY                 = "research:jobs"
    CONSUMER_GROUP             = "workers"
    RESULT_TTL                 = "3600"
    AGENT_REPORT_TRUNCATE      = "3000"
    AGENT_MAX_ITERATIONS       = "2"
    EVAL_REPORT_TRUNCATE       = "1500"
    EVAL_COMMENT_TRUNCATE      = "300"
    LLM_MAX_RETRIES            = "3"
    LLM_RETRY_DELAY            = "1.0"
    RATE_LIMIT_REQUESTS        = "10"
    RATE_LIMIT_WINDOW          = "60"
    DB_POOL_MIN                = "2"
    DB_POOL_MAX                = "10"
  })
}

# ─── ECS Task Definitions ─────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project}-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([
    {
      name         = "app"
      image        = var.app_image
      essential    = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      environment  = [{ name = "AWS_REGION", value = var.aws_region }]
      dependsOn    = [{ containerName = "tensorzero", condition = "START" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    },
    {
      name         = "tensorzero"
      image        = var.tensorzero_image
      essential    = true
      portMappings = [{ containerPort = 3000, protocol = "tcp" }]
      secrets = [
        { name = "GROQ_API_KEY", valueFrom = "${aws_secretsmanager_secret.config.arn}:GROQ_API_KEY::" },
        { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.config.arn}:OPENAI_API_KEY::" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.tensorzero.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "pyrit" {
  family                   = "${var.project}-pyrit"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([{
    name         = "pyrit"
    image        = var.pyrit_image
    essential    = true
    portMappings = [{ containerPort = 8001, protocol = "tcp" }]
    environment = [
      { name = "TARGET_URL", value = "http://${aws_lb.main.dns_name}" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.pyrit.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ─── ECS Services ─────────────────────────────────────────────────────────────

resource "aws_ecs_service" "app" {
  name            = "${var.project}-app"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.app_desired_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8000
  }
  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "pyrit" {
  name            = "${var.project}-pyrit"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.pyrit.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.pyrit.arn
    container_name   = "pyrit"
    container_port   = 8001
  }
}

# ─── ECS Auto-Scaling ─────────────────────────────────────────────────────────

resource "aws_appautoscaling_target" "app" {
  max_capacity       = var.app_max_capacity
  min_capacity       = var.app_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "app_cpu" {
  name               = "${var.project}-app-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app.resource_id
  scalable_dimension = aws_appautoscaling_target.app.scalable_dimension
  service_namespace  = aws_appautoscaling_target.app.service_namespace
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_scale_target
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# ─── ECR Repositories with Security Vulnerability Scanning ────────────────────

resource "aws_ecr_repository" "app" {
  name                 = "${var.project}-app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "pyrit" {
  name                 = "${var.project}-pyrit"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "tensorzero" {
  name                 = "${var.project}-tensorzero"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration { scan_on_push = true }
}

# ─── EventBridge Scheduled Automated Red Team Attacks ─────────────────────────

resource "aws_cloudwatch_event_rule" "weekly_redteam" {
  name                = "${var.project}-weekly-redteam"
  description         = "Trigger weekly PyRIT red team automated security audit on Monday 02:00 AM"
  schedule_expression = "cron(0 2 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "redteam_ecs" {
  rule     = aws_cloudwatch_event_rule.weekly_redteam.name
  arn      = aws_ecs_cluster.main.arn
  role_arn = aws_iam_role.eventbridge_ecs.arn
  ecs_target {
    task_definition_arn = aws_ecs_task_definition.pyrit.arn
    launch_type         = "FARGATE"
    network_configuration {
      subnets          = aws_subnet.public[*].id
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = true
    }
  }
}

resource "aws_iam_role" "eventbridge_ecs" {
  name = "${var.project}-eventbridge-ecs"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_ecs_policy" {
  name = "${var.project}-eventbridge-ecs-policy"
  role = aws_iam_role.eventbridge_ecs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = aws_ecs_task_definition.pyrit.arn
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn,
        ]
      }
    ]
  })
}

# ─── S3 Static Web Application & Artifacts Storage ───────────────────────────

resource "random_string" "s3_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_s3_bucket" "static_cdn" {
  bucket        = "${var.project}-cdn-${random_string.s3_suffix.result}"
  force_destroy = true
  tags = {
    Project   = var.project
    ManagedBy = "Terraform"
    Tier      = "CDN-Origin"
  }
}

resource "aws_s3_bucket_public_access_block" "static_cdn" {
  bucket                  = aws_s3_bucket.static_cdn.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_cdn" {
  bucket = aws_s3_bucket.static_cdn.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ─── CloudFront Global Content Delivery Network (CDN) ─────────────────────────

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${var.project}-oac"
  description                       = "Origin Access Control for S3 static distribution"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront CDN for Hybrid Anime Recommender SPA and API"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.static_cdn.bucket_regional_domain_name
    origin_id                = "S3-StaticOrigin"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "ALB-ApiOrigin"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "S3-StaticOrigin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "ALB-ApiOrigin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies { forward = "all" }
    }
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project = var.project
    Tier    = "CloudFront-CDN"
  }
}

# ─── Amazon DocumentDB (MongoDB 4.0/5.0 Compatible Cluster) ───────────────────

resource "aws_security_group" "docdb" {
  name        = "${var.project}-docdb-sg"
  description = "Access to Amazon DocumentDB cluster from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MongoDB wire protocol from ECS tasks"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project}-docdb-sg"
    Project = var.project
  }
}

resource "aws_docdb_subnet_group" "main" {
  name        = "${var.project}-docdb-subnets"
  description = "Subnet group for DocumentDB in private subnets"
  subnet_ids  = aws_subnet.private[*].id
  tags = {
    Project = var.project
  }
}

resource "aws_docdb_cluster" "main" {
  cluster_identifier      = "${var.project}-docdb"
  engine                  = "docdb"
  master_username         = "docdbadmin"
  master_password         = var.docdb_master_password
  backup_retention_period = 5
  preferred_backup_window = "07:00-09:00"
  skip_final_snapshot     = true
  db_subnet_group_name    = aws_docdb_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.docdb.id]
  storage_encrypted       = true

  tags = {
    Name      = "${var.project}-docdb"
    Project   = var.project
    Database  = "DocumentDB-MongoDB"
  }
}

resource "aws_docdb_cluster_instance" "cluster_instances" {
  count              = 1
  identifier         = "${var.project}-docdb-instance-${count.index}"
  cluster_identifier = aws_docdb_cluster.main.id
  instance_class     = "db.t3.medium"
}

