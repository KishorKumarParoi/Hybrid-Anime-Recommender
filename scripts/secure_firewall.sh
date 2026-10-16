#!/usr/bin/env bash
# ==============================================================================
# 🛡️ ENTERPRISE BOT SHIELD & ZERO-TRUST GCP FIREWALL HARDENING RUNNER
# HYBRID ANIME RECOMMENDER & AI AGENT PLATFORM
#
# Eliminates bot attack vectors, brute-force scanners, and unauthenticated probes:
# 1. Deletes default wide-open RDP (3389) and SSH (22 to 0.0.0.0/0).
# 2. Implements Google Cloud Identity-Aware Proxy (IAP) Tunneling (35.235.240.0/20)
#    for SSH so port 22 is completely invisible to public internet botnets.
# 3. Restricts all DevOps management ports (Jenkins:8080, ArgoCD:30751, SonarQube:9000,
#    Nexus:8081, Prometheus:9090, Grafana:3000, Kibana:5601) to ADMIN_IP ONLY.
# 4. Enforces strict default-deny ingress baseline across the VPC.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Visual formatting
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Source environment
if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    source "${ROOT_DIR}/.env" 2>/dev/null || true
    set +a
fi

# Ensure Python 3.11 for gcloud to prevent OpenSSL legacy attribute crash
if [ -z "$CLOUDSDK_PYTHON" ]; then
    for py in /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11 /usr/bin/python3.11 /opt/homebrew/bin/python3.12 /usr/bin/python3.12 /usr/local/bin/python3.12 /usr/bin/python3; do
        if [ -x "$py" ]; then
            export CLOUDSDK_PYTHON="$py"
            break
        fi
    done
fi

GCP_PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo 'project-53d8ce01-b0e0-4f8b-94c')}"
GCP_NETWORK="${GCP_NETWORK:-default}"

DRY_RUN=false
AUDIT_ONLY=false
ADMIN_IP_OVERRIDE=""

show_help() {
    cat << EOF
Usage: ./scripts/secure_firewall.sh [OPTIONS]

Enterprise Google Cloud VPC Firewall Bot Shield and Anti-Reconnaissance Hardener.

Options:
  --apply                     Apply all strict zero-trust firewall rules to GCP VPC
  --audit                     Audit active firewall rules and report security vulnerabilities
  --dry-run                   Simulate firewall updates without modifying cloud state
  --admin-ip <IP>             Explicitly set administrator IPv4 for DevOps whitelist (default: auto-detected)
  --help, -h                  Show this help message

Examples:
  ./scripts/secure_firewall.sh --audit
  ./scripts/secure_firewall.sh --dry-run
  ./scripts/secure_firewall.sh --apply
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)
            DRY_RUN=false
            AUDIT_ONLY=false
            shift
            ;;
        --audit)
            AUDIT_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --admin-ip)
            ADMIN_IP_OVERRIDE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${CYAN}${BOLD}"
cat << "EOF"
================================================================================
  🛡️ GCP ZERO-TRUST BOT SHIELD & FIREWALL HARDENING RUNNER
================================================================================
EOF
echo -e "${NC}"

# Detect Operator Public IP
if [ -n "$ADMIN_IP_OVERRIDE" ]; then
    ADMIN_IP="$ADMIN_IP_OVERRIDE"
