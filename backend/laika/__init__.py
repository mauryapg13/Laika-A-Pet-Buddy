"""Laika: the dog's wall hub (hub), its camera (camera), the diary (diary) and the HTTP API (api)."""
from pathlib import Path

# backend/laika/__init__.py -> the repository root, where models/, data/, .env and out/ live.
REPO_ROOT = Path(__file__).resolve().parents[2]
