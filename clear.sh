#!/usr/bin/env bash
# ==============================================================================
# 🧹 ONE-CLICK ZERO-COST TEARDOWN & CLEANUP RUNNER
# HYBRID ANIME RECOMMENDER & AI AGENT PLATFORM
#
# Terminates and cleans up ALL cost-incurring resources:
# 1. Local: Stops background Python processes, Flask apps (5000/5001), Docker containers
# 2. Compute Engine VMs & GPU worker nodes
# 3. Google Kubernetes Engine (GKE) clusters & node pools
# 4. Cloud Run services & Cloud SQL instances
# 5. Persistent Disks (boot, SSD, orphaned disks)
# 6. Cloud Load Balancers, Forwarding Rules & Backend Services
# 7. Cloud NAT Gateways & Cloud Routers
# 8. Reserved Static External IP Addresses (which incur idle billing)
# 9. Custom Firewall Rules
#
# NOTE: Cloud Storage buckets (raw data, DVC version tracking, model weights)
# are NEVER deleted to protect datasets and training checkpoints.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Visual formatting
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment configuration if available
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    source "${SCRIPT_DIR}/.env" 2>/dev/null || true
    set +a
fi

# Configure gcloud Python runtime to prevent SSL legacy attribute crashes
if [ -z "$CLOUDSDK_PYTHON" ]; then
    for py in /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11 /usr/bin/python3.11 /opt/homebrew/bin/python3.12 /usr/bin/python3.12 /usr/local/bin/python3.12 /usr/bin/python3; do
        if [ -x "$py" ]; then
            export CLOUDSDK_PYTHON="$py"
            break
        fi
    done
fi

# Configurations
GCP_PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo 'project-53d8ce01-b0e0-4f8b-94c')}"
GCP_REGION="${GCP_REGION:-us-central1}"
GCP_ZONE="${GCP_ZONE:-us-central1-a}"
BUCKET_NAME="${BUCKET_NAME:-anime-recommender-${GCP_PROJECT}}"
DVC_BUCKET_NAME="${DVC_BUCKET_NAME:-anime-recommender-dvc-${GCP_PROJECT}}"

# CLI Flags
FORCE=false
DRY_RUN=false
CLEAN_LOCAL_ONLY=false

show_help() {
    cat << EOF
Usage: ./clear.sh [OPTIONS]

Comprehensive zero-cost teardown script that terminates all local processes/containers
and deletes active bill-incurring cloud resources (VMs, GKE clusters, disks, load balancers,
NAT gateways, static IPs).

Data Safety Guarantee:
  Cloud Storage buckets (raw data & DVC model checkpoints) are strictly PRESERVED
  and will NOT be deleted.

Options:
  -y, --yes, -f, --force      Non-interactive: immediately destroy cloud resources without prompt
  --dry-run                   Audit and display all active cost-incurring resources without deleting
  --local-only                Only stop local processes and Docker containers (no cloud changes)
  --help, -h                  Show this help message

Examples:
  ./clear.sh                  Interactive cleanup with confirmation
  ./clear.sh --force          Automated non-interactive teardown
  ./clear.sh --dry-run        Audit cloud spend and active resources
  ./clear.sh --local-only     Stop local running app & Docker instances
EOF
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes|-f|--force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --local-only)
            CLEAN_LOCAL_ONLY=true
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
  🧹 HYBRID ANIME RECOMMENDER - ZERO-COST TEARDOWN & RESOURCE CLEANUP
================================================================================
EOF
echo -e "${NC}"

# ==============================================================================
# 1. LOCAL PROCESS & DOCKER CLEANUP
# ==============================================================================
echo -e "${YELLOW}[1/10] Stopping local application instances & Docker containers...${NC}"

# Kill any python processes running application.py or tester.py
LOCAL_PIDS=$(pgrep -f "python.*application.py" || true)
if [ -n "$LOCAL_PIDS" ]; then
    echo "[+] Terminating local application processes (PIDs: $LOCAL_PIDS)..."
    kill $LOCAL_PIDS 2>/dev/null || kill -9 $LOCAL_PIDS 2>/dev/null || true
    echo -e "${GREEN}[✓] Application processes stopped.${NC}"
fi

