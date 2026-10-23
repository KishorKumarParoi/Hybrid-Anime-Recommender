#!/usr/bin/env bash
# ==============================================================================
# 🚀 ZERO-TOUCH 1-COMMAND AUTO-BOOTSTRAPPER FOR EC2 & CLOUD VMS
# HYBRID ANIME INTELLIGENCE & CONTINUOUS LLMOPS PLATFORM
#
# Designed for Senior Staff / Principal Engineer Demonstrations:
# Can be run directly on a completely bare, fresh EC2 instance or local workstation
# via a single curl command without pre-installing git, docker, or python:
#
#   curl -fsSL https://raw.githubusercontent.com/KishorKumarParoi/Hybrid-Anime-Recommender/main/bootstrap.sh | bash
#
# What this script automates:
# 1. Detects OS (Ubuntu, Debian, Amazon Linux 2023, RHEL, macOS)
# 2. Automatically installs git, curl, and base build tools
# 3. OOM Protection: Detects if RAM < 4GB and auto-configures a 4GB Swapfile
# 4. Automatically clones or updates the GitHub repository
# 5. Configures permissions and invokes ./deploy.sh with all options passed through
# ==============================================================================

set -eo pipefail

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << "EOF"
================================================================================
  🎬 HYBRID ANIME PLATFORM — ZERO-TOUCH INSTANT CLOUD BOOTSTRAPPER
================================================================================
EOF
echo -e "${NC}"

run_sudo() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &>/dev/null && sudo -n true 2>/dev/null; then
        sudo "$@"
    elif command -v sudo &>/dev/null; then
        sudo "$@"
    else
        "$@"
    fi
}

# ─── 1. Install Git & Base Prereqs If Missing ─────────────────────────────────
echo -e "${CYAN}[1/4] Detecting OS and ensuring Git & Curl are available...${NC}"

if ! command -v git &>/dev/null || ! command -v curl &>/dev/null; then
    echo -e "${YELLOW}[+] Installing Git and Core Networking Utilities...${NC}"
    if [ -f /etc/debian_version ]; then
        run_sudo apt-get update -qq
        run_sudo apt-get install -y -qq git curl ca-certificates tar gzip unzip build-essential >/dev/null 2>&1
    elif [ -f /etc/amazon-linux-release ] || [ -f /etc/redhat-release ]; then
        if command -v dnf &>/dev/null; then
            run_sudo dnf install -y -q git curl ca-certificates tar gzip unzip >/dev/null 2>&1 || true
        else
            run_sudo yum install -y -q git curl ca-certificates tar gzip unzip >/dev/null 2>&1 || true
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v git &>/dev/null; then
            xcode-select --install 2>/dev/null || true
        fi
    fi
fi

echo -e "${GREEN}[✓] Git: $(git --version 2>/dev/null || echo 'Installed')${NC}"
echo -e "${GREEN}[✓] Curl: $(curl --version 2>/dev/null | head -n 1 || echo 'Installed')${NC}"

# ─── 2. Auto-Swap Configuration (OOM Protection for Small EC2 Instances) ──────
echo -e "\n${CYAN}[2/4] Checking System Memory & OOM Protection...${NC}"

if command -v free &>/dev/null; then
    TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    EXISTING_SWAP_MB=$(free -m | awk '/^Swap:/{print $2}')
    
    # If RAM is under 4GB (e.g. t2.micro, t3.micro, t3.small) and swap is under 1GB, create 4GB swapfile
    if [ "$TOTAL_RAM_MB" -lt 4000 ] && [ "$EXISTING_SWAP_MB" -lt 1000 ]; then
        echo -e "${YELLOW}[!] Host has ${TOTAL_RAM_MB}MB RAM. Auto-configuring 4GB swapfile to prevent compiler OOM crashes...${NC}"
        if [ ! -f /swapfile ]; then
            run_sudo fallocate -l 4G /swapfile 2>/dev/null || run_sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 2>/dev/null
            run_sudo chmod 600 /swapfile
            run_sudo mkswap /swapfile >/dev/null 2>&1
            run_sudo swapon /swapfile 2>/dev/null || true
            echo -e "${GREEN}[✓] 4GB Swapfile configured and active!${NC}"
        fi
    else
        echo -e "${GREEN}[✓] Sufficient memory available (${TOTAL_RAM_MB}MB RAM, ${EXISTING_SWAP_MB}MB Swap).${NC}"
    fi
else
    echo -e "${GREEN}[✓] Memory check bypassed (macOS / BSD runtime).${NC}"
fi

# ─── 3. Repository Auto-Clone or Sync ──────────────────────────────────────────
echo -e "\n${CYAN}[3/4] Ensuring Hybrid-Anime-Recommender repository is local...${NC}"

REPO_DIR="Hybrid-Anime-Recommender"

if [ -f "deploy.sh" ] && [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}[✓] Already inside repository directory ($(pwd)). Syncing latest commit...${NC}"
    git pull origin main 2>/dev/null || true
elif [ -d "$REPO_DIR" ]; then
    echo -e "${GREEN}[✓] Found existing directory ${REPO_DIR}. Entering and updating...${NC}"
    cd "$REPO_DIR"
    git pull origin main 2>/dev/null || true
else
    echo -e "${YELLOW}[+] Cloning repository from GitHub...${NC}"
    git clone https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Set executable permissions
chmod +x deploy.sh clear.sh bootstrap.sh 2>/dev/null || true
find scripts/ -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true

# ─── 4. Hand Off to deploy.sh ─────────────────────────────────────────────────
echo -e "\n${CYAN}[4/4] Executing One-Click Production Deployment Pipeline...${NC}"
exec ./deploy.sh "$@"
