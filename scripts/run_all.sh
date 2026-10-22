#!/usr/bin/env bash
# ==============================================================================
# Principal Engineer Polyglot Mesh Local Orchestrator
# Starts Go, Express, Rust, Python, and Next.js with graceful SIGINT teardown.
# ==============================================================================
set -eo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIDS=()

cleanup() {
    echo -e "\n${YELLOW}[!] Received interrupt signal. Gracefully shutting down all microservices...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
    echo -e "${GREEN}[✓] All microservices stopped cleanly. Zero orphan processes.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo -e "\n${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN} 🚀 LAUNCHING HYBRID ANIME POLYGLOT MESH (5 SERVICES) ${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}\n"

# 1. Start Rust SIMD Scoring Engine (Port 8083)
echo -e "${YELLOW}[1/5] Starting Rust SIMD Scoring Engine (Port 8083)...${NC}"
(cd services/rust-scoring-engine && cargo run --quiet --release) &
PIDS+=($!)

# 2. Start Go Authentication Microservice (Port 8081)
echo -e "${YELLOW}[2/5] Starting Go Authentication Microservice (Port 8081)...${NC}"
(cd services/go-auth-service && go run main.go) &
PIDS+=($!)

# 3. Start Node.js Express Interactions Service (Port 8082)
echo -e "${YELLOW}[3/5] Starting Node.js Express Interactions Service (Port 8082)...${NC}"
(cd services/express-interaction-service && npm start --silent) &
PIDS+=($!)

# 4. Start Python FastAPI Intelligence Core (Port 8000)
echo -e "${YELLOW}[4/5] Starting Python FastAPI Intelligence Core (Port 8000)...${NC}"
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning &
PIDS+=($!)

# 5. Start Next.js 16 Latest Frontend (Port 3000)
echo -e "${YELLOW}[5/5] Starting Next.js Latest Frontend (Port 3000)...${NC}"
(cd frontend && npm run dev) &
PIDS+=($!)

echo -e "\n${BOLD}${GREEN}======================================================================${NC}"
echo -e "${BOLD}${GREEN} ✓ ALL 5 MICROSERVICES ACTIVE AND RUNNING! ${NC}"
echo -e "${BOLD}${CYAN} 🌐 Next.js Frontend:     http://localhost:3000 ${NC}"
echo -e "${BOLD}${CYAN} ⚡ Rust SIMD Engine:     http://localhost:8083/health ${NC}"
echo -e "${BOLD}${CYAN} 🔐 Go Auth Service:      http://localhost:8081/health ${NC}"
echo -e "${BOLD}${CYAN} 💬 Express Interactions: http://localhost:8082/health ${NC}"
echo -e "${BOLD}${CYAN} 🤖 Python FastAPI:       http://localhost:8000/docs ${NC}"
echo -e "${BOLD}${GREEN}======================================================================${NC}"
echo -e "${YELLOW}Press [CTRL+C] at any time to gracefully terminate all services.${NC}\n"

# Wait for all background tasks
wait