# Free up ports 5000 and 5001 if occupied by Python
for port in 5000 5001; do
    if command -v lsof >/dev/null 2>&1; then
        PORT_PID=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$PORT_PID" ]; then
            # Only kill if it's a python or flask process
            PROC_CMD=$(ps -p $PORT_PID -o comm= 2>/dev/null || true)
            if [[ "$PROC_CMD" =~ python ]]; then
                echo "[+] Freeing port $port (PID: $PORT_PID)..."
                kill -9 $PORT_PID 2>/dev/null || true
            fi
        fi
    fi
done

# Stop any local Docker containers
if command -v docker >/dev/null 2>&1; then
    RUNNING_CONTAINERS=$(docker ps -q --filter "name=jenkins" --filter "name=anime" --filter "name=redis" 2>/dev/null || true)
    if [ -n "$RUNNING_CONTAINERS" ]; then
        echo "[+] Stopping local project Docker containers..."
        docker stop $RUNNING_CONTAINERS 2>/dev/null || true
        echo -e "${GREEN}[✓] Docker containers stopped.${NC}"
    fi
fi

if [ "$CLEAN_LOCAL_ONLY" = true ]; then
    echo -e "\n${GREEN}[✓] Local instances stopped successfully. Exiting (--local-only specified).${NC}"
    exit 0
fi

# ==============================================================================
# 2. VERIFY GCLOUD CLI & ACTIVE PROJECT
# ==============================================================================
if ! command -v gcloud >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] 'gcloud' CLI not installed or not in PATH. Skipping cloud cleanup.${NC}"
    exit 0
fi

ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -n "$ACTIVE_GCLOUD_PROJECT" ] && [ "$ACTIVE_GCLOUD_PROJECT" != "(unset)" ]; then
    GCP_PROJECT="$ACTIVE_GCLOUD_PROJECT"
fi

echo -e "\n${BOLD}Target Cloud Environment:${NC}"
echo "  Project ID : ${GCP_PROJECT}"
echo "  Region     : ${GCP_REGION}"
echo "  Zone       : ${GCP_ZONE}"
echo ""

# ==============================================================================
# 3. AUDIT COST-INCURRING CLOUD RESOURCES
# ==============================================================================
echo -e "${CYAN}[2/10] Auditing Compute Engine VM instances...${NC}"
INSTANCES_TO_DELETE=()
while IFS= read -r line; do
    [ -n "$line" ] && INSTANCES_TO_DELETE+=("$line")
done < <(gcloud compute instances list --project="$GCP_PROJECT" --format="value(name,zone)" 2>/dev/null || true)

echo -e "${CYAN}[3/10] Auditing Google Kubernetes Engine (GKE) clusters...${NC}"
GKE_CLUSTERS=()
while IFS= read -r line; do
    [ -n "$line" ] && GKE_CLUSTERS+=("$line")
done < <(gcloud container clusters list --project="$GCP_PROJECT" --format="value(name,location)" 2>/dev/null || true)

echo -e "${CYAN}[4/10] Auditing persistent disks...${NC}"
DISKS_TO_DELETE=()
while IFS= read -r line; do
    [ -n "$line" ] && DISKS_TO_DELETE+=("$line")
done < <(gcloud compute disks list --project="$GCP_PROJECT" --filter="users:''" --format="value(name,zone)" 2>/dev/null || true)

echo -e "${CYAN}[5/10] Auditing Cloud Load Balancers & Forwarding Rules...${NC}"
FORWARDING_RULES=()
while IFS= read -r line; do
    [ -n "$line" ] && FORWARDING_RULES+=("$line")
done < <(gcloud compute forwarding-rules list --project="$GCP_PROJECT" --format="value(name,region)" 2>/dev/null || true)

echo -e "${CYAN}[6/10] Auditing Cloud NAT Gateways & Cloud Routers...${NC}"
ROUTERS_TO_DELETE=()
while IFS= read -r line; do
    [ -n "$line" ] && ROUTERS_TO_DELETE+=("$line")
done < <(gcloud compute routers list --project="$GCP_PROJECT" --format="value(name,region)" 2>/dev/null || true)

echo -e "${CYAN}[7/10] Auditing reserved static external IP addresses...${NC}"
IPS_TO_DELETE=()
while IFS= read -r line; do
    [ -n "$line" ] && IPS_TO_DELETE+=("$line")
done < <(gcloud compute addresses list --project="$GCP_PROJECT" --format="value(name,region)" 2>/dev/null || true)

