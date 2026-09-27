"""Loads the project's .env (ANTHROPIC_API_KEY, ANTHROPIC_WORKSPACE_ID, LAIKA_MODEL)."""
import os
from pathlib import Path


def load_dotenv(path: Path = Path(__file__).resolve().parent.parent / ".env"):
    """Minimal .env reader (KEY=value lines). Variables already set in the shell win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ.setdefault(key.strip(), value)
