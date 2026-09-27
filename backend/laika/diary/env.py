"""Loads the project's .env (ANTHROPIC_API_KEY, ANTHROPIC_WORKSPACE_ID, LAIKA_MODEL)."""
import os
from pathlib import Path


def load_dotenv(path: Path | None = None):
    """Minimal .env reader (KEY=value lines): ./.env, else the repo root's. Variables already set in the shell win."""
    from laika import REPO_ROOT
    path = path or next((p for p in (Path.cwd() / ".env", REPO_ROOT / ".env") if p.exists()), REPO_ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ.setdefault(key.strip(), value)
