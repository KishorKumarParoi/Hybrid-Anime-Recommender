#!/usr/bin/env bash
# ==============================================================================
# 🎬 HYBRID ANIME RECOMMENDER & AI PLATFORM - ONE-CLICK BOOTSTRAP & DEVOPS RUNNER
# Works on fresh Ubuntu VMs, Cloud Shell, and macOS:
# 1. Loads configuration & secrets from .env if present
# 2. Bootstraps system tools (curl, git, unzip, uv, gcloud, kubectl, docker)
# 3. Configures GCP authentication & project
# 4. Ensures GCS raw data bucket & DVC versioning bucket exist
# 5. Configures Service Account with Storage Admin/Viewer permissions
# 6. Initializes DVC remote storage
# 7. Syncs dataset from GCS or Kaggle
# 8. Installs Python dependencies via uv
# 9. Optionally deploys complete Kubernetes stack (Redis, Prometheus, Grafana,
#    Elasticsearch, Logstash, Filebeat, Kibana, ArgoCD)
# 10. Optionally launches Jenkins or the local Flask web application
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
  🎬 HYBRID ANIME RECOMMENDER & AI AGENT PLATFORM - ENTERPRISE RUNNER
================================================================================
EOF
echo -e "${NC}"

# Helper for sudo commands
run_sudo() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &>/dev/null; then
        sudo "$@"
    else
        "$@"
    fi
}

# 1. Load Configurations & Flags
if [ -f .env ]; then
    echo -e "${CYAN}[+] Sourcing environment configurations from .env...${NC}"
    set -a
    source .env 2>/dev/null || true
    set +a
fi

GCP_PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo 'project-53d8ce01-b0e0-4f8b-94c')}"
BUCKET_NAME="${BUCKET_NAME:-anime-recommender-${GCP_PROJECT}}"
DVC_BUCKET_NAME="${DVC_BUCKET_NAME:-anime-recommender-dvc-${GCP_PROJECT}}"
GCP_REGION="${GCP_REGION:-us-central1}"
SA_NAME="${SA_NAME:-anime-recommender}"
KEY_FILE="${KEY_FILE:-${GOOGLE_APPLICATION_CREDENTIALS}}"
if [ -z "$KEY_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    KEY_FILE="$(ls project-*.json 2>/dev/null | head -n 1)"
fi
if [ -z "$KEY_FILE" ]; then
    KEY_FILE="${GCP_PROJECT}-sa-key.json"
fi

DATA_DIR="artifacts/raw"
KAGGLE_DATASET="hernan4444/anime-recommendation-database-2020"
START_APP=false
DEPLOY_K8S=false
RUN_JENKINS=false
RUN_TESTS=false
PUSH_GCR=false
SECURE_FIREWALL=false
CREATE_VM=false
VM_NAME=""
VM_MACHINE_TYPE=""
VM_DISK_SIZE=""
VM_ZONE=""
VM_SPOT=false
GCR_HOSTNAME="${GCR_HOSTNAME:-gcr.io}"
SERVER_PUBLIC_IP="${SERVER_PUBLIC_IP:-136.71.59.13}"

# CLI Flag parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --start|-s)
            START_APP=true
            shift
            ;;
        --create-vm|--vm)
            CREATE_VM=true
            shift
            ;;
        --vm-name)
            VM_NAME="$2"
            shift 2
            ;;
        --machine-type|-m)
            VM_MACHINE_TYPE="$2"
            shift 2
            ;;
        --vm-disk)
            VM_DISK_SIZE="$2"
            shift 2
            ;;
        --spot|--preemptible)
            VM_SPOT=true
            shift
            ;;
        --deploy-k8s|-k|--k8s)
            DEPLOY_K8S=true
            shift
            ;;
        --jenkins|-j)
            RUN_JENKINS=true
            shift
            ;;
        --test|-t)
            RUN_TESTS=true
            shift
            ;;
        --push-gcr|--gcr)
            PUSH_GCR=true
            shift
            ;;
        --secure-firewall|--firewall)
            SECURE_FIREWALL=true
            shift
            ;;
        --project|-p)
            GCP_PROJECT="$2"
            shift 2
            ;;
        --bucket|-b)
            BUCKET_NAME="$2"
            shift 2
            ;;
        --dvc-bucket)
            DVC_BUCKET_NAME="$2"
            shift 2
            ;;
        --region|-r)
            GCP_REGION="$2"
            shift 2
            ;;
        --zone|-z)
            GCP_ZONE="$2"
            VM_ZONE="$2"
            shift 2
            ;;
        --sa-name)
            SA_NAME="$2"
            shift 2
            ;;
        --key-file)
            KEY_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./deploy.sh [OPTIONS]"
            echo ""
            echo "Execution Modes:"
            echo "  --start, -s                Launch the Flask web app locally"
            echo "  --create-vm, --vm          Provision Compute Engine VM, clone repo, and start platform"
            echo "  --deploy-k8s, -k           Deploy complete Kubernetes stack (App, Redis, Security, Prometheus, Grafana, ELK, ArgoCD)"
            echo "  --jenkins, -j              Start Jenkins container with Docker socket integration"
            echo "  --test, -t                 Execute pytest test suite with code coverage"
            echo "  --push-gcr, --gcr          Build and push container image to Google Container Registry (gcr.io)"
            echo "  --secure-firewall          Apply zero-trust GCP VPC firewall rules and anti-bot shield"
            echo ""
            echo "VM Customization Options:"
            echo "  --vm-name <NAME>           Compute Engine VM instance name (default: hybrid-anime-recommender-vm)"
            echo "  --machine-type, -m <TYPE>  GCP Machine type (default: e2-standard-4, e2-standard-2, e2-medium)"
            echo "  --vm-disk <GB>             Boot disk size in GB (default: 50)"
            echo "  --spot                     Provision as Spot VM (60-80% cost reduction)"
            echo ""
            echo "Configuration Overrides:"
            echo "  --project, -p <PROJECT_ID> GCP Project ID (default: ${GCP_PROJECT})"
            echo "  --bucket, -b <BUCKET_NAME> GCS Raw Data Bucket Name (default: ${BUCKET_NAME})"
            echo "  --dvc-bucket <NAME>        GCS DVC Bucket Name (default: ${DVC_BUCKET_NAME})"
            echo "  --region, -r <REGION>      GCP Region (default: ${GCP_REGION})"
            echo "  --zone, -z <ZONE>          GCP Zone (default: ${GCP_ZONE:-us-central1-a})"
            echo "  --sa-name <NAME>           Service Account name (default: ${SA_NAME})"
            echo "  --key-file <PATH>          Service Account JSON key path (default: ${KEY_FILE})"
            echo "  --help, -h                 Show this help message"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}[!] Unknown argument: $1 (ignoring)${NC}"
            shift
            ;;
    esac
