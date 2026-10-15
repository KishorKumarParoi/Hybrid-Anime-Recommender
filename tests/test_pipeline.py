import pytest
from pipeline.prediction_pipeline import hybrid_recommendation


def test_hybrid_recommendation_known_user():
    # User 11880 has ample watched anime in rating_df
    results = hybrid_recommendation(11880)
    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 10
    assert isinstance(results[0], str)


def test_hybrid_recommendation_cold_start():
    # Negative user id triggers cold-start fallback
    results = hybrid_recommendation(-999999)
    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 10
