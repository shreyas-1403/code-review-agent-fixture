"""JSON file storage for tasks."""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_tasks(path: Path) -> list[dict[str, Any]]:
    """Load tasks from a JSON file. Returns an empty list if the file is missing
    or contains invalid JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("No task file found at %s, starting fresh", path)
        return []
    except json.JSONDecodeError:
        logger.error("Task file at %s is corrupted, starting fresh", path)
        return []


def save_tasks(path: Path, tasks: list[dict[str, Any]]) -> None:
    """Write tasks to a JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except OSError as exc:
        logger.error("Failed to save tasks to %s: %s", path, exc)
        raise