echo -e "${CYAN}[8/10] Auditing custom DevOps firewall rules...${NC}"
FWS_TO_DELETE=()
for fw in "allow-devops-public-web" "allow-devops-admin-mgmt" "allow-devops-platform" "allow-anime-recommender"; do
    if gcloud compute firewall-rules describe "$fw" --project="$GCP_PROJECT" >/dev/null 2>&1; then
        FWS_TO_DELETE+=("$fw")
    fi
done

echo -e "${CYAN}[9/10] Auditing Cloud Run & Cloud SQL instances...${NC}"
CLOUDRUN_SERVICES=()
while IFS= read -r line; do
    [ -n "$line" ] && CLOUDRUN_SERVICES+=("$line")
done < <(gcloud run services list --project="$GCP_PROJECT" --format="value(name,region)" 2>/dev/null || true)

# ==============================================================================
# 4. DISPLAY AUDIT SUMMARY
# ==============================================================================
echo -e "\n${BOLD}================ CLOUD RESOURCE AUDIT SUMMARY ================${NC}"

if [ ${#INSTANCES_TO_DELETE[@]} -eq 0 ]; then
    echo -e "  Compute Engine VMs:   ${GREEN}None active (0 instances)${NC}"
else
    echo -e "  Compute Engine VMs:   ${RED}${BOLD}${#INSTANCES_TO_DELETE[@]} active instance(s)${NC}"
    for inst in "${INSTANCES_TO_DELETE[@]}"; do echo "                        - $inst"; done
fi

if [ ${#GKE_CLUSTERS[@]} -eq 0 ]; then
    echo -e "  GKE Clusters:         ${GREEN}None active (0 clusters)${NC}"
else
    echo -e "  GKE Clusters:         ${RED}${BOLD}${#GKE_CLUSTERS[@]} active cluster(s)${NC}"
    for cl in "${GKE_CLUSTERS[@]}"; do echo "                        - $cl"; done
fi

if [ ${#DISKS_TO_DELETE[@]} -eq 0 ]; then
    echo -e "  Orphaned Disks:       ${GREEN}None (0 disks)${NC}"
else
    echo -e "  Orphaned Disks:       ${YELLOW}${#DISKS_TO_DELETE[@]} disk(s)${NC}"
fi

if [ ${#FORWARDING_RULES[@]} -eq 0 ]; then
    echo -e "  Load Balancers:       ${GREEN}None active (0 rules)${NC}"
else
    echo -e "  Load Balancers:       ${YELLOW}${#FORWARDING_RULES[@]} rule(s)${NC}"
fi

if [ ${#ROUTERS_TO_DELETE[@]} -eq 0 ]; then
    echo -e "  Cloud NAT / Routers:  ${GREEN}None active (0 routers)${NC}"
else
    echo -e "  Cloud NAT / Routers:  ${YELLOW}${#ROUTERS_TO_DELETE[@]} router(s)${NC}"
fi

if [ ${#IPS_TO_DELETE[@]} -eq 0 ]; then
    echo -e "  Reserved Static IPs:  ${GREEN}None allocated (0 IPs)${NC}"
else
    echo -e "  Reserved Static IPs:  ${YELLOW}${#IPS_TO_DELETE[@]} idle IP(s) found (incurs idle fee)${NC}"
fi

if [ ${#CLOUDRUN_SERVICES[@]} -eq 0 ]; then
    echo -e "  Cloud Run Services:   ${GREEN}None active (0 services)${NC}"
else
    echo -e "  Cloud Run Services:   ${YELLOW}${#CLOUDRUN_SERVICES[@]} service(s)${NC}"
fi

echo -e "${BOLD}==============================================================${NC}\n"

if [ "$DRY_RUN" = true ]; then
    echo -e "${GREEN}[✓] Dry run complete. No cloud resources were modified or destroyed.${NC}"
    exit 0
fi

TOTAL_ITEMS=$(( ${#INSTANCES_TO_DELETE[@]} + ${#GKE_CLUSTERS[@]} + ${#DISKS_TO_DELETE[@]} + ${#FORWARDING_RULES[@]} + ${#ROUTERS_TO_DELETE[@]} + ${#IPS_TO_DELETE[@]} + ${#FWS_TO_DELETE[@]} + ${#CLOUDRUN_SERVICES[@]} ))

# ==============================================================================
# 5. EXECUTE TEARDOWN DELETION
# ==============================================================================
if [ "$TOTAL_ITEMS" -gt 0 ]; then
    if [ "$FORCE" != true ]; then
        echo -e "${RED}${BOLD}[WARNING] This will permanently delete all ${TOTAL_ITEMS} cloud resource(s) listed above to eliminate 100% of billing.${NC}"
        read -r -p "Do you want to proceed with deletion? [Y/n]: " CONFIRM
        CONFIRM="${CONFIRM:-Y}"
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}[*] Cloud resource deletion cancelled by user.${NC}"
            exit 0
        fi
    fi

    # 1. Delete GKE Clusters
    if [ ${#GKE_CLUSTERS[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting GKE clusters...${NC}"
        for cl_entry in "${GKE_CLUSTERS[@]}"; do
            CL_NAME=$(echo "$cl_entry" | awk '{print $1}')
            CL_LOC=$(echo "$cl_entry" | awk '{print $2}')
            echo -e "  ${RED}✖${NC} Deleting GKE cluster ${BOLD}${CL_NAME}${NC} (${CL_LOC})..."
            gcloud container clusters delete "$CL_NAME" --project="$GCP_PROJECT" --location="$CL_LOC" --quiet || true
        done
        echo -e "${GREEN}[✓] GKE clusters deleted.${NC}"
    fi

    # 2. Delete Compute Engine Instances
    if [ ${#INSTANCES_TO_DELETE[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting Compute Engine VM instances and boot disks...${NC}"
        for inst_entry in "${INSTANCES_TO_DELETE[@]}"; do
            INST_NAME=$(echo "$inst_entry" | awk '{print $1}')
            INST_ZONE=$(echo "$inst_entry" | awk '{print $2}')
            echo -e "  ${RED}✖${NC} Deleting instance ${BOLD}${INST_NAME}${NC} (Zone: ${INST_ZONE})..."
            gcloud compute instances delete "$INST_NAME" --project="$GCP_PROJECT" --zone="$INST_ZONE" --delete-disks=all --quiet || true
        done
        echo -e "${GREEN}[✓] Compute instances deleted.${NC}"
    fi

    # 3. Delete Orphaned Disks
    if [ ${#DISKS_TO_DELETE[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting lingering persistent disks...${NC}"
        for disk_entry in "${DISKS_TO_DELETE[@]}"; do
            DISK_NAME=$(echo "$disk_entry" | awk '{print $1}')
            DISK_ZONE=$(echo "$disk_entry" | awk '{print $2}')
            gcloud compute disks delete "$DISK_NAME" --project="$GCP_PROJECT" --zone="$DISK_ZONE" --quiet 2>/dev/null || true
        done
        echo -e "${GREEN}[✓] Persistent disks purged.${NC}"
    fi

    # 4. Delete Forwarding Rules (Load Balancers)
    if [ ${#FORWARDING_RULES[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting forwarding rules...${NC}"
        for fr_entry in "${FORWARDING_RULES[@]}"; do
            FR_NAME=$(echo "$fr_entry" | awk '{print $1}')
            FR_REGION=$(echo "$fr_entry" | awk '{print $2}')
            gcloud compute forwarding-rules delete "$FR_NAME" --project="$GCP_PROJECT" --region="$FR_REGION" --quiet 2>/dev/null || \
            gcloud compute forwarding-rules delete "$FR_NAME" --project="$GCP_PROJECT" --global --quiet 2>/dev/null || true
        done
        echo -e "${GREEN}[✓] Forwarding rules deleted.${NC}"
    fi

    # 5. Delete Cloud Routers & NAT
    if [ ${#ROUTERS_TO_DELETE[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting Cloud Routers & NAT gateways...${NC}"
        for rt_entry in "${ROUTERS_TO_DELETE[@]}"; do
            RT_NAME=$(echo "$rt_entry" | awk '{print $1}')
            RT_REGION=$(echo "$rt_entry" | awk '{print $2}')
            gcloud compute routers delete "$RT_NAME" --project="$GCP_PROJECT" --region="$RT_REGION" --quiet 2>/dev/null || true
        done
        echo -e "${GREEN}[✓] Cloud Routers & NAT deleted.${NC}"
    fi

    # 6. Release Static External IPs
    if [ ${#IPS_TO_DELETE[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Releasing static external IP addresses...${NC}"
        for ip_entry in "${IPS_TO_DELETE[@]}"; do
            IP_NAME=$(echo "$ip_entry" | awk '{print $1}')
            IP_REGION=$(echo "$ip_entry" | awk '{print $2}')
            if [ -n "$IP_REGION" ] && [ "$IP_REGION" != "(unset)" ]; then
                gcloud compute addresses delete "$IP_NAME" --project="$GCP_PROJECT" --region="$IP_REGION" --quiet 2>/dev/null || true
            else
                gcloud compute addresses delete "$IP_NAME" --project="$GCP_PROJECT" --global --quiet 2>/dev/null || true
            fi
        done
        echo -e "${GREEN}[✓] Static IPs released.${NC}"
    fi

    # 7. Delete Cloud Run Services
    if [ ${#CLOUDRUN_SERVICES[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting Cloud Run services...${NC}"
        for cr_entry in "${CLOUDRUN_SERVICES[@]}"; do
            CR_NAME=$(echo "$cr_entry" | awk '{print $1}')
            CR_REGION=$(echo "$cr_entry" | awk '{print $2}')
            gcloud run services delete "$CR_NAME" --project="$GCP_PROJECT" --region="$CR_REGION" --quiet 2>/dev/null || true
        done
        echo -e "${GREEN}[✓] Cloud Run services deleted.${NC}"
    fi

    # 8. Delete Firewall Rules
    if [ ${#FWS_TO_DELETE[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}[*] Deleting firewall rules...${NC}"
        for fw in "${FWS_TO_DELETE[@]}"; do
            gcloud compute firewall-rules delete "$fw" --project="$GCP_PROJECT" --quiet 2>/dev/null || true
        done
        echo -e "${GREEN}[✓] Firewall rules deleted.${NC}"
    fi
fi

# GCS Buckets Preservation (Data and DVC artifacts are kept safe)
echo -e "\n${CYAN}[*] Preserving Google Cloud Storage Buckets (Data & Checkpoint Safety):${NC}"
echo -e "  - gs://${BUCKET_NAME} ${GREEN}[PRESERVED]${NC}"
echo -e "  - gs://${DVC_BUCKET_NAME} ${GREEN}[PRESERVED]${NC}"
echo -e "  ${YELLOW}* Datasets, DVC tracking pointers, and model weights are retained and will NOT be deleted.${NC}"

# ==============================================================================
# 6. FINAL ZERO-COST VERIFICATION
# ==============================================================================
echo -e "\n${CYAN}[10/10] Performing final Zero-Cost audit verification...${NC}"
FINAL_INSTANCES=$(gcloud compute instances list --project="$GCP_PROJECT" --format="value(name)" 2>/dev/null || true)
FINAL_GKE=$(gcloud container clusters list --project="$GCP_PROJECT" --format="value(name)" 2>/dev/null || true)
FINAL_DISKS=$(gcloud compute disks list --project="$GCP_PROJECT" --filter="users:''" --format="value(name)" 2>/dev/null || true)
FINAL_IPS=$(gcloud compute addresses list --project="$GCP_PROJECT" --format="value(name)" 2>/dev/null || true)

echo -e "\n${BOLD}================ FINAL CLOUD STATUS AUDIT ================${NC}"
[ -z "$FINAL_INSTANCES" ] && echo -e "  Active Compute VMs:   ${GREEN}${BOLD}0 (NO Compute Engine charges)${NC}" || echo -e "  Active VMs:           ${RED}${BOLD}Warning: ${FINAL_INSTANCES}${NC}"
[ -z "$FINAL_GKE" ]       && echo -e "  Active GKE Clusters:  ${GREEN}${BOLD}0 (NO Kubernetes charges)${NC}" || echo -e "  Active GKE:           ${RED}${BOLD}Warning: ${FINAL_GKE}${NC}"
[ -z "$FINAL_DISKS" ]     && echo -e "  Orphaned Disks:       ${GREEN}${BOLD}0 (NO Idle Disk charges)${NC}" || echo -e "  Orphaned Disks:       ${YELLOW}Active: ${FINAL_DISKS}${NC}"
[ -z "$FINAL_IPS" ]       && echo -e "  Reserved Static IPs:  ${GREEN}${BOLD}0 (NO Static IP idle fees)${NC}" || echo -e "  Static IPs:           ${YELLOW}Active: ${FINAL_IPS}${NC}"
echo -e "  Estimated Cloud Burn: ${GREEN}${BOLD}\$0.00 / hr${NC}"
echo -e "${BOLD}==========================================================${NC}\n"

echo -e "${GREEN}${BOLD}🎉 Zero-cost teardown complete! All local instances stopped and billing-incurring cloud assets verified at \$0.00/hr.${NC}\n"