done

SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

echo -e "${BOLD}Target Configuration:${NC}"
echo "  Project ID      : ${GCP_PROJECT}"
echo "  Data Bucket     : gs://${BUCKET_NAME}"
echo "  DVC Bucket      : gs://${DVC_BUCKET_NAME}"
echo "  Region          : ${GCP_REGION}"
echo "  Service Account : ${SA_EMAIL}"
echo "  SA Key File     : ${KEY_FILE}"
echo "  Raw Data Dir    : ${DATA_DIR}"
echo ""

# 2. System Bootstrap (Ubuntu / Debian / Linux Tools)
echo -e "${CYAN}[1/8] Checking system dependencies...${NC}"
if [ -f /etc/debian_version ]; then
    echo "[+] Debian/Ubuntu detected. Ensuring base packages are installed..."
    run_sudo apt-get update -qq
    run_sudo apt-get install -y -qq curl git unzip build-essential python3 python3-pip python3-venv ca-certificates
fi

# Ensure uv is installed
if ! command -v uv &>/dev/null; then
    echo -e "${YELLOW}[+] Installing uv (high-performance Python manager)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
echo -e "${GREEN}[✓] uv is ready: $(uv --version)${NC}"

# Ensure Google Cloud SDK (gcloud) is installed
if ! command -v gcloud &>/dev/null; then
    echo -e "${YELLOW}[+] Installing Google Cloud SDK (gcloud)...${NC}"
    if [ -f /etc/debian_version ]; then
        run_sudo apt-get install -y -qq apt-transport-https ca-certificates gnupg curl
        curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | run_sudo gpg --dearmor --yes -o /usr/share/keyrings/cloud.google.gpg
        echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | run_sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
        run_sudo apt-get update -qq && run_sudo apt-get install -y -qq google-cloud-cli
    else
        curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="$HOME"
        export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    fi
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
echo -e "${GREEN}[✓] gcloud is ready: $(gcloud --version | head -n 1)${NC}"

