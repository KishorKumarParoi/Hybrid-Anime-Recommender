"""
Hyperparameters and Configuration Engine for Production QLoRA / PEFT Fine-Tuning.

Incorporates state-of-the-art fine-tuning architectures:
- RSLoRA (Rank-Stabilized LoRA): Scaled by alpha/sqrt(r) to prevent gradient instability.
- NeFTune (Noisy Embedding Fine-Tuning): Injects uniform noise into embeddings to boost generalizability.
- Completion-Only Loss Masking: Masks prompt tokens with -100 to calculate loss strictly on assistant completions.
- Paged Optimizer Fallback: Automatically negotiates paged_adamw_8bit on CUDA and adamw_torch on CPU/Apple MPS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LoRAConfig:
    """LoRA and QLoRA fine-tuning hyperparameters."""

    # Model specifications
    base_model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"  # Lightweight default for versatile CI/CD; swap to 7B in production
    output_dir: str = "artifacts/adapters/anime-stylist-lora"
    train_data_path: str = "data/curated/train.jsonl"
    val_data_path: str = "data/curated/val.jsonl"
    attn_implementation: str = "sdpa"  # Scaled Dot Product Attention (PyTorch 2.x)

    # LoRA / PEFT Architecture
    r: int = 16  # Rank of decomposition matrices
    lora_alpha: int = 32  # Scaling factor
    use_rslora: bool = True  # Rank-Stabilized LoRA: scales by alpha / sqrt(r) instead of alpha / r
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    target_modules: List[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )

    # Training settings & Optimization
    max_seq_length: int = 1024
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4  # Effective batch size = 2 * 4 = 8
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    weight_decay: float = 0.01  # Prevents adapter weight divergence
    max_grad_norm: float = 0.3  # Gradient clipping essential for 4-bit backpropagation stability
    max_steps: int = 30
    num_train_epochs: int = 1
    logging_steps: int = 5
    save_steps: int = 15
    save_total_limit: int = 2
    optim: str = "paged_adamw_8bit"  # Auto-falls back to adamw_torch if CUDA is absent

    # Advanced Regularization & Loss Masking
    neftune_noise_alpha: float = 5.0  # Injects noise into embeddings during SFT to prevent template overfitting
    mask_prompt_loss: bool = True  # Ignore prompt tokens (label = -100) and compute loss exclusively on assistant response

    # Quantization (QLoRA)
    use_4bit: bool = True
    bits: int = 4
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    @property
    def effective_batch_size(self) -> int:
        """Computes the effective global batch size."""
        return self.per_device_train_batch_size * self.gradient_accumulation_steps


# Alias for backwards compatibility
TrainingConfig = LoRAConfig


def get_preset_config(persona: str = "anime-stylist") -> LoRAConfig:
    """
    Factory creating curated, battle-tested hyperparameter profiles for specific domain tasks.
    
    Args:
        persona: One of 'anime-critic', 'anime-stylist', or 'general-assistant'.
    """
    if persona == "anime-critic":
        # Analytical, deep narrative and sakuga critique requires higher rank and lower learning rate
        return LoRAConfig(
            output_dir="artifacts/adapters/anime-critic-lora",
            r=32,
            lora_alpha=64,
            use_rslora=True,
            learning_rate=1.5e-4,
            neftune_noise_alpha=3.0,
            max_seq_length=1536,
        )
    elif persona == "anime-stylist":
        # Conversational otaku persona benefits from higher NeFTune noise for stylistic variance
        return LoRAConfig(
            output_dir="artifacts/adapters/anime-stylist-lora",
            r=16,
            lora_alpha=32,
            use_rslora=True,
            learning_rate=2e-4,
            neftune_noise_alpha=6.0,
            max_seq_length=1024,
        )
    else:
        return LoRAConfig()
