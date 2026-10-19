#!/usr/bin/env bash
# Project verification for vLLM on GKE
# Proves vLLM serves tokens on the Google Cloud GPU and reads GPU memory.
set -uo pipefail

MODEL="Qwen/Qwen2.5-7B-Instruct-AWQ"
PORT=8000
PF_PID=""
cleanup() { [ -n "$PF_PID" ] && kill "$PF_PID" 2>/dev/null || true; }
trap cleanup EXIT

run() { echo "\$ $*"; "$@"; }

echo "==> [0/4] GKE Cluster context"
run kubectl config current-context

echo; echo "==> [1/4] Waiting for the vLLM pod to be Ready (pulls image + model weights)..."
run kubectl wait --for=condition=ready pod -l app=vllm --timeout=900s || {
  echo "FAIL: pod never became Ready. Check: kubectl get pods -l app=vllm ; kubectl logs deploy/vllm"
  exit 1
}

echo; echo "==> [2/4] Opening port-forward localhost:${PORT} -> svc/vllm:8000"
kubectl port-forward "svc/vllm" "${PORT}:8000" >/tmp/vllm-gke-pf.log 2>&1 &
PF_PID=$!
echo "    waiting for the tunnel to answer..."
for i in $(seq 1 30); do
  curl -sf "http://localhost:${PORT}/v1/models" >/dev/null 2>&1 && break
  sleep 1
  [ "$i" = "30" ] && { echo "FAIL: port-forward never came up. See /tmp/vllm-gke-pf.log"; exit 1; }
done
echo "    tunnel is up."

echo; echo "==> [3/4] POST /v1/completions (Inference checkpoint)"
RESP=$(curl -s "http://localhost:${PORT}/v1/completions" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"Hello, my name is\",\"max_tokens\":32,\"temperature\":0}")
echo "$RESP" | (jq . 2>/dev/null || cat)
echo "$RESP" | grep -q '"text"' \
  && echo "PASS: API returned generated tokens from GKE GPU." \
  || { echo "FAIL: no tokens in response."; exit 1; }

echo; echo "==> [4/4] GPU hardware verification (nvidia-smi)"
run kubectl exec deploy/vllm -- nvidia-smi

echo; echo "==> KV-cache and concurrency metrics from startup logs"
kubectl logs deploy/vllm 2>&1 | grep -iE "Available KV cache memory|GPU KV cache size|Maximum concurrency" | tail -3

echo; echo "✅ GKE vLLM verification complete!"