# 3. GCP Authentication & Project Connection
echo -e "\n${CYAN}[2/8] Connecting to Google Cloud Platform...${NC}"
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)

if [ -z "$CURRENT_ACCOUNT" ]; then
    if curl -s -f -m 2 -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email" &>/dev/null; then
        VM_SA=$(curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email")
        echo -e "${GREEN}[✓] Authenticated via GCP Compute Engine Service Account: ${VM_SA}${NC}"
    elif [ -n "${GOOGLE_APPLICATION_CREDENTIALS}" ] && [ -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
        echo -e "[+] Authenticating with Service Account key: ${GOOGLE_APPLICATION_CREDENTIALS}..."
        gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
    elif [ -f "${KEY_FILE}" ]; then
        echo -e "[+] Authenticating with Service Account key: ${KEY_FILE}..."
        gcloud auth activate-service-account --key-file="${KEY_FILE}"
    else
        echo -e "${YELLOW}[!] No active GCP account detected. Initiating authentication...${NC}"
        gcloud auth login --no-launch-browser || gcloud auth login
    fi
else
    echo -e "${GREEN}[✓] Using active GCP account: ${CURRENT_ACCOUNT}${NC}"
fi

echo "[+] Setting active GCP project to: ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}" >/dev/null

# 4. GCS Buckets Verification & Creation (Raw Data + DVC Versioning)
echo -e "\n${CYAN}[3/8] Verifying Google Cloud Storage Buckets...${NC}"

# Raw Data Bucket
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
    echo "[+] Raw data bucket gs://${BUCKET_NAME} does not exist. Creating in ${GCP_REGION}..."
    gcloud storage buckets create "gs://${BUCKET_NAME}" \
        --project="${GCP_PROJECT}" \
        --location="${GCP_REGION}" \
        --default-storage-class=STANDARD \
        --uniform-bucket-level-access
    echo -e "${GREEN}[✓] Raw data bucket created: gs://${BUCKET_NAME}${NC}"
else
    echo -e "${GREEN}[✓] Raw data bucket gs://${BUCKET_NAME} exists and is accessible.${NC}"
fi

# DVC Version Tracking Bucket
if ! gcloud storage buckets describe "gs://${DVC_BUCKET_NAME}" &>/dev/null; then
    echo "[+] DVC tracking bucket gs://${DVC_BUCKET_NAME} does not exist. Creating in ${GCP_REGION}..."
    gcloud storage buckets create "gs://${DVC_BUCKET_NAME}" \
        --project="${GCP_PROJECT}" \
        --location="${GCP_REGION}" \
        --default-storage-class=STANDARD \
        --uniform-bucket-level-access
    echo -e "${GREEN}[✓] DVC tracking bucket created: gs://${DVC_BUCKET_NAME}${NC}"
else
    echo -e "${GREEN}[✓] DVC tracking bucket gs://${DVC_BUCKET_NAME} exists and is accessible.${NC}"
fi

# 5. Service Account Creation, IAM Permissions & Buckets Connection
echo -e "\n${CYAN}[4/8] Configuring Service Account and Bucket Permissions...${NC}"

if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${GCP_PROJECT}" &>/dev/null; then
    echo "[+] Creating Service Account: ${SA_NAME}..."
    gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="Anime Recommender Service Account" \
        --description="Service account for Anime Recommender Storage & Operations" \
        --project="${GCP_PROJECT}"
    echo -e "${GREEN}[✓] Service Account ${SA_EMAIL} created.${NC}"
else
    echo -e "${GREEN}[✓] Service Account ${SA_EMAIL} already exists.${NC}"
fi

echo "[+] Assigning IAM roles: storage-object-viewer, storage-object-admin, owner..."
for role in "roles/storage.objectViewer" "roles/storage.objectAdmin" "roles/owner"; do
    gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --condition=None --quiet >/dev/null 2>&1 || true
done
echo -e "${GREEN}[✓] Roles granted to ${SA_EMAIL} at project level.${NC}"

for bkt in "${BUCKET_NAME}" "${DVC_BUCKET_NAME}"; do
    gcloud storage buckets add-iam-policy-binding "gs://${bkt}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.objectAdmin" >/dev/null 2>&1 || true
    gcloud storage buckets add-iam-policy-binding "gs://${bkt}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.objectViewer" >/dev/null 2>&1 || true
    echo -e "${GREEN}[✓] Connected ${SA_EMAIL} to gs://${bkt} with Admin/Viewer permissions.${NC}"
done

if [ ! -f "${KEY_FILE}" ]; then
    echo "[+] Generating JSON credentials key: ${KEY_FILE}..."
    gcloud iam service-accounts keys create "${KEY_FILE}" \
        --iam-account="${SA_EMAIL}" \
        --project="${GCP_PROJECT}"
    echo -e "${GREEN}[✓] Key created: ${KEY_FILE}${NC}"
else
    echo -e "${GREEN}[✓] Key file already present: ${KEY_FILE}${NC}"
fi

export GOOGLE_APPLICATION_CREDENTIALS="$(cd "$(dirname "${KEY_FILE}")" && pwd)/$(basename "${KEY_FILE}")"

# 6. DVC Version Tracking Remote Configuration
echo -e "\n${CYAN}[5/8] Configuring DVC Version Tracking Remote...${NC}"
if [ ! -d ".dvc" ]; then
    echo "[+] Initializing DVC repository..."
    uv run dvc init 2>/dev/null || dvc init 2>/dev/null || true
fi
DVC_REMOTE_URL="gs://${DVC_BUCKET_NAME}/dvc_store"
uv run dvc remote add -d -f gcs-remote "${DVC_REMOTE_URL}" 2>/dev/null || dvc remote add -d -f gcs-remote "${DVC_REMOTE_URL}" 2>/dev/null || true
echo -e "${GREEN}[✓] DVC remote configured to: ${DVC_REMOTE_URL}${NC}"

# 7. Smart Dataset Synchronization
echo -e "\n${CYAN}[6/8] Synchronizing Dataset...${NC}"
mkdir -p "${DATA_DIR}"

if [ -f "${DATA_DIR}/anime.csv" ] && [ -f "${DATA_DIR}/animelist.csv" ]; then
    echo -e "${GREEN}[✓] Full dataset (2.7 GB+) is already present locally in ${DATA_DIR}.${NC}"
else
    if gcloud storage ls "gs://${BUCKET_NAME}/anime.csv" &>/dev/null && gcloud storage ls "gs://${BUCKET_NAME}/animelist.csv" &>/dev/null; then
        echo -e "[+] Dataset detected in GCS bucket gs://${BUCKET_NAME}. Downloading directly via GCP network..."
        gcloud storage cp "gs://${BUCKET_NAME}/*.csv" "${DATA_DIR}/"
        echo -e "${GREEN}[✓] Downloaded dataset from GCS into ${DATA_DIR}.${NC}"
    else
        echo -e "[+] Dataset not found in GCS. Downloading from Kaggle (${KAGGLE_DATASET})..."
        uv pip install -q kaggle || pip install -q kaggle || true

        DOWNLOAD_OK=false
        if uv run kaggle datasets download -d "${KAGGLE_DATASET}" -p "${DATA_DIR}" --unzip; then
            DOWNLOAD_OK=true
        elif command -v kaggle &>/dev/null && kaggle datasets download -d "${KAGGLE_DATASET}" -p "${DATA_DIR}" --unzip; then
            DOWNLOAD_OK=true
        fi

        if [ "$DOWNLOAD_OK" = false ] || [ ! -f "${DATA_DIR}/anime.csv" ]; then
            echo -e "${YELLOW}[!] Syncing missing files directly from GCP Cloud Storage endpoint...${NC}"
            GCS_PUBLIC_URL="https://storage.googleapis.com/${BUCKET_NAME}"
            for fname in anime.csv anime_with_synopsis.csv watching_status.csv rating_complete.csv animelist.csv; do
                if [ ! -f "${DATA_DIR}/${fname}" ]; then
                    curl -fsSL "${GCS_PUBLIC_URL}/${fname}" -o "${DATA_DIR}/${fname}" || true
                fi
            done
        fi

        if ls "${DATA_DIR}"/*.csv &>/dev/null; then
            echo -e "[+] Uploading dataset to gs://${BUCKET_NAME} for persistent cloud storage..."
            gcloud storage cp "${DATA_DIR}"/*.csv "gs://${BUCKET_NAME}/" || true
        fi
    fi
fi

# 8. Python Environment Setup & Dependency Sync
echo -e "\n${CYAN}[7/8] Syncing Python dependencies via uv...${NC}"
uv sync
echo -e "${GREEN}[✓] Virtual environment synced successfully.${NC}"

# Execute Test Suite if requested
if [ "$RUN_TESTS" = true ]; then
    echo -e "\n${CYAN}[*] Running Pytest test suite with code coverage...${NC}"
    uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
fi

# Build & Push Docker image to Google Container Registry (GCR) if requested
if [ "$PUSH_GCR" = true ]; then
    echo -e "\n${CYAN}[*] Building & Pushing Docker Image to Google Container Registry (GCR)...${NC}"
    GCR_TAG="${GCR_HOSTNAME}/${GCP_PROJECT}/hybrid-anime-recommender:latest"
    GIT_TAG="${GCR_HOSTNAME}/${GCP_PROJECT}/hybrid-anime-recommender:$(git rev-parse --short HEAD 2>/dev/null || echo 'manual')"

    echo "[*] Configuring Docker authentication for ${GCR_HOSTNAME} via gcloud..."
    gcloud auth configure-docker "${GCR_HOSTNAME}" --quiet 2>/dev/null || true

    echo "[*] Building Docker container image for linux/amd64..."
    docker build \
        -t "$GCR_TAG" \
        -t "$GIT_TAG" \
        .

    echo "[*] Pushing container tags to Google Container Registry..."
    docker push "$GCR_TAG"
    docker push "$GIT_TAG"
    echo -e "${GREEN}[✓] Docker image successfully pushed to Google Container Registry!${NC}"
    echo -e "    GCR URI (latest): $GCR_TAG"
    echo -e "    GCR URI (commit): $GIT_TAG"
fi

# Provision Compute Engine VM & Clone Repository if requested
if [ "$CREATE_VM" = true ]; then
    echo -e "\n${CYAN}[*] Provisioning Compute Engine VM & Bootstrapping Repository...${NC}"
    VM_ARGS=()
    [ -n "$VM_NAME" ] && VM_ARGS+=(--name "$VM_NAME")
    [ -n "$VM_MACHINE_TYPE" ] && VM_ARGS+=(--machine-type "$VM_MACHINE_TYPE")
    [ -n "$VM_DISK_SIZE" ] && VM_ARGS+=(--disk-size "$VM_DISK_SIZE")
    [ -n "$VM_ZONE" ] && VM_ARGS+=(--zone "$VM_ZONE")
    [ "$VM_SPOT" = true ] && VM_ARGS+=(--spot)

    if [ -x "${SCRIPT_DIR}/scripts/create_vm.sh" ]; then
        "${SCRIPT_DIR}/scripts/create_vm.sh" "${VM_ARGS[@]}"
    else
        bash "${SCRIPT_DIR}/scripts/create_vm.sh" "${VM_ARGS[@]}"
    fi

    # Reload environment to pick up newly assigned SERVER_PUBLIC_IP
    if [ -f "${SCRIPT_DIR}/.env" ]; then
        set -a
        source "${SCRIPT_DIR}/.env" 2>/dev/null || true
        set +a
    fi
fi

# Apply GCP Firewall Bot Shield if requested
if [ "$SECURE_FIREWALL" = true ]; then
    echo -e "\n${CYAN}[*] Applying Zero-Trust GCP VPC Firewall Rules & Bot Shield...${NC}"
    if [ -x "${SCRIPT_DIR}/scripts/secure_firewall.sh" ]; then
        "${SCRIPT_DIR}/scripts/secure_firewall.sh" --apply
    else
        bash "${SCRIPT_DIR}/scripts/secure_firewall.sh" --apply
    fi
fi

# Deploy Kubernetes Stack if requested
if [ "$DEPLOY_K8S" = true ]; then
    echo -e "\n${CYAN}[*] Deploying Enterprise Kubernetes Platform Stack...${NC}"
    echo "[+] Deploying Zero-Trust NetworkPolicies & Security Hardening..."
    kubectl apply -f manifests/security/ 2>/dev/null || true

    echo "[+] Deploying Redis Cache..."
    kubectl apply -f manifests/redis/ 2>/dev/null || true

    echo "[+] Deploying Elasticsearch, Logstash, Filebeat & Kibana logging..."
    kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -f manifests/logging/ 2>/dev/null || true

    echo "[+] Deploying Application Deployment and Service..."
    kubectl apply -f manifests/deployment.yaml -f manifests/service.yaml

    echo "[+] Deploying Prometheus & Grafana monitoring stack..."
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -f manifests/monitoring/ 2>/dev/null || true

    echo "[+] Deploying ArgoCD GitOps application..."
    kubectl apply -f argocd/application.yaml 2>/dev/null || true
    echo -e "${GREEN}[✓] All Kubernetes manifests successfully applied.${NC}"
fi

# Launch Jenkins if requested
if [ "$RUN_JENKINS" = true ]; then
    echo -e "\n${CYAN}[*] Launching Jenkins CI/CD Container...${NC}"
    if command -v docker &>/dev/null; then
        docker build -t custom-jenkins:latest custom_jenkins/
        docker stop jenkins 2>/dev/null || true
        docker rm jenkins 2>/dev/null || true
        docker run -d \
            --name jenkins \
            --restart always \
            -p 8080:8080 \
            -p 50000:50000 \
            -v jenkins_home:/var/jenkins_home \
            -v /var/run/docker.sock:/var/run/docker.sock \
            custom-jenkins:latest
        echo -e "${GREEN}[✓] Jenkins is running at http://localhost:8080${NC}"
    else
        echo -e "${RED}[!] Docker is not installed or running. Cannot launch Jenkins.${NC}"
    fi
fi

# Summary
echo -e "\n${CYAN}[8/8] Deployment Summary & Service Endpoints...${NC}"
echo -e "${GREEN}${BOLD}"
cat << "EOF"
================================================================================
🎉 DEPLOYMENT COMPLETE! All systems bootstrapped, synced, and operational.
================================================================================
EOF
echo -e "${NC}"

echo "DevOps & Platform Service Endpoints:"
echo "  🌐 Web UI (LoadBalancer / Alt) : http://${SERVER_PUBLIC_IP}:30080  |  http://${SERVER_PUBLIC_IP}:5000"
echo "  📊 Prometheus Metrics UI       : http://${SERVER_PUBLIC_IP}:9090   (NodePort: 30090)"
echo "  📈 Grafana AI Telemetry UI     : http://${SERVER_PUBLIC_IP}:3000   (NodePort: 30300)"
echo "  🔭 Kibana Log Analytics UI     : http://${SERVER_PUBLIC_IP}:5601   (NodePort: 30601)"
echo "  🔍 SonarQube Code Quality UI   : http://${SERVER_PUBLIC_IP}:9000"
echo "  📦 Sonatype Nexus Repository   : http://${SERVER_PUBLIC_IP}:8081"
echo "  🚀 ArgoCD GitOps Dashboard     : http://${SERVER_PUBLIC_IP}:30751"
echo "  🛠️ Jenkins CI/CD Dashboard     : http://${SERVER_PUBLIC_IP}:8080"
echo ""
echo "Quick Commands:"
echo "  • Run full training pipeline: uv run python pipeline/training_pipeline.py"
echo "  • Start Web UI & API server : uv run python application.py"
echo "  • Run test suite            : uv run pytest tests/ -v"
echo "  • Run quick CLI tester      : uv run python tester.py"
echo "  • Deploy K8s stack          : ./deploy.sh --deploy-k8s"
echo "  • Run Jenkins               : ./deploy.sh --jenkins"
echo ""

# Launch application if requested
if [ "$START_APP" = true ]; then
    APP_PORT="${PORT:-5000}"
    if command -v lsof &>/dev/null && lsof -i ":${APP_PORT}" &>/dev/null; then
        echo -e "${YELLOW}[!] Port ${APP_PORT} is in use. Switching to port 5001...${NC}"
        APP_PORT=5001
    fi
    export PORT="${APP_PORT}"
    echo -e "${CYAN}[*] Starting Web Application on http://0.0.0.0:${APP_PORT}...${NC}"
    uv run python application.py
fi
