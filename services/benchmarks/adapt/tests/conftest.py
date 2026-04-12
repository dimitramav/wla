"""Shared fixtures for adapt/ tests."""
import pytest


@pytest.fixture
def tiny_bkt_params():
    return {"p_L0": 0.3, "p_T": 0.15, "p_S": 0.08, "p_G": 0.22}


@pytest.fixture
def toy_keywords():
    return [
        "common signs and symptoms",
        "peer aggression",
        "social evaluation fears",
        "somatic complaints",
        "attendance tracking",
    ]


@pytest.fixture
def toy_mastery_vector(toy_keywords):
    return {kw: 0.5 for kw in toy_keywords}
