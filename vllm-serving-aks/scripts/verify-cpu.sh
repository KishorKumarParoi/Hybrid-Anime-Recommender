#!/usr/bin/env bash
# Verification for AKS cluster CPU / Mock serving
# Handles port-forward + cleanup automatically.
set -uo pipefail

PORT=8000
PF_PID=""
cleanup() { [ -n "$PF_PID" ] && kill "$PF_PID" 2>/dev/null || true; }
trap cleanup EXIT

run() { echo "\$ $*"; "$@"; }

echo "==> [0/3] Cluster context"
run kubectl config current-context

echo; echo "==> [1/3] Waiting for the vllm pod to be Ready (system node pool)..."
run kubectl wait --for=condition=ready pod -l app=vllm --timeout=180s || {
  echo "FAIL: pod never became Ready. Check: kubectl get pods -l app=vllm ; kubectl logs deploy/vllm-cpu-mock"
  exit 1
}

echo; echo "==> [2/3] Opening port-forward localhost:${PORT} -> svc/vllm:8000"
kubectl port-forward svc/vllm "${PORT}:8000" >/tmp/vllm-pf.log 2>&1 &
PF_PID=$!
echo "    waiting for the tunnel to answer..."
for i in $(seq 1 20); do
  curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1 && break
  sleep 1
  [ "$i" = "20" ] && { echo "FAIL: port-forward never responded. See /tmp/vllm-pf.log"; exit 1; }
done
echo "    tunnel is up."

echo; echo "==> [3/3] Testing OpenAI-compatible /v1/completions endpoint"
RESP=$(curl -s "http://localhost:${PORT}/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-7B-Instruct-AWQ","prompt":"Hello, my name is","max_tokens":32,"temperature":0}')
echo "$RESP" | (jq . 2>/dev/null || cat)

echo "$RESP" | grep -q '"text"' \
  && echo -e "\n✅ PASS: AKS cluster is live and OpenAI inference endpoint returned tokens successfully!" \
  || { echo -e "\n❌ FAIL: no tokens in response."; exit 1; }
