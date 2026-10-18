# ==============================================================================
# AZURE EVENT HUBS (APACHE KAFKA STREAMING) & AI CONTENT SAFETY
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ─── Resource Group ───────────────────────────────────────────────────────────
resource "azurerm_resource_group" "rg" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.azure_region

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Tier        = "EventStreaming"
  }
}

# ─── Azure Event Hubs Namespace (Kafka 1.0+ API Surface) ──────────────────────
# Standard tier automatically exposes Apache Kafka endpoints on port 9093 (SASL_SSL)
resource "azurerm_eventhub_namespace" "kafka_ns" {
  name                = "${var.project_name}-kafka-${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = var.eventhub_sku
  capacity            = var.eventhub_capacity

  auto_inflate_enabled     = var.auto_inflate_enabled
  maximum_throughput_units = var.max_throughput_units

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Streaming   = "ApacheKafka"
  }
}

# ─── Kafka Topics (Event Hubs) ─────────────────────────────────────────────────

# 1. Real-time User Anime Interactions & Ratings Stream
resource "azurerm_eventhub" "interactions_stream" {
  name                = "anime-interactions-stream"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = var.partition_count
  message_retention   = var.message_retention_days
}

# Consumer group for online recommendation adaptation worker
resource "azurerm_eventhub_consumer_group" "recommender_cg" {
  name                = "recommender-online-worker"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  eventhub_name       = azurerm_eventhub.interactions_stream.name
  resource_group_name = azurerm_resource_group.rg.name
}

# 2. PyRIT Red-Teaming & Security Audit Events Stream
resource "azurerm_eventhub" "security_audit_stream" {
  name                = "security-audit-stream"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 2
  message_retention   = var.message_retention_days
}

# Consumer group for PyRIT audit logger and security alerts
resource "azurerm_eventhub_consumer_group" "security_cg" {
  name                = "pyrit-audit-logger"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  eventhub_name       = azurerm_eventhub.security_audit_stream.name
  resource_group_name = azurerm_resource_group.rg.name
}

# 3. Autonomous LangGraph Research Events Stream
resource "azurerm_eventhub" "research_stream" {
  name                = "agent-research-stream"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 2
  message_retention   = var.message_retention_days
}

# Consumer group for dossier archiving
resource "azurerm_eventhub_consumer_group" "research_cg" {
  name                = "research-dossier-archiver"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  eventhub_name       = azurerm_eventhub.research_stream.name
  resource_group_name = azurerm_resource_group.rg.name
}

# ─── Kafka SASL Shared Access Policy ──────────────────────────────────────────
# Used as SASL_SSL plain credentials for Kafka clients (Username = "$ConnectionString")
resource "azurerm_eventhub_namespace_authorization_rule" "kafka_auth" {
  name                = "kafka-client-policy"
  namespace_name      = azurerm_eventhub_namespace.kafka_ns.name
  resource_group_name = azurerm_resource_group.rg.name

  listen = true
  send   = true
  manage = false
}

# ─── Azure AI Content Safety (PyRIT Red-Team Evaluator) ───────────────────────
resource "azurerm_cognitive_account" "content_safety" {
  name                = "${var.project_name}-safety-${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "ContentSafety"
  sku_name            = "S0"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Function    = "AISecurityGuardrail"
  }
}

# ─── Azure Key Vault (Secrets & SASL Token Store) ─────────────────────────────
resource "azurerm_key_vault" "kv" {
  name                       = "har-kv-${random_string.suffix.result}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge"
    ]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Store Kafka Connection String in Key Vault
resource "azurerm_key_vault_secret" "kafka_connection_string" {
  name         = "kafka-connection-string"
  value        = azurerm_eventhub_namespace_authorization_rule.kafka_auth.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

# Store AI Content Safety API Key in Key Vault
resource "azurerm_key_vault_secret" "content_safety_key" {
  name         = "content-safety-primary-key"
  value        = azurerm_cognitive_account.content_safety.primary_access_key
  key_vault_id = azurerm_key_vault.kv.id
}
