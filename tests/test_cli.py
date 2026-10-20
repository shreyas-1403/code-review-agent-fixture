from pathlib import Path

import pytest

from task_manager.cli import main


@pytest.fixture(autouse=True)
def _isolated_tasks_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI uses ./tasks.json, so run every test in its own empty directory."""
    monkeypatch.chdir(tmp_path)


def test_add_then_list_shows_the_task(capsys: pytest.CaptureFixture[str]) -> None:
    main(["add", "Write tests"])
    main(["list"])
    output = capsys.readouterr().out
    assert "Added task #1: Write tests" in output
    assert "[ ] #1 Write tests" in output


def test_done_marks_task_complete(capsys: pytest.CaptureFixture[str]) -> None:
    main(["add", "Ship feature"])
    main(["done", "1"])
    main(["list"])
    output = capsys.readouterr().out
    assert "Task #1 marked done" in output
    assert "[x] #1 Ship feature" in output


def test_done_reports_unknown_task(capsys: pytest.CaptureFixture[str]) -> None:
    main(["done", "42"])
    assert "Task #42 not found" in capsys.readouterr().out


def test_missing_command_exits_with_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2
