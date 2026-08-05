from pathlib import Path

from task_manager.storage import load_tasks, save_tasks


def test_load_tasks_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_tasks(tmp_path / "nope.json") == []


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    save_tasks(tasks_file, [{"id": 1, "title": "x", "done": False}])
    assert load_tasks(tasks_file) == [{"id": 1, "title": "x", "done": False}]


def test_load_tasks_corrupted_file_returns_empty(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text("{not valid json", encoding="utf-8")
    assert load_tasks(tasks_file) == []
