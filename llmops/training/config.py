"""Hyperparameters and configuration for QLoRA fine-tuning."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class LoRAConfig:
    """LoRA and QLoRA fine-tuning hyperparameters."""

    # Model specifications
    base_model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"  # Lightweight default for versatile execution; swap to 7B in production
    output_dir: str = "artifacts/adapters/anime-stylist-lora"
    train_data_path: str = "data/curated/train.jsonl"
    val_data_path: str = "data/curated/val.jsonl"

    # LoRA Adapter settings
    r: int = 16  # Rank of decomposition matrices
    lora_alpha: int = 32  # Scaling factor
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

    # Training settings
    max_seq_length: int = 1024
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.05
    max_steps: int = 30
    num_train_epochs: int = 1
    logging_steps: int = 5
    save_steps: int = 15
    optim: str = "adamw_torch"

    # Quantization
    use_4bit: bool = True
    bits: int = 4
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True


TrainingConfig = LoRAConfig

