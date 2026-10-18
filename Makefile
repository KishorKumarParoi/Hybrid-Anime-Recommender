# ==============================================================================
# Hybrid Anime Intelligence Platform — Master Automation Makefile
# Principal Engineer Grade Developer Experience & Cloud Orchestration
# ==============================================================================

SHELL := /bin/bash
.PHONY: help dev test test-fast build docker-up docker-down clean

help:
	@echo "======================================================================"
	@echo " 🚀 HYBRID ANIME INTELLIGENCE PLATFORM — MAKEFILE AUTOMATION"
	@echo "======================================================================"
	@echo "  make dev          - Start all 5 polyglot services locally"
	@echo "  make test         - Run unified polyglot test suite (Rust, Go, Node, Python, Next)"
	@echo "  make build        - Compile release binaries and Next.js Turbopack build"
	@echo "  make docker-up    - Build and launch all 9 services via Docker Compose"
	@echo "  make docker-down  - Gracefully stop and clean Docker Compose containers"
	@echo "  make clean        - Remove caches, temporary files, and build artifacts"
	@echo "======================================================================"

dev:
	@chmod +x scripts/run_all.sh
	@./scripts/run_all.sh

test:
	@chmod +x scripts/test_all.sh
	@./scripts/test_all.sh

build:
	@echo "==> Building Rust SIMD Engine (Release)..."
	@cd services/rust-scoring-engine && cargo build --release
	@echo "==> Compiling Go Auth Microservice..."
	@cd services/go-auth-service && go build -o /dev/null main.go
	@echo "==> Compiling Next.js 16 Production Bundle..."
	@cd frontend && npm run build
	@echo "✓ All binaries and production bundles built successfully."

docker-up:
	@docker-compose up --build

docker-down:
	@docker-compose down -v

clean:
	@rm -rf .pytest_cache frontend/.next services/rust-scoring-engine/target
	@echo "✓ Cleaned build caches and temporary directories."
