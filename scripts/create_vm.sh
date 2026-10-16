#!/usr/bin/env bash
# ==============================================================================
# 🚀 AUTOMATED COMPUTE ENGINE VM PROVISIONER & ZERO-TRUST REPO BOOTSTRAPPER
# HYBRID ANIME RECOMMENDER & AI AGENT PLATFORM
#
# Automates:
# 1. Customizable GCP Compute Engine VM creation (Machine Type, Disk, Zone, Spot/On-Demand).
# 2. Automated OS hardening and software bootstrap (Docker, Astral uv, Python, Git).
# 3. Post-boot git repository cloning directly onto the VM (/opt/Hybrid-Anime-Recommender).
# 4. Dependency sync, systemd service installation, and background app execution.
# 5. Integration with zero-trust firewall perimeter and dynamic .env IP synchronization.
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

# Default Customization Parameters
GCP_PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo 'project-53d8ce01-b0e0-4f8b-94c')}"
INSTANCE_NAME="hybrid-anime-recommender-vm"
MACHINE_TYPE="e2-standard-4"        # 4 vCPU, 16 GB RAM (Enterprise default)
ZONE="${GCP_ZONE:-us-central1-a}"
DISK_SIZE="50"                      # GB
DISK_TYPE="pd-balanced"             # Cost-effective, high IOPS SSD
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
SERVICE_ACCOUNT="${SA_EMAIL:-anime-recommender@${GCP_PROJECT}.iam.gserviceaccount.com}"
REPO_URL="https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender.git"
CLONE_DIR="/opt/Hybrid-Anime-Recommender"
TARGET_BRANCH="main"
IS_SPOT=false
AUTO_START=true
DRY_RUN=false
SYNC_FIREWALL=true

show_help() {
    cat << EOF
Usage: ./scripts/create_vm.sh [OPTIONS]

Provisions a hardened Google Cloud Compute Engine VM instance, attaches security tags,
automatically clones the Hybrid Anime Recommender repository, and starts the platform.

Customization Options:
  --name, --instance-name <NAME>    VM Instance name (default: ${INSTANCE_NAME})
  --machine-type, -m <TYPE>         GCP Machine type (default: ${MACHINE_TYPE})
                                    Options: e2-standard-2, e2-standard-4, e2-standard-8, e2-medium
  --zone, -z <ZONE>                 GCP Zone (default: ${ZONE})
  --disk-size <GB>                  Boot disk capacity in GB (default: ${DISK_SIZE})
  --disk-type <TYPE>                Boot disk type (default: ${DISK_TYPE})
                                    Options: pd-balanced, pd-ssd, pd-standard
  --image-family <FAMILY>           OS Image family (default: ${IMAGE_FAMILY})
  --image-project <PROJECT>         OS Image project (default: ${IMAGE_PROJECT})
  --spot, --preemptible             Provision as Spot VM (60-80% cost savings)
  --repo-url <URL>                  Git repository URL to clone on the VM
  --branch <BRANCH>                 Git branch to checkout (default: ${TARGET_BRANCH})
  --clone-dir <PATH>                Directory on VM where repository is placed (default: ${CLONE_DIR})
  --no-start                        Do not start the web application service automatically
  --no-firewall-sync                Skip re-verifying GCP firewall bot shield rules
  --dry-run                         Simulate the VM creation command without provisioning
  --help, -h                        Show this help message

Examples:
  # 1. Standard Production VM with automated clone & launch:
  ./scripts/create_vm.sh

  # 2. High-Performance Cost-Optimized Spot VM:
  ./scripts/create_vm.sh --machine-type e2-standard-8 --disk-size 100 --spot

  # 3. Budget lightweight development instance:
  ./scripts/create_vm.sh --machine-type e2-medium --disk-size 30 --spot
EOF
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --name|--instance-name)
            INSTANCE_NAME="$2"
            shift 2
            ;;
        --machine-type|-m)
            MACHINE_TYPE="$2"
            shift 2
            ;;
        --zone|-z)
            ZONE="$2"
            shift 2
            ;;
        --disk-size)
            DISK_SIZE="$2"
            shift 2
            ;;
        --disk-type)
            DISK_TYPE="$2"
            shift 2
            ;;
        --image-family)
            IMAGE_FAMILY="$2"
            shift 2
            ;;
        --image-project)
            IMAGE_PROJECT="$2"
            shift 2
            ;;
        --spot|--preemptible)
            IS_SPOT=true
            shift
            ;;
        --repo-url)
            REPO_URL="$2"
            shift 2
            ;;
        --branch)
            TARGET_BRANCH="$2"
            shift 2
            ;;
        --clone-dir)
            CLONE_DIR="$2"
            shift 2
            ;;
        --no-start)
            AUTO_START=false
            shift
            ;;
        --no-firewall-sync)
            SYNC_FIREWALL=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
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
  🚀 COMPUTE ENGINE VM PROVISIONER & AUTOMATED REPO CLONER
