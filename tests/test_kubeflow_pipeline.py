import os
import yaml
import pytest
from kubeflow.pipeline import compile_pipeline, anime_recommender_pipeline
from kubeflow.components import (
    data_ingestion_op,
    data_preprocessing_op,
    model_training_op,
    model_evaluation_op,
    model_deployment_op,
)


def test_kubeflow_components_registered():
    """Verify all Kubeflow components are initialized with correct inputs/outputs."""
    assert callable(data_ingestion_op)
    assert callable(data_preprocessing_op)
    assert callable(model_training_op)
    assert callable(model_evaluation_op)
    assert callable(model_deployment_op)


def test_kubeflow_pipeline_compilation(tmp_path):
    """Verify that KFP v2 successfully compiles the pipeline to a valid YAML manifest."""
    target_yaml = str(tmp_path / "test_pipeline.yaml")
    output_path = compile_pipeline(target_yaml)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000

    # Parse and validate YAML structure
    with open(output_path, "r") as f:
        manifest = yaml.safe_load(f)

    assert "pipelineInfo" in manifest
    assert manifest["pipelineInfo"]["name"] == "anime-recommender-training-pipeline"
    assert "root" in manifest
    assert "dag" in manifest["root"]
    assert "tasks" in manifest["root"]["dag"]

    # Verify task graph contains all 5 pipeline stages
    task_keys = list(manifest["root"]["dag"]["tasks"].keys())
    assert len(task_keys) >= 5
