"""
Integration and Unit Tests for the LLMOps Continuous Fine-Tuning and Dynamic Multi-LoRA Serving Pipeline.
"""

import json
from pathlib import Path
import pytest
import yaml

from llmops.curation.curate_dataset import DatasetCurator
from llmops.training.config import TrainingConfig
from llmops.training.train_lora import LoRATrainer
from llmops.evals.eval_adapter import AdapterEvaluator
from llmops.client.multilora_client import MultiLoRAClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDatasetCuration:
    """Tests for PII scrubbing, quality filtering, and replay buffer data curation."""

    def test_pii_scrubbing(self):
        curator = DatasetCurator()
        text_with_pii = (
            "Contact me at otaku99@gmail.com or 555-123-4567. "
            "My key is sk-live1234567890abcdef1234567890 and IP is 192.168.1.1."
        )
        cleaned = curator.scrub_pii(text_with_pii)
        assert "otaku99@gmail.com" not in cleaned
        assert "[REDACTED_EMAIL]" in cleaned
        assert "555-123-4567" not in cleaned
        assert "[REDACTED_PHONE]" in cleaned
        assert "sk-live1234567890" not in cleaned
        assert "[REDACTED_API_KEY]" in cleaned
        assert "192.168.1.1" not in cleaned
        assert "[REDACTED_IP]" in cleaned

    def test_quality_filtering(self):
        curator = DatasetCurator()
        high_quality = {
            "prompt": "Recommend me an anime with deep lore.",
            "response": "Consider watching Shinsekai Yori (From the New World).",
            "quality_score": 0.95,
        }
        low_quality = {
            "prompt": "hi",
            "response": "ok",
            "quality_score": 0.40,
        }
        assert curator.passes_quality_filter(high_quality) is True
        assert curator.passes_quality_filter(low_quality) is False

    def test_chatml_conversion(self):
        curator = DatasetCurator()
        sample = {
            "prompt": "What makes Mob Psycho 100 great?",
            "response": "The fluid sakuga animation by Studio Bones and emotional core.",
        }
        chatml = curator.format_chatml(sample["prompt"], sample["response"])
        assert "messages" in chatml
        assert len(chatml["messages"]) == 3
        assert chatml["messages"][0]["role"] == "system"
        assert chatml["messages"][1]["role"] == "user"
        assert chatml["messages"][2]["role"] == "assistant"
        assert "Studio Bones" in chatml["messages"][2]["content"]

    def test_curation_run_and_split(self, tmp_path):
        raw_file = tmp_path / "raw.jsonl"
        with open(raw_file, "w") as f:
            for i in range(10):
                f.write(json.dumps({
                    "prompt": f"Anime query {i}?",
                    "response": f"Detailed analytical response {i} with sakuga commentary.",
                    "quality_score": 0.92,
                }) + "\n")

        train_file = tmp_path / "train.jsonl"
        val_file = tmp_path / "val.jsonl"
        curator = DatasetCurator(
            raw_data_path=str(raw_file),
            output_train_path=str(train_file),
            output_val_path=str(val_file),
            replay_buffer_ratio=0.20,
        )
        summary = curator.run()
        assert summary["curated_domain_samples"] == 10
        assert summary["replay_samples_added"] > 0
        assert train_file.exists()
        assert val_file.exists()


class TestLoRATraining:
    """Tests for QLoRA training configuration and artifact export."""

    def test_training_config_defaults(self):
        config = TrainingConfig()
        assert config.r == 16
        assert config.lora_alpha == 32
        assert config.bits == 4
        assert "q_proj" in config.target_modules
        assert "v_proj" in config.target_modules

    def test_simulation_training_run(self, tmp_path):
        adapter_output = tmp_path / "test-adapter"
        config = TrainingConfig(
            output_dir=str(adapter_output),
            num_train_epochs=1,
            r=16,
            lora_alpha=32,
        )
        trainer = LoRATrainer(config=config, dry_run=True)
        summary = trainer.train()

        assert summary["status"] == "COMPLETED_SIMULATION"
        assert adapter_output.exists()
        assert (adapter_output / "adapter_config.json").exists()
        assert (adapter_output / "training_metadata.json").exists()

        with open(adapter_output / "adapter_config.json") as f:
            cfg = json.load(f)
            assert cfg["r"] == 16
            assert cfg["lora_alpha"] == 32


