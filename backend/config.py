"""Settings read from the environment."""
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "tasks.db")
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).parent / "static"))
