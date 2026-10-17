"""
Kubeflow Pipelines Runner for Hybrid Anime Recommender System.
CLI tool to trigger, monitor, and manage pipeline runs on remote or local Kubeflow clusters.
"""

import os
import sys
import argparse
from kubeflow.pipeline import compile_pipeline, anime_recommender_pipeline


def run_pipeline(
    host: str = None,
    experiment_name: str = "anime-recommender-experiments",
    run_name: str = None,
    compile_only: bool = False,
    epochs: int = 5,
    batch_size: int = 64,
    embedding_dim: int = 128,
    gcs_bucket: str = "project-53d8ce01-b0e0-4f8b-94c-mlops-artifacts",
):
    """
    Submits the Anime Recommender pipeline to a Kubeflow cluster or compiles it locally.
    """
    compiled_yaml = compile_pipeline()

    if compile_only:
        print(f"[✓] Pipeline compiled only. File ready at: {compiled_yaml}")
        return

    try:
        import kfp

        client_host = host or os.getenv("KUBEFLOW_HOST", "http://localhost:8080")
        print(f"Connecting to Kubeflow Pipelines cluster at: {client_host}")

        client = kfp.Client(host=client_host)

        # Create or fetch experiment
        try:
            experiment = client.create_experiment(name=experiment_name)
            experiment_id = experiment.experiment_id
            print(f"[✓] Created/retrieved experiment: {experiment_name} (ID: {experiment_id})")
        except Exception as exp_err:
            print(f"Using default experiment due to: {exp_err}")
            experiment_id = None

        pipeline_params = {
            "gcs_bucket": gcs_bucket,
            "raw_data_path": "data/raw/animelist.csv",
            "epochs": epochs,
            "batch_size": batch_size,
            "embedding_dim": embedding_dim,
            "min_user_ratings": 50,
            "min_anime_ratings": 5,
            "test_size": 0.1,
            "max_acceptable_loss": 0.50,
        }

        import time

        active_run_name = run_name or f"anime-rec-run-{int(time.time())}"
        print(f"Triggering pipeline run: '{active_run_name}'...")

        run_result = client.create_run_from_pipeline_package(
            pipeline_file=compiled_yaml,
            arguments=pipeline_params,
            run_name=active_run_name,
            experiment_name=experiment_name,
        )

        print(f"[✓] Pipeline run created successfully!")
        print(f"Run ID: {run_result.run_id}")
        if hasattr(run_result, "run_url"):
            print(f"Dashboard URL: {run_result.run_url}")

    except Exception as e:
        print(f"\n[!] Could not connect to live Kubeflow cluster: {e}")
        print("Note: If running outside a Kubeflow cluster, upload the compiled YAML directly:")
        print(f"       -> {compiled_yaml}")
        print("       to your Kubeflow Pipelines Web UI under 'Pipelines' -> 'Upload Pipeline'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit Kubeflow Pipeline for Anime Recommender")
    parser.add_argument("--host", type=str, default=None, help="Kubeflow Pipelines endpoint URL")
    parser.add_argument("--experiment", type=str, default="anime-recommender-experiments", help="Experiment name")
    parser.add_argument("--run-name", type=str, default=None, help="Pipeline run name")
    parser.add_argument("--compile-only", action="store_true", help="Only compile the YAML without submitting")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--embedding-dim", type=int, default=128, help="Embedding dimension")
    parser.add_argument("--bucket", type=str, default="project-53d8ce01-b0e0-4f8b-94c-mlops-artifacts", help="GCS Bucket")

    args = parser.parse_args()
    run_pipeline(
        host=args.host,
        experiment_name=args.experiment,
        run_name=args.run_name,
        compile_only=args.compile_only,
        epochs=args.epochs,
        batch_size=args.batch_size,
        embedding_dim=args.embedding_dim,
        gcs_bucket=args.bucket,
    )
