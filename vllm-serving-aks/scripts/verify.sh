#!/usr/bin/env bash
# Project verification: proves vLLM serves tokens on the GPU and reads GPU memory.
# Handles the port-forward + cleanup for you. Run from anywhere; kubectl uses its current context.
# Every command is printed (as "$ ...") right before it runs, so you can see what executes.
set -uo pipefail

MODEL="Qwen/Qwen2.5-7B-Instruct-AWQ"
PORT=8000
PF_PID=""
cleanup() { [ -n "$PF_PID" ] && kill "$PF_PID" 2>/dev/null || true; }
trap cleanup EXIT

# Helper: print a command, then run it.
run() { echo "\$ $*"; "$@"; }

echo "==> [0/4] Cluster context"
run kubectl config current-context

echo; echo "==> [1/4] Waiting for the vllm pod to be Ready (up to 15 min — first boot pulls ~11GB)..."
run kubectl wait --for=condition=ready pod -l app=vllm --timeout=900s || {
  echo "FAIL: pod never became Ready. Check: kubectl get pods -l app=vllm ; kubectl logs deploy/vllm"
  exit 1
}

echo; echo "==> [2/4] Opening port-forward localhost:${PORT} -> svc/vllm:8000 (in background)"
echo "\$ kubectl port-forward svc/vllm ${PORT}:8000   # backgrounded, logs to /tmp/vllm-pf.log"
kubectl port-forward "svc/vllm" "${PORT}:8000" >/tmp/vllm-pf.log 2>&1 &
PF_PID=$!
echo "    waiting for the tunnel to answer..."
echo "\$ curl -sf http://localhost:${PORT}/v1/models   # retried until it responds"
for i in $(seq 1 20); do
  curl -sf "http://localhost:${PORT}/v1/models" >/dev/null 2>&1 && break
  sleep 1
  [ "$i" = "20" ] && { echo "FAIL: port-forward never came up. See /tmp/vllm-pf.log"; exit 1; }
done
echo "    tunnel is up."

echo; echo "==> [3/4] POST /v1/completions (the checkpoint — must return tokens)"
echo "\$ curl -s http://localhost:${PORT}/v1/completions -H 'Content-Type: application/json' \\"
echo "       -d '{\"model\":\"${MODEL}\",\"prompt\":\"Hello, my name is\",\"max_tokens\":32,\"temperature\":0}'"
RESP=$(curl -s "http://localhost:${PORT}/v1/completions" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"Hello, my name is\",\"max_tokens\":32,\"temperature\":0}")
echo "$RESP" | (jq . 2>/dev/null || cat)
echo "$RESP" | grep -q '"text"' \
  && echo "PASS: API returned generated tokens." \
  || { echo "FAIL: no tokens in response (see above)."; exit 1; }

echo; echo "==> [4/4] GPU memory inside the pod (nvidia-smi)"
run kubectl exec deploy/vllm -- nvidia-smi

echo; echo "==> KV-cache evidence from startup logs"
echo "\$ kubectl logs deploy/vllm | grep -iE 'Available KV cache memory|GPU KV cache size|Maximum concurrency'"
kubectl logs deploy/vllm 2>&1 | grep -iE "Available KV cache memory|GPU KV cache size|Maximum concurrency" | tail -3

echo; echo "✅ Project verification complete."
echo "   Remember to tear down: cd terraform && terraform destroy"
