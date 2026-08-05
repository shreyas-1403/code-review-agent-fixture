from pathlib import Path

from task_manager.tasks import add_task, complete_task, list_tasks


def test_add_task_creates_entry(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    task = add_task("Write tests", tasks_file)
    assert task["title"] == "Write tests"
    assert task["done"] is False
    assert list_tasks(tasks_file) == [task]


def test_complete_task_marks_done(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    task = add_task("Ship feature", tasks_file)
    assert complete_task(task["id"], tasks_file) is True
    assert list_tasks(tasks_file)[0]["done"] is True


def test_complete_task_returns_false_when_missing(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    assert complete_task(999, tasks_file) is False
