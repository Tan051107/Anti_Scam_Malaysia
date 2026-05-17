# -*- coding: utf-8 -*-
"""Bedrock model IDs loaded from environment at call time."""

import os

# Env var names (values live in backend/.env)
ANALYSIS_MODEL_ENV = "BEDROCK_MODEL_ID"
SIMULATOR_MODEL_ENV = "SIMULATOR_MODEL_ID"
COMMUNITY_MODEL_ENV = "COMMUNITY_MODEL_ID"


def get_model_id(env_key: str) -> str:
    """Return a Bedrock model ID from the environment (read on each call)."""
    value = os.getenv(env_key, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {env_key}")
    return value
