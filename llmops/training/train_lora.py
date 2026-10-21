"""
Production LoRA / QLoRA Fine-Tuning Pipeline.

Trains parameter-efficient adapters on top of frozen LLM foundations, incorporating:
- RSLoRA (Rank-Stabilized LoRA: scaling by alpha / sqrt(r))
- NeFTune (Noisy Embedding Fine-Tuning)
- Completion-Only Loss Masking (loss calculated strictly on assistant response tokens)
- Dynamic hardware & optimizer negotiation (paged_adamw_8bit on CUDA, adamw_torch on MPS/CPU)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    TrainingArguments,
)
from trl import SFTTrainer

from llmops.training.config import LoRAConfig, get_preset_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LoRATrainer")


def get_hardware_and_optimizer(requested_optim: str) -> Tuple[str, torch.dtype, str]:
    """
    Detects hardware capabilities and selects the optimal precision and optimizer.
    
    Returns:
        (device_map, compute_dtype, negotiated_optimizer)
    """
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        logger.info("CUDA detected: %s (Compute Capability: %s)", gpu_name, capability)
        # Ampere (SM 8.0), Ada Lovelace (SM 8.9), Hopper (SM 9.0) support bfloat16
        if capability[0] >= 8:
            dtype = torch.bfloat16
        else:
            dtype = torch.float16
        optim = requested_optim  # e.g., paged_adamw_8bit or adamw_torch
        return "auto", dtype, optim
    elif torch.backends.mps.is_available():
        logger.info("Apple Silicon MPS detected (switching optimizer to adamw_torch, dtype float32)")
        return "mps", torch.float32, "adamw_torch"
    else:
        logger.info("Running on CPU (switching optimizer to adamw_torch, dtype float32)")
        return "cpu", torch.float32, "adamw_torch"


def tokenize_with_completion_masking(
    sample: Dict[str, Any],
    tokenizer: Any,
    max_seq_length: int = 1024,
) -> Dict[str, List[int]]:
    """
    Tokenizes ChatML conversation and applies label masking (-100) to system and user prompt tokens.
    Gradients and cross-entropy loss are computed exclusively on the assistant response.
    """
    messages = sample.get("messages", [])
    if len(messages) < 2:
        return {"input_ids": [], "labels": [], "attention_mask": []}

    # Format prompt (system + user) and full conversation
    prompt_text = tokenizer.apply_chat_template(messages[:-1], add_generation_prompt=True, tokenize=False)
    full_text = tokenizer.apply_chat_template(messages, tokenize=False)

    prompt_ids = tokenizer.encode(prompt_text, add_special_tokens=False)
    full_ids = tokenizer.encode(full_text, add_special_tokens=False)

    # Truncate if exceeding max length
    if len(full_ids) > max_seq_length:
        full_ids = full_ids[:max_seq_length]
        prompt_len = min(len(prompt_ids), max_seq_length)
    else:
        prompt_len = len(prompt_ids)

    # Set labels: -100 for prompt tokens, token IDs for assistant completion tokens
    labels = [-100] * prompt_len + full_ids[prompt_len:]

    return {
        "input_ids": full_ids,
        "labels": labels,
        "attention_mask": [1] * len(full_ids),
    }


def train_lora_pipeline(cfg: LoRAConfig, dry_run: bool = False) -> Path:
    """Executes the fine-tuning workflow and saves adapter weights."""
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        logger.info("[DRY RUN] Simulating fine-tuning execution and writing mock adapter...")
        adapter_config = {
            "base_model_name_or_path": cfg.base_model_id,
            "r": cfg.r,
            "lora_alpha": cfg.lora_alpha,
            "lora_dropout": cfg.lora_dropout,
            "use_rslora": cfg.use_rslora,
            "target_modules": cfg.target_modules,
            "peft_type": "LORA",
            "task_type": "CAUSAL_LM",
        }
        with (output_dir / "adapter_config.json").open("w", encoding="utf-8") as f:
            json.dump(adapter_config, f, indent=2)

        # Mock adapter tensor file
        dummy_weights = {"dummy_lora_a": torch.zeros((16, 64)), "dummy_lora_b": torch.zeros((64, 16))}
        torch.save(dummy_weights, output_dir / "adapter_model.bin")

        metadata = {
            "status": "COMPLETED_SIMULATION",
            "mode": "dry_run_simulation",
            "steps": cfg.max_steps,
            "r": cfg.r,
            "lora_alpha": cfg.lora_alpha,
            "use_rslora": cfg.use_rslora,
            "neftune_noise_alpha": cfg.neftune_noise_alpha,
            "loss_masking": "completion_only" if cfg.mask_prompt_loss else "full_sequence",
            "effective_batch_size": cfg.effective_batch_size,
            "trainable_params": 1640000,
            "trainable_percentage": 0.32,
            "base_model": cfg.base_model_id,
        }
        with (output_dir / "training_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info("[DRY RUN] Mock adapter successfully generated at %s", output_dir)
        return output_dir

    logger.info("Initializing Tokenizer for %s", cfg.base_model_id)
    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Hardware & Quantization setup
    device_map, compute_dtype, resolved_optim = get_hardware_and_optimizer(cfg.optim)
    bnb_config = None
    if torch.cuda.is_available() and cfg.use_4bit:
        logger.info("Applying 4-bit NormalFloat (NF4) quantization")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=cfg.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=cfg.bnb_4bit_use_double_quant,
        )

    logger.info("Loading foundational base model: %s", cfg.base_model_id)
    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model_id,
        quantization_config=bnb_config,
        device_map=device_map if torch.cuda.is_available() else None,
        torch_dtype=compute_dtype,
        trust_remote_code=True,
    )

    if torch.cuda.is_available() and cfg.use_4bit:
        model = prepare_model_for_kbit_training(model)

    # Attach LoRA adapter with Rank-Stabilized LoRA (RSLoRA)
    logger.info(
        "Configuring PEFT LoRA (r=%d, alpha=%d, use_rslora=%s, target_modules=%s)",
        cfg.r,
        cfg.lora_alpha,
        cfg.use_rslora,
        cfg.target_modules,
    )
    peft_config = LoraConfig(
        r=cfg.r,
        lora_alpha=cfg.lora_alpha,
        use_rslora=cfg.use_rslora,
        target_modules=cfg.target_modules,
        lora_dropout=cfg.lora_dropout,
        bias=cfg.bias,
        task_type=cfg.task_type,
    )
    model = get_peft_model(model, peft_config)

    trainable_params, all_params = model.get_nb_trainable_parameters()
    logger.info(
        "Trainable parameters: %d / %d (%.3f%% of total model)",
        trainable_params,
        all_params,
        100 * trainable_params / all_params,
    )

    # Load dataset
    logger.info("Loading dataset from %s", cfg.train_data_path)
    raw_dataset = load_dataset("json", data_files={"train": cfg.train_data_path, "validation": cfg.val_data_path})

    if cfg.mask_prompt_loss:
        logger.info("Applying Completion-Only Loss Masking (-100 for prompt tokens)")
        train_dataset = raw_dataset["train"].map(
            lambda x: tokenize_with_completion_masking(x, tokenizer, cfg.max_seq_length),
            remove_columns=raw_dataset["train"].column_names,
        )
        val_dataset = raw_dataset["validation"].map(
            lambda x: tokenize_with_completion_masking(x, tokenizer, cfg.max_seq_length),
            remove_columns=raw_dataset["validation"].column_names,
        )
    else:
        train_dataset = raw_dataset["train"]
        val_dataset = raw_dataset["validation"]

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        lr_scheduler_type=cfg.lr_scheduler_type,
        warmup_ratio=cfg.warmup_ratio,
        weight_decay=cfg.weight_decay,
        max_grad_norm=cfg.max_grad_norm,
        max_steps=cfg.max_steps,
        logging_steps=cfg.logging_steps,
        save_steps=cfg.save_steps,
        save_total_limit=cfg.save_total_limit,
        optim=resolved_optim,
        neftune_noise_alpha=cfg.neftune_noise_alpha,
        fp16=(compute_dtype == torch.float16),
        bf16=(compute_dtype == torch.bfloat16),
        save_strategy="steps",
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, pad_to_multiple_of=8)

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        max_seq_length=cfg.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
    )

    logger.info("Starting fine-tuning training loop (Effective Batch Size: %d)...", cfg.effective_batch_size)
    trainer.train()

    logger.info("Saving trained LoRA adapter to %s", output_dir)
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metadata = {
        "status": "COMPLETED",
        "steps": cfg.max_steps,
        "effective_batch_size": cfg.effective_batch_size,
        "trainable_params": trainable_params,
        "trainable_percentage": round(100 * trainable_params / all_params, 4),
        "base_model": cfg.base_model_id,
        "rank": cfg.r,
        "alpha": cfg.lora_alpha,
        "use_rslora": cfg.use_rslora,
        "neftune_noise_alpha": cfg.neftune_noise_alpha,
        "loss_masking": "completion_only" if cfg.mask_prompt_loss else "full_sequence",
        "optimizer": resolved_optim,
    }
    with (output_dir / "training_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training pipeline finished successfully!")
    return output_dir


class LoRATrainer:
    """Object-oriented wrapper around the LoRA / QLoRA training pipeline."""

    def __init__(self, config: LoRAConfig | None = None, dry_run: bool = False):
        self.config = config or LoRAConfig()
        self.dry_run = dry_run

    def train(self) -> Dict[str, Any]:
        output_dir = train_lora_pipeline(self.config, dry_run=self.dry_run)
        meta_file = Path(output_dir) / "training_metadata.json"
        metadata = {}
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                metadata = json.load(f)
        return {
            "status": "COMPLETED_SIMULATION" if self.dry_run else "COMPLETED",
            "output_dir": str(output_dir),
            **metadata,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run production QLoRA fine-tuning with RSLoRA, NeFTune, and Loss Masking")
    parser.add_argument("--persona", choices=["anime-critic", "anime-stylist", "default"], default="default", help="Preset configuration persona")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct", help="Hugging Face base model ID")
    parser.add_argument("--output-dir", type=str, default="artifacts/adapters/anime-stylist-lora", help="Output directory for adapter")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum training steps")
    parser.add_argument("--rslora", action="store_true", default=True, help="Enable Rank-Stabilized LoRA")
    parser.add_argument("--neftune", type=float, default=5.0, help="NeFTune noise alpha")
    parser.add_argument("--dry-run", action="store_true", help="Simulate training without downloading full weights")
    args = parser.parse_args()

    if args.persona != "default":
        cfg = get_preset_config(args.persona)
    else:
        cfg = LoRAConfig(
            base_model_id=args.base_model,
            output_dir=args.output_dir,
            max_steps=args.max_steps,
            use_rslora=args.rslora,
            neftune_noise_alpha=args.neftune,
        )

    train_lora_pipeline(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
