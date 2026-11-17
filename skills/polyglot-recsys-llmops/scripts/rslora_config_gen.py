#!/usr/bin/env python3
"""
RSLoRA (Rank-Stabilized LoRA) Config Generator
Calculates exact scaling factor alpha = gamma / sqrt(r) to stabilize gradient updates
across high-rank fine-tuning jobs (r >= 16, r = 32, r = 64).
"""
import math
import json
import sys

def generate_rslora_config(rank: int = 16, gamma: float = 16.0):
    scaling_factor = gamma / math.sqrt(rank)
    config = {
        "peft_type": "LORA",
        "r": rank,
        "lora_alpha": round(gamma * math.sqrt(rank)),
        "use_rslora": True,
        "scaling_factor": round(scaling_factor, 4),
        "target_modules": [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        "lora_dropout": 0.05,
        "bias": "none",
        "task_type": "CAUSAL_LM"
    }
    return config

if __name__ == "__main__":
    rank = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    cfg = generate_rslora_config(rank=rank)
    print(json.dumps(cfg, indent=2))