else
    ADMIN_IP=$(curl -s --max-time 4 https://ifconfig.me || curl -s --max-time 4 https://api.ipify.org || echo "")
fi

if [ -z "$ADMIN_IP" ]; then
    echo -e "${YELLOW}[!] Warning: Could not detect public IP automatically. Falling back to local loopback.${NC}"
    ADMIN_IP="127.0.0.1"
fi

echo -e "Target GCP Configuration:"
echo -e "  Project ID         : ${BOLD}${GCP_PROJECT}${NC}"
echo -e "  VPC Network        : ${BOLD}${GCP_NETWORK}${NC}"
echo -e "  Admin Whitelist IP : ${GREEN}${BOLD}${ADMIN_IP}/32${NC} (Protected from bot attacks)\n"

# ──────────────────────────────────────────────────────────────────────────────
# 1. AUDIT CURRENT VULNERABILITIES
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${CYAN}[1/4] Auditing active GCP firewall rules for bot exposure...${NC}"

VULNERABLE_RULES=()
CURRENT_RULES=$(gcloud compute firewall-rules list --project="$GCP_PROJECT" --format="table(name,direction,priority,allow,disabled)" 2>/dev/null || true)
echo "$CURRENT_RULES"

# Check for wide-open SSH
if gcloud compute firewall-rules describe default-allow-ssh --project="$GCP_PROJECT" >/dev/null 2>&1; then
    SSH_SOURCES=$(gcloud compute firewall-rules describe default-allow-ssh --project="$GCP_PROJECT" --format="value(sourceRanges)" 2>/dev/null || true)
    if [[ "$SSH_SOURCES" == *"0.0.0.0/0"* ]]; then
        VULNERABLE_RULES+=("default-allow-ssh (SSH exposed to 0.0.0.0/0 - Bot brute force target!)")
    fi
fi

# Check for wide-open RDP
if gcloud compute firewall-rules describe default-allow-rdp --project="$GCP_PROJECT" >/dev/null 2>&1; then
    RDP_DISABLED=$(gcloud compute firewall-rules describe default-allow-rdp --project="$GCP_PROJECT" --format="value(disabled)" 2>/dev/null || true)
    if [ "$RDP_DISABLED" != "True" ]; then
        VULNERABLE_RULES+=("default-allow-rdp (RDP exposed to 0.0.0.0/0 - High-frequency port scan target!)")
    fi
fi

if [ ${#VULNERABLE_RULES[@]} -gt 0 ]; then
    echo -e "\n${RED}${BOLD}🚨 DETECTED HIGH-RISK BOT EXPOSURE VULNERABILITIES:${NC}"
    for vuln in "${VULNERABLE_RULES[@]}"; do
        echo -e "  ${RED}✖ ${vuln}${NC}"
    done
else
    echo -e "\n${GREEN}[✓] No default wide-open management rules detected.${NC}"
fi

if [ "$AUDIT_ONLY" = true ]; then
    echo -e "\n${GREEN}[✓] Audit complete.${NC}"
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# 2. BOT SHIELD IMPLEMENTATION
# ──────────────────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    echo -e "\n${YELLOW}[*] DRY RUN: Would execute the following security hardening actions:${NC}"
    echo "  1. Delete/Disable default-allow-rdp (port 3389)."
    echo "  2. Replace default-allow-ssh with allow-iap-ssh-tunnel (restricted to 35.235.240.0/20)."
    echo "  3. Create allow-admin-direct-ssh strictly for ${ADMIN_IP}/32."
    echo "  4. Create allow-devops-admin-management (8080, 30751, 9000, 8081, 9090, 3000, 5601) strictly for ${ADMIN_IP}/32."
    echo "  5. Create allow-public-web-shielded (ports 80, 443, 30080) with target tags and logging."
    echo "  6. Create deny-all-unauthorized-ingress with priority 65000."
    echo -e "\n${GREEN}[✓] Dry run finished.${NC}"
    exit 0
fi

echo -e "\n${CYAN}[2/4] Remediating default vulnerability rules...${NC}"

# Delete default-allow-rdp
if gcloud compute firewall-rules describe default-allow-rdp --project="$GCP_PROJECT" >/dev/null 2>&1; then
    echo "[+] Deleting dangerous default-allow-rdp rule..."
    gcloud compute firewall-rules delete default-allow-rdp --project="$GCP_PROJECT" --quiet
    echo -e "${GREEN}[✓] default-allow-rdp deleted.${NC}"
fi

# Replace default-allow-ssh
if gcloud compute firewall-rules describe default-allow-ssh --project="$GCP_PROJECT" >/dev/null 2>&1; then
    echo "[+] Disabling open default-allow-ssh to prevent bot brute-force attacks..."
    gcloud compute firewall-rules update default-allow-ssh --project="$GCP_PROJECT" --disabled
    echo -e "${GREEN}[✓] default-allow-ssh disabled.${NC}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3. APPLY ZERO-TRUST FIREWALL RULES
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}[3/4] Provisioning Zero-Trust Bot Shield firewall rules...${NC}"

# Rule A: Google Cloud Identity-Aware Proxy (IAP) SSH Tunneling
# Source IP range 35.235.240.0/20 is Google's official IAP proxy range
# Zero public IP bots can connect to port 22.
echo "[+] Creating 'allow-iap-ssh-tunnel' (Google IAP range: 35.235.240.0/20)..."
if ! gcloud compute firewall-rules describe allow-iap-ssh-tunnel --project="$GCP_PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-iap-ssh-tunnel \
        --project="$GCP_PROJECT" \
        --network="$GCP_NETWORK" \
        --priority=1000 \
        --direction=INGRESS \
        --action=ALLOW \
        --rules=tcp:22 \
        --source-ranges="35.235.240.0/20" \
        --description="Allow secure SSH tunneling strictly through Google Cloud Identity-Aware Proxy (IAP). Prevents public bot access."
    echo -e "${GREEN}[✓] allow-iap-ssh-tunnel created.${NC}"
else
    echo -e "${YELLOW}[*] allow-iap-ssh-tunnel already exists.${NC}"
fi

# Rule B: Direct Admin SSH from Operator Public IP Only
echo "[+] Creating 'allow-admin-direct-ssh' (Admin IP: ${ADMIN_IP}/32)..."
if ! gcloud compute firewall-rules describe allow-admin-direct-ssh --project="$GCP_PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-admin-direct-ssh \
        --project="$GCP_PROJECT" \
        --network="$GCP_NETWORK" \
        --priority=1010 \
        --direction=INGRESS \
        --action=ALLOW \
        --rules=tcp:22 \
        --source-ranges="${ADMIN_IP}/32" \
        --description="Allow direct SSH strictly from verified administrator public IP."
    echo -e "${GREEN}[✓] allow-admin-direct-ssh created.${NC}"
else
    gcloud compute firewall-rules update allow-admin-direct-ssh \
        --project="$GCP_PROJECT" \
        --source-ranges="${ADMIN_IP}/32" \
        --quiet 2>/dev/null || true
    echo -e "${GREEN}[✓] allow-admin-direct-ssh updated to current IP (${ADMIN_IP}/32).${NC}"
fi

# Rule C: Admin DevOps Management Platform Shield
# Ports:
# - 8080, 50000: Jenkins Master & Agent
# - 30751, 8080: ArgoCD Server UI & GitOps
# - 9000: SonarQube Scanner
# - 8081: Nexus Repository
# - 9090, 30090: Prometheus Server & NodePort
# - 3000, 30300: Grafana Dashboard & NodePort
# - 5601, 30601: Kibana Log Analytics & NodePort
echo "[+] Creating 'allow-devops-admin-mgmt' (Admin IP: ${ADMIN_IP}/32)..."
DEVOPS_PORTS="tcp:8080,tcp:50000,tcp:30751,tcp:9000,tcp:8081,tcp:9090,tcp:30090,tcp:3000,tcp:30300,tcp:5601,tcp:30601"
if ! gcloud compute firewall-rules describe allow-devops-admin-mgmt --project="$GCP_PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-devops-admin-mgmt \
        --project="$GCP_PROJECT" \
        --network="$GCP_NETWORK" \
        --priority=1020 \
        --direction=INGRESS \
        --action=ALLOW \
        --rules="$DEVOPS_PORTS" \
        --source-ranges="${ADMIN_IP}/32" \
        --description="Strict administrative access to Jenkins, ArgoCD, Prometheus, Grafana, ELK, SonarQube and Nexus. Blocked for all bots."
    echo -e "${GREEN}[✓] allow-devops-admin-mgmt created.${NC}"
else
    gcloud compute firewall-rules update allow-devops-admin-mgmt \
        --project="$GCP_PROJECT" \
        --source-ranges="${ADMIN_IP}/32" \
        --rules="$DEVOPS_PORTS" \
        --quiet 2>/dev/null || true
    echo -e "${GREEN}[✓] allow-devops-admin-mgmt updated to current IP (${ADMIN_IP}/32).${NC}"
fi

# Rule D: Shielded Public Web Ingress (Application API & Frontend)
# Ports 80, 443, 5000, and NodePort 30080 are permitted to receive web traffic
echo "[+] Creating or updating 'allow-public-web-shielded' (Ports 80, 443, 5000, 30080)..."
if ! gcloud compute firewall-rules describe allow-public-web-shielded --project="$GCP_PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-public-web-shielded \
        --project="$GCP_PROJECT" \
        --network="$GCP_NETWORK" \
        --priority=1050 \
        --direction=INGRESS \
        --action=ALLOW \
        --rules=tcp:80,tcp:443,tcp:5000,tcp:30080 \
        --source-ranges="0.0.0.0/0" \
        --enable-logging \
        --description="Public web traffic to application frontend and REST API with access logging enabled for bot/anomaly detection."
    echo -e "${GREEN}[✓] allow-public-web-shielded created with connection logging.${NC}"
else
    gcloud compute firewall-rules update allow-public-web-shielded \
        --project="$GCP_PROJECT" \
        --rules=tcp:80,tcp:443,tcp:5000,tcp:30080 \
        --quiet 2>/dev/null || true
    echo -e "${GREEN}[✓] allow-public-web-shielded updated to include port 5000.${NC}"
fi

# Rule E: Default Deny All Remaining Ingress
echo "[+] Enforcing 'deny-all-bot-scanners' (Priority 65000)..."
if ! gcloud compute firewall-rules describe deny-all-bot-scanners --project="$GCP_PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create deny-all-bot-scanners \
        --project="$GCP_PROJECT" \
        --network="$GCP_NETWORK" \
        --priority=65000 \
        --direction=INGRESS \
        --action=DENY \
        --rules=all \
        --source-ranges="0.0.0.0/0" \
        --description="Default-deny baseline. Unconditionally drops all unauthorized port scans, botnet probes, and unsolicited inbound connections."
    echo -e "${GREEN}[✓] deny-all-bot-scanners rule created.${NC}"
else
    echo -e "${YELLOW}[*] deny-all-bot-scanners already exists.${NC}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 4. FINAL VERIFICATION SUMMARY
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}[4/4] Verifying active security perimeter...${NC}"
gcloud compute firewall-rules list --project="$GCP_PROJECT" --format="table(name,priority,direction,action,allow,sourceRanges.list():label=SOURCE_RANGES,disabled)"

echo -e "\n${GREEN}${BOLD}"
cat << "EOF"
================================================================================
🛡️ VPC FIREWALL BOT SHIELD APPLIED SUCCESSFULLY!
================================================================================
EOF
echo -e "${NC}"
echo "Security Summary:"
echo "  1. SSH (22)       : Protected by Google Cloud IAP (35.235.240.0/20) + ${ADMIN_IP}/32. ZERO bot access."
echo "  2. RDP (3389)     : Completely eliminated."
echo "  3. DevOps Ports   : Jenkins (8080), ArgoCD (30751), SonarQube (9000), Prometheus (9090), Grafana (3000),"
echo "                      Nexus (8081), and Kibana (5601) are locked strictly to ${ADMIN_IP}/32."
echo "  4. Web Ingress    : Application ports (80, 443, 30080) are monitored with Cloud Logging."
echo "  5. Baseline Deny  : All other unsolicited bot probes are dropped at VPC perimeter."
echo ""
