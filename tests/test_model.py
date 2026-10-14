import pytest
import numpy as np
import tensorflow as tf
from src.base_model import BaseModel
from config.paths_config import CONFIG_PATH


def test_base_model_initialization():
    base_model = BaseModel(config_path=CONFIG_PATH)
    assert base_model.config is not None
    assert "model" in base_model.config


def test_recommender_net_architecture():
    base_model = BaseModel(config_path=CONFIG_PATH)
    n_users = 100
    n_anime = 200

    model = base_model.RecommenderNet(n_users=n_users, n_anime=n_anime)
    assert isinstance(model, tf.keras.models.Model)

    # Verify critical embedding layers required for similarity extraction
    user_layer = model.get_layer("user_embedding")
    anime_layer = model.get_layer("anime_embedding")
    assert user_layer is not None
    assert anime_layer is not None
    assert user_layer.input_dim == n_users
    assert anime_layer.input_dim == n_anime

    # Test forward pass with dummy batch
    dummy_users = np.array([[1], [5], [10]], dtype=np.int32)
    dummy_animes = np.array([[2], [8], [25]], dtype=np.int32)
    preds = model.predict([dummy_users, dummy_animes], verbose=0)

    assert preds.shape == (3, 1)
    assert np.all(preds >= 0.0) and np.all(preds <= 1.0)