================================================================================
EOF
echo -e "${NC}"

echo -e "Instance Customization Specification:"
echo -e "  Instance Name    : ${BOLD}${INSTANCE_NAME}${NC}"
echo -e "  GCP Project ID   : ${BOLD}${GCP_PROJECT}${NC}"
echo -e "  Machine Type     : ${BOLD}${MACHINE_TYPE}${NC}"
echo -e "  Zone             : ${BOLD}${ZONE}${NC}"
echo -e "  Disk             : ${BOLD}${DISK_SIZE} GB (${DISK_TYPE})${NC}"
echo -e "  OS Image         : ${BOLD}${IMAGE_FAMILY} (${IMAGE_PROJECT})${NC}"
echo -e "  Provisioning Mode: $([ "$IS_SPOT" = true ] && echo -e "${YELLOW}${BOLD}Spot / Preemptible (Discounted)${NC}" || echo -e "${GREEN}${BOLD}Standard On-Demand${NC}")"
echo -e "  Service Account  : ${BOLD}${SERVICE_ACCOUNT}${NC}"
echo -e "  Repo to Clone    : ${GREEN}${BOLD}${REPO_URL} (${TARGET_BRANCH})${NC}"
echo -e "  VM Target Path   : ${BOLD}${CLONE_DIR}${NC}\n"

# Verify Service Account exists or fallback to Compute Engine default
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$GCP_PROJECT" >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Configured SA '${SERVICE_ACCOUNT}' not found in project. Using default compute service account.${NC}"
    SERVICE_ACCOUNT=""
fi

