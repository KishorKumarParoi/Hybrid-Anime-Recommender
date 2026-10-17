"""
Kubeflow Pipelines (KFP v2) Pipeline Definition for Hybrid Anime Recommender System.
Compiles into an Argo / Kubeflow Pipelines execution graph (YAML).
"""

import os
from kfp import dsl, compiler
from kubeflow.components import (
    data_ingestion_op,
    data_preprocessing_op,
    model_training_op,
    model_evaluation_op,
    model_deployment_op,
)


@dsl.pipeline(
    name="anime-recommender-training-pipeline",
    description="Automated End-to-End Deep Learning Training and Quality Gated Deployment for Hybrid Anime Recommender",
)
def anime_recommender_pipeline(
    gcs_bucket: str = "project-53d8ce01-b0e0-4f8b-94c-mlops-artifacts",
    raw_data_path: str = "data/raw/animelist.csv",
    min_user_ratings: int = 50,
    min_anime_ratings: int = 5,
    test_size: float = 0.1,
    embedding_dim: int = 128,
    epochs: int = 5,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    max_acceptable_loss: float = 0.50,
    deployment_name: str = "ml-app",
    namespace: str = "default",
):
    """
    End-to-end Kubeflow DAG:
    1. Ingestion: Download / read raw anime interaction logs.
    2. Preprocessing: Filtering, encoding, scaling, train/test split.
    3. Training: Neural Matrix Factorization / Collaborative Filtering (RecommenderNet).
    4. Evaluation: Loss/MAE validation against production quality gate.
    5. Deployment: Trigger deployment rollover if evaluation gate passes.
    """

    # 1. Ingestion Step
    ingestion_step = data_ingestion_op(
        gcs_bucket=gcs_bucket,
        raw_data_path=raw_data_path,
    ).set_display_name("1. Ingest Raw Interactions")

    # 2. Preprocessing Step
    preprocessing_step = data_preprocessing_op(
        raw_dataset=ingestion_step.outputs["raw_dataset"],
        min_user_ratings=min_user_ratings,
        min_anime_ratings=min_anime_ratings,
        test_size=test_size,
    ).set_display_name("2. Preprocess & Encode Features")

    # 3. Model Training Step
    training_step = model_training_op(
        processed_train=preprocessing_step.outputs["processed_train"],
        encoders=preprocessing_step.outputs["encoders"],
        embedding_dim=embedding_dim,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
    ).set_display_name("3. Train RecommenderNet (TF/Keras)")

    # 4. Model Evaluation Step
    evaluation_step = model_evaluation_op(
        trained_model=training_step.outputs["trained_model"],
        processed_test=preprocessing_step.outputs["processed_test"],
        max_acceptable_loss=max_acceptable_loss,
    ).set_display_name("4. Evaluate & Quality Gate")

    # 5. Deployment Step
    deployment_step = model_deployment_op(
        deploy_decision=evaluation_step.outputs["deploy_decision"],
        deployment_name=deployment_name,
        namespace=namespace,
    ).set_display_name("5. Rolling Deployment Rollover")


def compile_pipeline(output_yaml: str = None) -> str:
    """Compiles the Kubeflow pipeline to a standalone KFP v2 YAML manifest."""
    if output_yaml is None:
        output_yaml = os.path.join(
            os.path.dirname(__file__), "anime_training_pipeline.yaml"
        )
    os.makedirs(os.path.dirname(output_yaml), exist_ok=True)
    compiler.Compiler().compile(
        pipeline_func=anime_recommender_pipeline,
        package_path=output_yaml,
    )
    print(f"[✓] Successfully compiled Kubeflow pipeline to: {output_yaml}")
    return output_yaml


if __name__ == "__main__":
    compile_pipeline()
