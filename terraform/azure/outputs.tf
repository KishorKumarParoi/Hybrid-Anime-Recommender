# ==============================================================================
# AZURE EVENT HUBS (KAFKA STREAMING) & AI SECURITY - OUTPUTS
# ==============================================================================

output "resource_group_name" {
  description = "Resource group hosting all Azure streaming and security assets"
  value       = azurerm_resource_group.rg.name
}

output "eventhub_namespace_name" {
  description = "Azure Event Hubs Namespace name"
  value       = azurerm_eventhub_namespace.kafka_ns.name
}

output "kafka_bootstrap_servers" {
  description = "Kafka compatible bootstrap servers endpoint for aiokafka / confluent-kafka"
  value       = "${azurerm_eventhub_namespace.kafka_ns.name}.servicebus.windows.net:9093"
}

output "kafka_sasl_username" {
  description = "SASL PLAIN username required by Azure Event Hubs Kafka endpoint"
  value       = "$ConnectionString"
}

output "kafka_primary_connection_string" {
  description = "Event Hubs Kafka SASL PLAIN password / connection string"
  value       = azurerm_eventhub_namespace_authorization_rule.kafka_auth.primary_connection_string
  sensitive   = true
}

output "topic_anime_interactions" {
  description = "Kafka Topic name for real-time user ratings and interactions"
  value       = azurerm_eventhub.interactions_stream.name
}

output "topic_security_audit" {
  description = "Kafka Topic name for PyRIT red-teaming and security audit logs"
  value       = azurerm_eventhub.security_audit_stream.name
}

output "topic_agent_research" {
  description = "Kafka Topic name for autonomous agent research and dossier events"
  value       = azurerm_eventhub.research_stream.name
}

output "azure_content_safety_endpoint" {
  description = "Azure AI Content Safety REST endpoint for PyRIT evaluation"
  value       = azurerm_cognitive_account.content_safety.endpoint
}

output "azure_content_safety_key" {
  description = "Azure AI Content Safety primary access key"
  value       = azurerm_cognitive_account.content_safety.primary_access_key
  sensitive   = true
}

output "key_vault_uri" {
  description = "Azure Key Vault URI holding all secrets"
  value       = azurerm_key_vault.kv.vault_uri
}