# Prepare Startup Script
STARTUP_SCRIPT=$(cat << STARTUP_EOF
#!/usr/bin/env bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "[+] Log start: $(date)" >> /var/log/startup-script.log

# 1. Update OS and install essential packages
echo "[*] Updating apt packages..." >> /var/log/startup-script.log
apt-get update -y
apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    git \
    jq \
    ufw \
    build-essential \
    python3-pip \
    python3-venv \
    tar >> /var/log/startup-script.log 2>&1

# 2. Install Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "[*] Installing Docker Engine..." >> /var/log/startup-script.log
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo "\$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >> /var/log/startup-script.log 2>&1
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu 2>/dev/null || true
fi

# 3. Install Astral uv (high-performance Python manager)
echo "[*] Installing Astral uv package manager..." >> /var/log/startup-script.log
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh >> /var/log/startup-script.log 2>&1
export PATH="/usr/local/bin:\$PATH"

# 4. Clone Repository
echo "[*] Cloning repository ${REPO_URL} into ${CLONE_DIR}..." >> /var/log/startup-script.log
if [ ! -d "${CLONE_DIR}" ]; then
    git clone -b "${TARGET_BRANCH}" "${REPO_URL}" "${CLONE_DIR}" >> /var/log/startup-script.log 2>&1
else
    git -C "${CLONE_DIR}" fetch --all >> /var/log/startup-script.log 2>&1
    git -C "${CLONE_DIR}" checkout "${TARGET_BRANCH}" >> /var/log/startup-script.log 2>&1
    git -C "${CLONE_DIR}" pull origin "${TARGET_BRANCH}" >> /var/log/startup-script.log 2>&1
fi

cd "${CLONE_DIR}"
chmod +x deploy.sh clear.sh scripts/*.sh 2>/dev/null || true

# 5. Bootstrap Environment
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
fi
sed -i 's/^PORT=.*/PORT=5000/' .env 2>/dev/null || echo "PORT=5000" >> .env

# 6. Synchronize Python virtual environment
echo "[*] Syncing Python dependencies with uv..." >> /var/log/startup-script.log
uv sync >> /var/log/startup-script.log 2>&1

# 7. Setup Systemd Service for continuous execution
cat << 'SERVICE_CONF' > /etc/systemd/system/anime-recommender.service
[Unit]
Description=Hybrid Anime Recommender & AI Agent Platform
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=${CLONE_DIR}
EnvironmentFile=-${CLONE_DIR}/.env
ExecStart=/usr/local/bin/uv run python application.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_CONF

systemctl daemon-reload
systemctl enable anime-recommender.service
if [ "${AUTO_START}" = "true" ]; then
    echo "[*] Starting anime-recommender systemd service..." >> /var/log/startup-script.log
    systemctl restart anime-recommender.service
fi

echo "[✓] VM Initialization complete at: \$(date)" >> /var/log/startup-script.log
STARTUP_EOF
)

# Build GCP gcloud command
GCLOUD_CMD=(
    gcloud compute instances create "$INSTANCE_NAME"
    --project="$GCP_PROJECT"
    --zone="$ZONE"
    --machine-type="$MACHINE_TYPE"
    --boot-disk-size="${DISK_SIZE}GB"
    --boot-disk-type="$DISK_TYPE"
    --image-family="$IMAGE_FAMILY"
    --image-project="$IMAGE_PROJECT"
    --tags="hybrid-anime-recommender,http-server,https-server,devops-platform"
    --scopes="cloud-platform"
    --metadata="startup-script=${STARTUP_SCRIPT}"
)

if [ -n "$SERVICE_ACCOUNT" ]; then
    GCLOUD_CMD+=(--service-account="$SERVICE_ACCOUNT")
fi

if [ "$IS_SPOT" = true ]; then
    GCLOUD_CMD+=(--provisioning-model=SPOT --instance-termination-action=STOP)
fi

# Handle Dry Run
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[*] DRY RUN: Would execute the following gcloud command:${NC}\n"
    printf '%q ' "${GCLOUD_CMD[@]}"
    echo -e "\n\n${GREEN}[✓] Dry run finished.${NC}"
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# 1. CHECK IF INSTANCE ALREADY EXISTS
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${CYAN}[1/4] Checking instance status...${NC}"
if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$GCP_PROJECT" >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] VM Instance '${INSTANCE_NAME}' already exists.${NC}"
    STATUS=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$GCP_PROJECT" --format="value(status)")
    echo -e "    Current Status: ${BOLD}${STATUS}${NC}"
    if [ "$STATUS" = "TERMINATED" ] || [ "$STATUS" = "STOPPED" ]; then
        echo -e "${CYAN}[*] Starting existing stopped VM instance...${NC}"
        gcloud compute instances start "$INSTANCE_NAME" --zone="$ZONE" --project="$GCP_PROJECT"
    fi
else
    # ──────────────────────────────────────────────────────────────────────────
    # 2. CREATE THE VM INSTANCE
    # ──────────────────────────────────────────────────────────────────────────
    echo -e "${CYAN}[2/4] Provisioning Compute Engine VM on Google Cloud...${NC}"
    "${GCLOUD_CMD[@]}"
    echo -e "${GREEN}[✓] Instance '${INSTANCE_NAME}' created successfully.${NC}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3. RETRIEVE PUBLIC IP & REFRESH CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}[3/4] Fetching VM network interfaces and public IP...${NC}"

