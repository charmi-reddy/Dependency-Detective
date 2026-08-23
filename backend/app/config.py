"""Application configuration, sourced entirely from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

root_env = Path(__file__).resolve().parents[2] / ".env"
backend_env = Path(__file__).resolve().parents[1] / ".env"
for env_path in (root_env, backend_env):
    load_dotenv(env_path)


class Config:
    # "cognodb"   -> connect to CognoDB (requires COGNODB_*)
    # "demo"      -> embedded in-memory dataset (offline development / tests)
    # "auto"      -> use CognoDB when COGNODB_URI is set, otherwise demo
    GRAPH_BACKEND = os.getenv("GRAPH_BACKEND", "auto")

    COGNODB_URI = os.getenv("COGNODB_URI", "")
    COGNODB_USERNAME = os.getenv("COGNODB_USERNAME", "cognodb")
    COGNODB_PASSWORD = os.getenv("COGNODB_PASSWORD", "")

    # Depth guardrail for variable-length traversals. The same bound is baked
    # into the Cypher in services/cypher.py (Cypher range literals cannot be
    # parameterised), so changing it requires editing both.
    IMPACT_MAX_DEPTH = int(os.getenv("IMPACT_MAX_DEPTH", "6"))
