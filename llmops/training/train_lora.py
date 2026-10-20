"""Production LoRA / QLoRA Fine-Tuning Pipeline.

Trains parameter-efficient adapters on top of frozen LLM foundations,
tracking loss, gradient updates, and exporting standardized adapter artifacts.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

from llmops.training.config import LoRAConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_device_map() -> Tuple[str, torch.dtype]:
    """Detect available compute hardware."""
    if torch.cuda.is_available():
        logger.info("CUDA detected: %s", torch.cuda.get_device_name(0))
        return "auto", torch.bfloat16
    elif torch.backends.mps.is_available():
        logger.info("Apple Silicon MPS detected")
        return "mps", torch.float32
    else:
        logger.info("Running on CPU")
        return "cpu", torch.float32


def format_chatml_prompt(sample: Dict[str, Any], tokenizer: Any) -> Dict[str, str]:
    """Formats ChatML message records into training text using model tokenizer chat template."""
    messages = sample.get("messages", [])
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    else:
        # Fallback standard ChatML formatting
        text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    return {"text": text}


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
            "target_modules": cfg.target_modules,
            "peft_type": "LORA",
            "task_type": "CAUSAL_LM"
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
            "trainable_params": 1640000,
            "trainable_percentage": 0.32,
            "base_model": cfg.base_model_id
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
    device_map, compute_dtype = get_device_map()
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

    # Attach LoRA adapter
    peft_config = LoraConfig(
        r=cfg.r,
        lora_alpha=cfg.lora_alpha,
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
    train_dataset = raw_dataset["train"].map(lambda x: format_chatml_prompt(x, tokenizer))
    val_dataset = raw_dataset["validation"].map(lambda x: format_chatml_prompt(x, tokenizer))

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        warmup_ratio=cfg.warmup_ratio,
        max_steps=cfg.max_steps,
        logging_steps=cfg.logging_steps,
        save_steps=cfg.save_steps,
        optim=cfg.optim,
        fp16=(compute_dtype == torch.float16),
        bf16=(compute_dtype == torch.bfloat16),
        save_strategy="steps",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=cfg.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
    )

    logger.info("Starting fine-tuning training loop...")
    trainer.train()

    logger.info("Saving trained LoRA adapter to %s", output_dir)
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    metadata = {
        "status": "completed",
        "steps": cfg.max_steps,
        "trainable_params": trainable_params,
        "trainable_percentage": round(100 * trainable_params / all_params, 4),
        "base_model": cfg.base_model_id,
        "rank": cfg.r,
        "alpha": cfg.lora_alpha,
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
    parser = argparse.ArgumentParser(description="Run QLoRA / LoRA fine-tuning for anime stylist adapter")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct", help="Hugging Face base model ID")
    parser.add_argument("--output-dir", type=str, default="artifacts/adapters/anime-stylist-lora", help="Output directory for adapter")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum training steps")
    parser.add_argument("--dry-run", action="store_true", help="Simulate training without downloading full weights")
    args = parser.parse_args()

    cfg = LoRAConfig(
        base_model_id=args.base_model,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
    )
    train_lora_pipeline(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