# Wait up to 30s for IP assignment
for i in {1..10}; do
    EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$GCP_PROJECT" \
        --format="get(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null || echo "")
    if [ -n "$EXTERNAL_IP" ]; then
        break
    fi
    sleep 3
done

if [ -z "$EXTERNAL_IP" ]; then
    echo -e "${RED}[ERROR] Could not resolve public IP address for '${INSTANCE_NAME}'.${NC}"
    exit 1
fi

echo -e "  Assigned External IP: ${GREEN}${BOLD}${EXTERNAL_IP}${NC}"

# Update .env in local workspace
if [ -f "${ROOT_DIR}/.env" ]; then
    if grep -q "^SERVER_PUBLIC_IP=" "${ROOT_DIR}/.env"; then
        sed -i.bak "s|^SERVER_PUBLIC_IP=.*|SERVER_PUBLIC_IP=\"${EXTERNAL_IP}\"|" "${ROOT_DIR}/.env" 2>/dev/null || true
    else
        echo "SERVER_PUBLIC_IP=\"${EXTERNAL_IP}\"" >> "${ROOT_DIR}/.env"
    fi
    echo -e "${GREEN}[✓] Updated SERVER_PUBLIC_IP in .env to ${EXTERNAL_IP}.${NC}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 4. VERIFY / SYNC FIREWALL BOT SHIELD
# ──────────────────────────────────────────────────────────────────────────────
if [ "$SYNC_FIREWALL" = true ]; then
    echo -e "\n${CYAN}[4/4] Verifying VPC Firewall Shield for VM instance...${NC}"
    if [ -x "${SCRIPT_DIR}/secure_firewall.sh" ]; then
        "${SCRIPT_DIR}/secure_firewall.sh" --apply
    fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY & SERVICE ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}"
cat << "EOF"
================================================================================
🎉 COMPUTE ENGINE VM CREATED & REPOSITORY INITIALIZED!
================================================================================
EOF
echo -e "${NC}"

echo -e "VM Instance Details:"
echo -e "  Instance Name    : ${BOLD}${INSTANCE_NAME}${NC}"
echo -e "  Zone             : ${BOLD}${ZONE}${NC}"
echo -e "  Machine Type     : ${BOLD}${MACHINE_TYPE}${NC}"
echo -e "  Public IPv4      : ${GREEN}${BOLD}${EXTERNAL_IP}${NC}"
echo -e "  Repo Cloned Path : ${BOLD}${CLONE_DIR}${NC}\n"

echo -e "Secure Access Commands:"
echo -e "  • ${BOLD}SSH via Google Cloud IAP Tunnel (Zero bot access):${NC}"
echo -e "    ${CYAN}gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --tunnel-through-iap${NC}"
echo -e "  • ${BOLD}View live VM startup & clone logs:${NC}"
echo -e "    ${CYAN}gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --command='tail -f /var/log/startup-script.log'${NC}"
echo -e "  • ${BOLD}Check systemd app status on VM:${NC}"
echo -e "    ${CYAN}gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --command='systemctl status anime-recommender'${NC}\n"

echo -e "Live Service Endpoints (Protected by VPC Bot Shield):"
echo -e "  🌐 Web UI & Recommender API : ${BOLD}http://${EXTERNAL_IP}:5000${NC}"
echo -e "  🩺 Healthcheck Endpoint     : ${BOLD}http://${EXTERNAL_IP}:5000/health${NC}"
echo -e "  📊 Prometheus Telemetry     : ${BOLD}http://${EXTERNAL_IP}:5000/metrics${NC}"
echo -e "  ⚡ Redis Cache Stats        : ${BOLD}http://${EXTERNAL_IP}:5000/api/cache/stats${NC}\n"

echo -e "${GREEN}[✓] VM instance is fully operational and accessible end-to-end!${NC}\n"
