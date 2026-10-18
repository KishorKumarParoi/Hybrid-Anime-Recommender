# ─── Cloud Armor Security Policy (WAF & Threat Defense) ──────────────────────
# Inspired by 190 - AI SECURITY PROJECT MATERIALS guardrails & injection defense

resource "google_compute_security_policy" "anime_cloud_armor" {
  name        = "${var.cluster_name}-cloud-armor"
  description = "Enterprise WAF and injection defense security policy for Hybrid Anime Recommender"

  # Rule 1: Mitigate SQL Injection (OWASP Top 10)
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block SQL injection attempts across query strings and headers"
  }

  # Rule 2: Mitigate Cross-Site Scripting (XSS)
  rule {
    action   = "deny(403)"
    priority = "1010"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block cross-site scripting attempts"
  }

  # Rule 3: Mitigate Local/Remote File Inclusion (LFI/RFI)
  rule {
    action   = "deny(403)"
    priority = "1020"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('lfi-v33-stable') || evaluatePreconfiguredExpr('rfi-v33-stable')"
      }
    }
    description = "Block local and remote file inclusion attempts"
  }

  # Rule 4: Protocol Attack & Scanner Defense
  rule {
    action   = "deny(403)"
    priority = "1030"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('scannerdetection-v33-stable') || evaluatePreconfiguredExpr('protocolattack-v33-stable')"
      }
    }
    description = "Block automated vulnerability scanners and protocol attacks"
  }

  # Rule 5: Rate Limiting & DoS Defense on LLM Inference endpoints
  rule {
    action   = "throttle"
    priority = "2000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 120
        interval_sec = 60
      }
    }
    description = "Rate limit traffic to 120 requests per minute per IP"
  }

  # Default rule: Allow legitimate traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule for benign user traffic"
  }
}

# ─── Secret Manager (Enterprise App & AI Agent Configuration) ─────────────────
# Inspired by 190 - AI SECURITY PROJECT MATERIALS secrets manager configuration

resource "google_secret_manager_secret" "app_config" {
  secret_id = "hybrid-anime-recommender-config"

  replication {
    auto {}
  }

  labels = local.common_labels
}

resource "google_secret_manager_secret_version" "app_config_version" {
  secret = google_secret_manager_secret.app_config.id

  secret_data = jsonencode({
    GROQ_API_KEY               = var.groq_api_key
    API_KEY                    = var.api_key
    CACHE_SIMILARITY_THRESHOLD = "0.85"
    CACHE_TTL                  = "3600"
    LLM_MAX_RETRIES            = "3"
    LLM_RETRY_DELAY            = "1.0"
    AGENT_MAX_ITERATIONS       = "2"
    ENVIRONMENT                = var.environment
    GCP_PROJECT                = var.gcp_project_id
    GCP_REGION                 = var.gcp_region
  })
}

# ─── Cloud Scheduler (Weekly Automated Red Teaming Security Audit) ────────────
# Inspired by 190 - AI SECURITY PROJECT MATERIALS EventBridge weekly red team rule

resource "google_cloud_scheduler_job" "weekly_security_audit" {
  name             = "${var.cluster_name}-weekly-redteam"
  description      = "Trigger weekly automated AI security and prompt injection audit on Monday 02:00 AM UTC"
  schedule         = "0 2 * * 1"
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "http://anime-rec-service.default.svc.cluster.local:80/api/security/audit"

    headers = {
      "Content-Type" = "application/json"
      "User-Agent"   = "Google-Cloud-Scheduler-RedTeam-Audit"
    }

    body = base64encode(jsonencode({
      trigger    = "automated_weekly_redteam"
      suite      = "prompt_injection_and_pii"
      confidence = "high"
    }))
  }
}
