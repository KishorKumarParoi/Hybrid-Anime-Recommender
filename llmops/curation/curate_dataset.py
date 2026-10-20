"""Continuous Fine-Tuning Data Curation & Flywheel Engine.

Ingests interaction logs, applies PII scrubbing, quality gating,
formats into ChatML/ShareGPT format, and injects a 15% general
replay buffer to prevent catastrophic forgetting.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# PII Scrubbing regex patterns
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b")
API_KEY_PATTERN = re.compile(r"\b(?:sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_\-\.]{20,})\b")
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# General reasoning replay buffer seed (Prevents catastrophic forgetting)
GENERAL_REPLAY_SAMPLES: List[Dict[str, Any]] = [
    {
        "messages": [
            {"role": "system", "content": "You are a precise and helpful assistant."},
            {"role": "user", "content": "Explain the difference between supervised and unsupervised learning in two sentences."},
            {"role": "assistant", "content": "Supervised learning trains models on labeled input-output pairs to predict known outcomes. Unsupervised learning identifies hidden patterns and groupings within unlabeled data without predefined outputs."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "You are an analytical and concise logical reasoning assistant."},
            {"role": "user", "content": "If all cats are felines and all felines are mammals, are all cats mammals?"},
            {"role": "assistant", "content": "Yes. By the transitive property of deductive logic: since all cats are felines, and all felines are mammals, it follows necessarily that all cats are mammals."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "You are a software architecture expert."},
            {"role": "user", "content": "What is the primary benefit of dynamic LoRA adapters over full model duplication in LLM serving?"},
            {"role": "assistant", "content": "Dynamic LoRA allows a single frozen base model in GPU VRAM to serve multiple distinct task adapters on-the-fly, reducing GPU memory overhead by up to 90% and eliminating multi-instance compute costs."}
        ]
    }
]


class DatasetCurator:
    """Enterprise dataset curation flywheel for LLM fine-tuning."""

    def __init__(
        self,
        min_quality_score: float = 0.7,
        replay_buffer_ratio: float = 0.15,
        raw_data_path: str | Path | None = None,
        output_train_path: str | Path | None = None,
        output_val_path: str | Path | None = None,
    ) -> None:
        self.min_quality_score = min_quality_score
        self.replay_buffer_ratio = replay_buffer_ratio
        self.raw_data_path = Path(raw_data_path) if raw_data_path else None
        self.output_train_path = Path(output_train_path) if output_train_path else None
        self.output_val_path = Path(output_val_path) if output_val_path else None

    @staticmethod
    def scrub_pii(text: str) -> str:
        """Redact sensitive personally identifiable information (PII)."""
        text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        text = API_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)
        text = IP_PATTERN.sub("[REDACTED_IP]", text)
        return text

    def filter_quality(self, record: Dict[str, Any]) -> bool:
        """Filter out low-quality interactions, thumbs-down responses, or empty content."""
        if not record.get("accepted", True):
            return False

        score = record.get("score", record.get("quality_score", 1.0))
        if score < self.min_quality_score:
            return False

        prompt = record.get("prompt", "").strip()
        completion = record.get("completion", record.get("response", "")).strip()

        # Reject degenerate/short examples
        if len(prompt) < 5 or len(completion) < 15:
            return False

        return True

    # Alias for API compatibility
    passes_quality_filter = filter_quality

    def format_chatml(self, prompt: str, response: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Format a single prompt-response pair into ChatML messages."""
        sys_msg = system_prompt or (
            "You are an expert Anime Recommender & Domain Stylist with deep knowledge of narrative pacing, animation studios, and thematic tropes."
        )
        return {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": self.scrub_pii(prompt.strip())},
                {"role": "assistant", "content": self.scrub_pii(response.strip())},
            ]
        }

    def transform_to_chatml(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an internal interaction record to the standard ChatML messages structure."""
        system_prompt = record.get("system_prompt")
        prompt = record.get("prompt", "")
        completion = record.get("completion", record.get("response", ""))
        return self.format_chatml(prompt, completion, system_prompt)

    def process_dataset(
        self,
        raw_records: List[Dict[str, Any]],
        val_ratio: float = 0.15,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filters, sanitizes, and balances domain data with general replay samples."""
        curated: List[Dict[str, Any]] = []

        for record in raw_records:
            if self.filter_quality(record):
                chatml_entry = self.transform_to_chatml(record)
                curated.append(chatml_entry)

        domain_count = len(curated)
        logger.info("Quality filtration retained %d / %d samples", domain_count, len(raw_records))

        replay_count = 0
        # Inject general replay buffer to prevent catastrophic forgetting
        if curated and self.replay_buffer_ratio > 0:
            target_replay_count = max(1, int(len(curated) * self.replay_buffer_ratio))
            replay_samples = (GENERAL_REPLAY_SAMPLES * ((target_replay_count // len(GENERAL_REPLAY_SAMPLES)) + 1))[:target_replay_count]
            curated.extend(replay_samples)
            replay_count = len(replay_samples)
            logger.info("Injected %d general replay samples (ratio: %.2f)", replay_count, self.replay_buffer_ratio)

        # Train / Validation Split
        val_size = max(1, int(len(curated) * val_ratio)) if len(curated) > 1 else 0
        train_data = curated[:-val_size] if val_size > 0 else curated
        val_data = curated[-val_size:] if val_size > 0 else []

        return train_data, val_data

    def run(self) -> Dict[str, Any]:
        """Execute the curation pipeline using initialized file paths."""
        if not self.raw_data_path or not self.raw_data_path.exists():
            raise FileNotFoundError(f"Raw data path {self.raw_data_path} not found")

        records: List[Dict[str, Any]] = []
        with open(self.raw_data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

        train_data, val_data = self.process_dataset(records)

        if self.output_train_path:
            save_jsonl(train_data, self.output_train_path)
        if self.output_val_path:
            save_jsonl(val_data, self.output_val_path)

        total_samples = len(train_data) + len(val_data)
        domain_samples = sum(1 for d in (train_data + val_data) if "You are a software" not in d["messages"][0]["content"] and "You are a precise" not in d["messages"][0]["content"] and "logical reasoning" not in d["messages"][0]["content"])
        replay_samples = total_samples - domain_samples

        return {
            "total_curated_samples": total_samples,
            "train_samples": len(train_data),
            "val_samples": len(val_data),
            "curated_domain_samples": domain_samples,
            "replay_samples_added": replay_samples,
        }



def save_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save records in JSONL format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("Saved %d samples to %s", len(data), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate and preprocess dataset for LoRA fine-tuning")
    parser.add_argument("--input", type=str, default="data/raw/sample_interactions.jsonl", help="Input raw JSONL file")
    parser.add_argument("--output-dir", type=str, default="data/curated", help="Directory for output train/val splits")
    parser.add_argument("--min-quality", type=float, default=0.7, help="Minimum quality rating")
    parser.add_argument("--replay-ratio", type=float, default=0.15, help="Replay buffer ratio")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.warning("Input file %s does not exist. Creating synthetic seed dataset.", input_path)
        input_path.parent.mkdir(parents=True, exist_ok=True)
        # Create default seed data
        seed_data = [
            {
                "prompt": "Recommend me an anime like Steins;Gate with complex time travel and psychological suspense.",
                "completion": "If you loved Steins;Gate, prioritize **Erased (Boku dake ga Inai Machi)** and **Madoka Magica**. For hard sci-fi causality, watch **Link Click (Shiguang Dailiren)**—it nails the high-stakes Butterfly Effect mechanics with brilliant emotional payoffs.",
                "score": 0.95,
                "accepted": True
            },
            {
                "prompt": "I want a dark cyberpunk aesthetic like Ghost in the Shell. What should I watch next?",
                "completion": "Watch **Cyberpunk: Edgerunners** (Studio Trigger) for visceral neon-drenched chrome action, followed by **Psycho-Pass** for philosophical dystopian inquiries into automated morality.",
                "score": 0.92,
                "accepted": True
            },
            {
                "prompt": "Bad anime query bad bad",
                "completion": "Too short",
                "score": 0.2,
                "accepted": False
            }
        ]
        save_jsonl(seed_data, input_path)

    raw_records: List[Dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_records.append(json.loads(line))

    curator = DatasetCurator(min_quality_score=args.min_quality, replay_buffer_ratio=args.replay_ratio)
    train_set, val_set = curator.process_dataset(raw_records)

    out_dir = Path(args.output_dir)
    save_jsonl(train_set, out_dir / "train.jsonl")
    save_jsonl(val_set, out_dir / "val.jsonl")
    logger.info("Dataset curation successfully completed. Train: %d, Val: %d", len(train_set), len(val_set))


if __name__ == "__main__":
    main()
