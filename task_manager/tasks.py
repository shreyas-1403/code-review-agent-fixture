"""Core task manager logic."""
import logging
from pathlib import Path
from typing import Any

from task_manager.storage import load_tasks, save_tasks

logger = logging.getLogger(__name__)

DEFAULT_TASKS_FILE = Path("tasks.json")


def add_task(title: str, tasks_file: Path = DEFAULT_TASKS_FILE) -> dict[str, Any]:
    """Add a new task with the given title and return the created task record."""
    tasks = load_tasks(tasks_file)
    new_task = {"id": len(tasks) + 1, "title": title, "done": False}
    tasks.append(new_task)
    save_tasks(tasks_file, tasks)
    logger.info("Added task %s: %s", new_task["id"], title)
    return new_task


def complete_task(task_id: int, tasks_file: Path = DEFAULT_TASKS_FILE) -> bool:
    """Mark a task as done. Returns True if the task was found and updated."""
    tasks = load_tasks(tasks_file)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks_file, tasks)
            logger.info("Completed task %s", task_id)
            return True
    logger.warning("Task %s not found", task_id)
    return False


def list_tasks(tasks_file: Path = DEFAULT_TASKS_FILE) -> list[dict[str, Any]]:
    """Return all tasks."""
    return load_tasks(tasks_file)
