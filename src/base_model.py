from typing import Union, List, Optional
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input,
    Embedding,
    Dot,
    Flatten,
    Dense,
    Dropout,
    BatchNormalization,
    Concatenate,
)
from utils.common_functions import read_yaml
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)


class BaseModel:
    """
    Constructs and compiles deep hybrid recommendation architectures with
    embedding regularization, bias terms, and non-linear feature interactions.
    """

    def __init__(self, config_path: str):
        try:
            self.config = read_yaml(config_path)
            logger.info(f"Loaded configuration successfully from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise CustomException("Error loading configuration", e)

    def RecommenderNet(self, n_users: int, n_anime: int) -> Model:
        """
        Builds a neural matrix factorization collaborative filtering architecture.
        Preserves 'user_embedding' and 'anime_embedding' layer names for downstream
        cosine distance extraction in utils/helpers.py.

        Args:
            n_users (int): Total number of unique users in encoding vocabulary.
            n_anime (int): Total number of unique anime in encoding vocabulary.

        Returns:
            tf.keras.models.Model: Compiled Keras recommendation model.
        """
        try:
            model_cfg = self.config.get("model", {})
            embedding_size: int = int(model_cfg.get("embedding_size", 128))
            dropout_rate: float = float(model_cfg.get("dropout_rate", 0.2))
            l2_reg: float = float(model_cfg.get("l2_reg", 1e-6))
            learning_rate: float = float(model_cfg.get("learning_rate", 0.001))
            loss: str = model_cfg.get("loss", "binary_crossentropy")
            optimizer_name: str = model_cfg.get("optimizer", "Adam")
            metrics: List[str] = model_cfg.get("metrics", ["mae", "mse"])

            logger.info(
                f"Initializing RecommenderNet: n_users={n_users}, n_anime={n_anime}, "
                f"embedding_size={embedding_size}, dropout={dropout_rate}, l2={l2_reg}, lr={learning_rate}"
            )

            regularizer = tf.keras.regularizers.l2(l2_reg) if l2_reg > 0 else None

            # Input layers
            user = Input(name="user", shape=[1], dtype="int32")
            anime = Input(name="anime", shape=[1], dtype="int32")

            # Latent feature embeddings (Retained layer names for extract_weights)
            user_embedding = Embedding(
                input_dim=n_users,
                output_dim=embedding_size,
                name="user_embedding",
                embeddings_initializer="he_normal",
                embeddings_regularizer=regularizer,
            )(user)

            anime_embedding = Embedding(
                input_dim=n_anime,
                output_dim=embedding_size,
                name="anime_embedding",
                embeddings_initializer="he_normal",
                embeddings_regularizer=regularizer,
            )(anime)

            # Bias terms for individual user baseline and item popularity
            user_bias = Embedding(
                input_dim=n_users,
                output_dim=1,
                name="user_bias",
                embeddings_initializer="zeros",
            )(user)

            anime_bias = Embedding(
                input_dim=n_anime,
                output_dim=1,
                name="anime_bias",
                embeddings_initializer="zeros",
            )(anime)

            # Flatten embeddings and biases
            u_vec = Flatten(name="flatten_user_embedding")(user_embedding)
            a_vec = Flatten(name="flatten_anime_embedding")(anime_embedding)
            u_bias = Flatten(name="flatten_user_bias")(user_bias)
            a_bias = Flatten(name="flatten_anime_bias")(anime_bias)

            # Dot-product latent interaction (Generalized Matrix Factorization branch)
            dot_product = Dot(axes=1, name="dot_product")([u_vec, a_vec])

            # Deep Multi-Layer Perceptron (MLP) branch with Dropout & BatchNorm
            interaction = Concatenate(name="concat_embeddings")(
                [u_vec, a_vec, dot_product]
            )
            dense_1 = Dense(
                64, activation="relu", kernel_initializer="he_normal", name="dense_64"
            )(interaction)
            bn_1 = BatchNormalization(name="bn_1")(dense_1)
            drop_1 = Dropout(dropout_rate, name="dropout_1")(bn_1)

            dense_2 = Dense(
                32, activation="relu", kernel_initializer="he_normal", name="dense_32"
            )(drop_1)
            drop_2 = Dropout(dropout_rate, name="dropout_2")(dense_2)

            # Combine deep features, matrix factorization dot-product, and baseline biases
            combined = Concatenate(name="concat_all")(
                [drop_2, dot_product, u_bias, a_bias]
            )
            prediction = Dense(1, activation="sigmoid", name="prediction")(combined)

            model = Model(
                inputs=[user, anime], outputs=prediction, name="AnimeRecommenderNet"
            )

            # Optimizer configuration
            if isinstance(optimizer_name, str):
                opt_lower = optimizer_name.lower()
                if opt_lower == "adam":
                    opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
                elif opt_lower == "adamw":
                    opt = tf.keras.optimizers.AdamW(learning_rate=learning_rate)
                elif opt_lower == "rmsprop":
                    opt = tf.keras.optimizers.RMSprop(learning_rate=learning_rate)
                elif opt_lower == "sgd":
                    opt = tf.keras.optimizers.SGD(learning_rate=learning_rate)
                else:
                    opt = optimizer_name
            else:
                opt = optimizer_name

            model.compile(loss=loss, optimizer=opt, metrics=metrics)
            logger.info(
                f"Model created successfully with {model.count_params():,} total parameters."
            )
            return model

        except Exception as e:
            logger.error(f"Error occurred during model architecture construction: {e}")
            raise CustomException("Failed to create recommender model", e)