class TestEvaluationAndGating:
    """Tests for automated evaluation rubric and deployment gating."""

    def test_evaluator_scoring(self, tmp_path):
        report_path = tmp_path / "eval_report.json"
        evaluator = AdapterEvaluator(
            report_path=str(report_path),
            pass_threshold=0.85,
        )
        report = evaluator.evaluate()

        assert "composite_score" in report
        assert report["composite_score"] >= 0.0
        assert report["status"] in ["APPROVED_FOR_DEPLOYMENT", "REJECTED_BELOW_THRESHOLD"]
        assert "dimensions" in report
        assert "domain_nuance" in report["dimensions"]
        assert "json_schema_adherence" in report["dimensions"]
        assert "reasoning_depth" in report["dimensions"]
        assert "general_retention" in report["dimensions"]
        assert report_path.exists()


class TestMultiLoRAClient:
    """Tests for the dynamic Multi-LoRA vLLM client in mock and router modes."""

    def test_client_mock_health_and_models(self):
        client = MultiLoRAClient(mock_mode=True)
        assert client.health_check() is True
        models = client.list_models()
        assert client.BASE_MODEL in models
        assert "anime-critic" in models
        assert "anime-stylist" in models
        client.close()

    def test_client_mock_generations(self):
        client = MultiLoRAClient(mock_mode=True)

        # 1. Base model
        res_base = client.generate("Recommend something", adapter=None)
        assert res_base.model_used == client.BASE_MODEL
        assert res_base.latency_ms > 0

        # 2. Anime Critic
        res_critic = client.generate_critique("Attack on Titan")
        assert res_critic.model_used == "anime-critic"
        assert "Critical Deconstruction" in res_critic.content or "Sakuga" in res_critic.content

        # 3. Anime Stylist
        res_stylist = client.generate_stylized_recommendation("Recommend cyberpunk anime")
        assert res_stylist.model_used == "anime-stylist"
        assert "Otaku Aesthetic" in res_stylist.content or "banquet" in res_stylist.content

        client.close()

    def test_client_benchmark_comparison(self):
        client = MultiLoRAClient(mock_mode=True)
        results = client.benchmark_comparison("Recommend anime with stunning visual direction")
        assert "base" in results
        assert "anime-critic" in results
        assert "anime-stylist" in results
        for k, v in results.items():
            assert v.latency_ms > 0
            assert len(v.content) > 20
        client.close()


class TestMultiCloudManifestParity:
    """Validates Multi-LoRA Kubernetes manifests across all cloud targets."""

    MANIFEST_PATHS = [
        PROJECT_ROOT / "llmops/serving/vllm-multilora-deployment.yaml",
        PROJECT_ROOT / "vllm-serving-aks/k8s/vllm-multilora-deployment.yaml",
        PROJECT_ROOT / "vllm-serving-gke/k8s/vllm-multilora-deployment.yaml",
        PROJECT_ROOT / "vllm-serving-aws/k8s/vllm-multilora-deployment.yaml",
    ]

    @pytest.mark.parametrize("manifest_path", MANIFEST_PATHS)
    def test_manifest_structure(self, manifest_path):
        assert manifest_path.exists(), f"Manifest {manifest_path} does not exist"

        with open(manifest_path) as f:
            docs = list(yaml.safe_load_all(f))

        deployment = next((d for d in docs if d and d.get("kind") == "Deployment"), None)
        service = next((d for d in docs if d and d.get("kind") == "Service"), None)

        assert deployment is not None, f"Deployment missing in {manifest_path}"
        assert service is not None, f"Service missing in {manifest_path}"

        # Verify deployment flags for Multi-LoRA
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        args = container.get("args", [])

        assert "--enable-lora" in args, f"--enable-lora missing in {manifest_path}"
        assert any("--max-loras" in a for a in args), f"--max-loras missing in {manifest_path}"
        assert "--lora-modules" in args, f"--lora-modules missing in {manifest_path}"
        assert container["resources"]["limits"]["nvidia.com/gpu"] == "1"

        # Verify Service
        assert service["spec"]["ports"][0]["port"] == 8000
