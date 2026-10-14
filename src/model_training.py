import os
import json
from typing import Tuple, List, Optional, Any
from dotenv import load_dotenv
import joblib
import numpy as np

load_dotenv()
import tensorflow as tf
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
    TensorBoard,
)
from src.logger import get_logger
from src.custom_exception import CustomException
from src.base_model import BaseModel
from utils.common_functions import read_yaml
from config.paths_config import (
    CONFIG_PATH,
    PROCESSED_DIR,
    X_TRAIN_ARRAY,
    X_TEST_ARRAY,
    Y_TRAIN,
    Y_TEST,
    USER2USER_ENCODED,
    ANIME2ANIME_ENCODED,
    MODEL_DIR,
    WEIGHTS_DIR,
    MODEL_PATH,
    ANIME_WEIGHTS_PATH,
    USER_WEIGHTS_PATH,
    CHECKPOINT_FILE_PATH,
)

logger = get_logger(__name__)


class ModelTraining:
    """
    Manages data ingestion for training, model instantiation, training loops
    with callbacks, metric reporting, and normalized embedding weight persistence.
    """

    def __init__(self, data_path: str = PROCESSED_DIR, config_path: str = CONFIG_PATH):
        self.data_path = data_path
        self.config_path = config_path

        try:
            self.config = read_yaml(self.config_path)
        except Exception as e:
            logger.warning(
                f"Could not load config from {self.config_path}: {e}. Using defaults."
            )
            self.config = {}

        self.experiment = self._init_comet()

    def _init_comet(self) -> Optional[Any]:
        """
        Initializes Comet ML experiment safely using environment variables
        or config, gracefully falling back to local mode if unavailable.
        """
        api_key = os.getenv("COMET_API_KEY", "")
        project_name = os.getenv("COMET_PROJECT_NAME", "hybrid-anime-recommender")
        workspace = os.getenv("COMET_WORKSPACE", None)

        if not api_key:
            logger.info(
                "COMET_API_KEY environment variable not set. Running model training in local mode."
            )
            return None

        try:
            import comet_ml

            exp = comet_ml.Experiment(
                api_key=api_key,
                project_name=project_name,
                workspace=workspace,
                auto_metric_logging=True,
                auto_param_logging=True,
            )
            logger.info("Comet ML experiment initialized successfully.")
            return exp
        except Exception as e:
            logger.warning(
                f"Could not initialize Comet ML experiment: {e}. Falling back to local mode."
            )
            return None

    def load_data(
        self,
    ) -> Tuple[List[np.ndarray], List[np.ndarray], np.ndarray, np.ndarray]:
        """
        Loads preprocessed feature arrays and target rating arrays from disk.

        Returns:
            Tuple: (X_train_array, X_test_array, y_train, y_test)
        """
        try:
            logger.info("Loading training and testing datasets from disk...")
            X_train_array = joblib.load(X_TRAIN_ARRAY)
            X_test_array = joblib.load(X_TEST_ARRAY)
            y_train = joblib.load(Y_TRAIN)
            y_test = joblib.load(Y_TEST)

            # Ensure inputs are lists of 1D arrays [users, animes]
            if isinstance(X_train_array, list) and len(X_train_array) == 2:
                X_train_array = [
                    np.asarray(X_train_array[0], dtype=np.int32),
                    np.asarray(X_train_array[1], dtype=np.int32),
                ]
            elif isinstance(X_train_array, np.ndarray) and X_train_array.ndim == 2:
                X_train_array = [
                    X_train_array[:, 0].astype(np.int32),
                    X_train_array[:, 1].astype(np.int32),
                ]

            if isinstance(X_test_array, list) and len(X_test_array) == 2:
                X_test_array = [
                    np.asarray(X_test_array[0], dtype=np.int32),
                    np.asarray(X_test_array[1], dtype=np.int32),
                ]
            elif isinstance(X_test_array, np.ndarray) and X_test_array.ndim == 2:
                X_test_array = [
                    X_test_array[:, 0].astype(np.int32),
                    X_test_array[:, 1].astype(np.int32),
                ]

            y_train = np.asarray(y_train, dtype=np.float32)
            y_test = np.asarray(y_test, dtype=np.float32)

            logger.info(
                f"Data loaded successfully. Train samples: {len(y_train):,}, Test samples: {len(y_test):,}"
            )
            return X_train_array, X_test_array, y_train, y_test

        except Exception as e:
            logger.error(f"Failed to load dataset artifacts from {self.data_path}: {e}")
            raise CustomException("Failed to load preprocessed data", e)

    def train_model(self) -> tf.keras.callbacks.History:
        """
        Instantiates BaseModel, trains the neural network with regularized callbacks,
        restores best checkpoint, logs metrics, and exports normalized weights.

        Returns:
            tf.keras.callbacks.History: Training history object.
        """
        try:
            X_train_array, X_test_array, y_train, y_test = self.load_data()

            user2user = joblib.load(USER2USER_ENCODED)
            anime2anime = joblib.load(ANIME2ANIME_ENCODED)

            max_user_idx = max(
                int(np.max(X_train_array[0])), int(np.max(X_test_array[0]))
            )
            max_anime_idx = max(
                int(np.max(X_train_array[1])), int(np.max(X_test_array[1]))
            )

            n_users = max(len(user2user), max_user_idx + 1)
            n_anime = max(len(anime2anime), max_anime_idx + 1)

            logger.info(
                f"Resolved vocabulary dimensions: n_users={n_users:,}, n_anime={n_anime:,}"
            )

            base_model = BaseModel(config_path=self.config_path)
            model = base_model.RecommenderNet(n_users=n_users, n_anime=n_anime)

            model_cfg = self.config.get("model", {})
            epochs: int = int(model_cfg.get("epochs", 15))
            batch_size: int = int(model_cfg.get("batch_size", 4096))
            patience: int = int(model_cfg.get("early_stopping_patience", 3))

            # Directory preparation
            os.makedirs(os.path.dirname(CHECKPOINT_FILE_PATH), exist_ok=True)
            os.makedirs(MODEL_DIR, exist_ok=True)
            os.makedirs(WEIGHTS_DIR, exist_ok=True)
            os.makedirs("logs/fit", exist_ok=True)

            callbacks = [
                ModelCheckpoint(
                    filepath=CHECKPOINT_FILE_PATH,
                    save_weights_only=True,
                    monitor="val_loss",
                    mode="min",
                    save_best_only=True,
                    verbose=1,
                ),
                EarlyStopping(
                    monitor="val_loss",
                    patience=patience,
                    mode="min",
                    restore_best_weights=True,
                    verbose=1,
                ),
                ReduceLROnPlateau(
                    monitor="val_loss",
                    factor=0.5,
                    patience=max(1, patience - 1),
                    min_lr=1e-5,
                    mode="min",
                    verbose=1,
                ),
            ]

            # Optional TensorBoard logging if installed
            try:
                import tensorboard

                callbacks.append(TensorBoard(log_dir="logs/fit", histogram_freq=0))
            except ImportError:
                pass

            logger.info(
                f"Starting model fit with {len(y_train):,} training samples, batch_size={batch_size}, epochs={epochs}..."
            )

            history = model.fit(
                x=X_train_array,
                y=y_train,
                batch_size=batch_size,
                epochs=epochs,
                verbose=1,
                validation_data=(X_test_array, y_test),
                callbacks=callbacks,
            )

            # Check if checkpoint exists and restore if needed
            if os.path.exists(CHECKPOINT_FILE_PATH):
                try:
                    model.load_weights(CHECKPOINT_FILE_PATH)
                    logger.info(
                        f"Restored best weights checkpoint from {CHECKPOINT_FILE_PATH}"
                    )
                except Exception as e:
                    logger.warning(f"Could not load checkpoint weights: {e}")

            logger.info("Model training loop completed successfully.")

            # Log to Comet ML if active
            if self.experiment and hasattr(history, "history"):
                try:
                    for epoch, (loss, val_loss) in enumerate(
                        zip(
                            history.history.get("loss", []),
                            history.history.get("val_loss", []),
                        )
                    ):
                        self.experiment.log_metric("train_loss", loss, step=epoch)
                        self.experiment.log_metric("val_loss", val_loss, step=epoch)
                except Exception as e:
                    logger.warning(f"Error logging metrics to Comet ML: {e}")

            # Save model and unit-normalized weights
            self.save_model_weights(model, history)
            return history

        except Exception as e:
            logger.error(f"Error occurred during Model Training: {e}")
            raise CustomException("Model training process failed", e)

    def extract_weights(
        self, layer_name: str, model: tf.keras.models.Model
    ) -> np.ndarray:
        """
        Extracts embedding weights and normalizes each row to unit L2 norm
        for fast, accurate cosine similarity dot products in prediction_pipeline.

        Args:
            layer_name (str): Name of the embedding layer in the model.
            model (tf.keras.models.Model): Trained Keras model.

        Returns:
            np.ndarray: Unit L2-normalized 2D numpy array of weights.
        """
        try:
            weight_layer = model.get_layer(layer_name)
            weights = weight_layer.get_weights()[0].astype(np.float32)

            # Compute L2 norms per entity row with numerical stability
            norms = np.linalg.norm(weights, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-10)
            normalized_weights = weights / norms

            logger.info(
                f"Extracted and normalized weights for '{layer_name}': shape={normalized_weights.shape}"
            )
            return normalized_weights

        except Exception as e:
            logger.error(f"Error extracting weights from layer '{layer_name}': {e}")
            raise CustomException(f"Failed to extract weights for {layer_name}", e)

    def save_model_weights(
        self,
        model: tf.keras.models.Model,
        history: Optional[tf.keras.callbacks.History] = None,
    ) -> None:
        """
        Persists the trained model, unit-normalized user & anime embeddings,
        and training history to disk.
        """
        try:
            # 1. Save full model
            model.save(MODEL_PATH)
            logger.info(f"Model saved successfully to {MODEL_PATH}")

            # 2. Extract and save normalized embeddings
            user_weights = self.extract_weights("user_embedding", model)
            anime_weights = self.extract_weights("anime_embedding", model)

            joblib.dump(user_weights, USER_WEIGHTS_PATH)
            joblib.dump(anime_weights, ANIME_WEIGHTS_PATH)
            logger.info(
                f"Saved user weights ({user_weights.shape}) to {USER_WEIGHTS_PATH} and "
                f"anime weights ({anime_weights.shape}) to {ANIME_WEIGHTS_PATH}"
            )

            # 3. Save training history summary
            if history and hasattr(history, "history"):
                history_path = os.path.join(MODEL_DIR, "training_history.json")
                serializable_history = {
                    k: [float(v) for v in vals] for k, vals in history.history.items()
                }
                with open(history_path, "w") as f:
                    json.dump(serializable_history, f, indent=2)
                logger.info(f"Training history saved to {history_path}")

            # 4. Log assets to Comet ML if connected
            if self.experiment:
                try:
                    self.experiment.log_asset(MODEL_PATH)
                    self.experiment.log_asset(USER_WEIGHTS_PATH)
                    self.experiment.log_asset(ANIME_WEIGHTS_PATH)
                except Exception as e:
                    logger.warning(f"Could not log assets to Comet ML: {e}")

            logger.info("All model artifacts and weights successfully persisted.")

        except Exception as e:
            logger.error(f"Error saving model and weights: {e}")
            raise CustomException("Failed to persist model and weights", e)


if __name__ == "__main__":
    trainer = ModelTraining(PROCESSED_DIR, CONFIG_PATH)
    trainer.train_model()
