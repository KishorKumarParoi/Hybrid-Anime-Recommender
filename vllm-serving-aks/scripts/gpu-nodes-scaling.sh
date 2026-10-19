#!/usr/bin/env bash
# Scale the GPU node pool in / out. Use this to stop the GPU bill during a break, or to free
# the GPU while debugging a stuck pod, WITHOUT destroying the cluster.
#
# READ THIS BEFORE USING IT — on AKS, scale-to-zero is usually the WRONG choice:
#
#   scale to 0  ->  ~$0.125/hr  (system node keeps running; cluster survives; ~5-8 min to
#                                first token when you scale back out)
#   destroy     ->  $0.00/hr    (everything gone; ~10-15 min to rebuild from terraform)
#
# The AKS control plane is FREE (sku_tier = "Free"), so unlike a paid-control-plane cluster
# there is very little to preserve by keeping it alive. $0.125/hr is ~$3/day, ~$90/month —
# above the whole project budget. Rule of thumb:
#
#   stepping away < ~4 hrs   -> scale in   (saves $0.684/hr, cluster stays warm)
#   done for the day/longer  -> terraform destroy
#
# WHY A SCRIPT AND NOT TERRAFORM: node_count in aks.tf is 1. Scaling here via the CLI creates
# drift, and the next `terraform apply` will scale the pool straight back to 1. That is
# harmless but surprising — scale back OUT before running terraform, or expect apply to do it
# for you.
#
# Usage:
#   scripts/gpu-nodes-scaling.sh status   # what Azure currently thinks
#   scripts/gpu-nodes-scaling.sh in       # count -> 0  (~$0.81/hr -> ~$0.125/hr)
#   scripts/gpu-nodes-scaling.sh out      # count -> 1
set -uo pipefail

RG="${RG:-rg-vllm-serving-aks}"
CLUSTER="${CLUSTER:-vllm-serving-aks}"
POOL="${POOL:-gpu}"
ACTION="${1:-status}"

run() { echo "\$ $*"; "$@"; }

show() {
  echo; echo "==> Current state"
  run az aks nodepool show --resource-group "$RG" --cluster-name "$CLUSTER" --name "$POOL" \
    --query '{name:name, count:count, state:provisioningState, vm:vmSize, os:osSku}' -o table
  run kubectl get nodes -l workload=gpu
}

case "$ACTION" in
  status) show ;;

  in|out)
    [ "$ACTION" = "in" ] && COUNT=0 || COUNT=1

    echo "==> Scaling node pool '${POOL}' to ${COUNT} (this cordons + drains on scale-in)"
    run az aks nodepool scale \
      --resource-group "$RG" --cluster-name "$CLUSTER" --name "$POOL" \
      --node-count "$COUNT" --output none || exit 1

    show

    if [ "$COUNT" -eq 0 ]; then
      echo; echo "GPU node released. Now billing ~\$0.125/hr for the system node only."
      echo "That is ~\$3/day — if you're done for the day, run terraform destroy instead (\$0)."
    else
      echo; echo "NOTE: the node is up, but the vllm pod still has to pull the ~11GB image and"
      echo "      re-download the weights (no PVC yet) — budget ~5-8 min to first token."
      echo "      Watch it with: bash scripts/verify.sh"
    fi

    echo; echo "REMINDER: aks.tf still declares node_count = 1. A 'terraform apply' while scaled"
    echo "          in will scale the pool back out to 1."
    ;;

  *) echo "Usage: $0 {status|in|out}"; exit 1 ;;
esac
