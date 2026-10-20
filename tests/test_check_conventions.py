"""Tests for tools/check_conventions.py, plus a test that the fixture itself is compliant."""
from pathlib import Path

import pytest

from tools.check_conventions import check_project, check_source, check_tests_exist

ROOT = Path(__file__).resolve().parent.parent

# The deliberately bad code from the demo PR (branch feature/search-tasks).
VIOLATING_SOURCE = '''
import json

def search_tasks(query, tasks_file=DEFAULT_TASKS_FILE):
    f = open(tasks_file, "r")
    d = json.load(f)
    results = []
    for t in d:
        if query.lower() in t["title"].lower():
            results.append(t)
    print(f"found {len(results)} matching tasks")
    return results


def delete_task(task_id, tasks_file=DEFAULT_TASKS_FILE, cache=[]):
    try:
        d = json.load(open(tasks_file))
        n = []
        for x in d:
            if x["id"] != task_id:
                n.append(x)
            else:
                cache.append(x)
        json.dump(n, open(tasks_file, "w"))
        print("deleted")
    except:
        pass
'''

# What a convention-compliant version of the same feature looks like.
COMPLIANT_SOURCE = '''
import logging

logger = logging.getLogger(__name__)


def search_tasks(query: str, tasks_file: Path = DEFAULT_TASKS_FILE) -> list[dict[str, Any]]:
    """Return tasks whose title contains the query (case-insensitive)."""
    needle = query.lower()
    matches = [task for task in load_tasks(tasks_file) if needle in task["title"].lower()]
    logger.info("Found %d tasks matching %r", len(matches), query)
    return matches


def delete_task(task_id: int, tasks_file: Path = DEFAULT_TASKS_FILE) -> bool:
    """Delete a task by id. Returns True if a task was removed."""
    tasks = load_tasks(tasks_file)
    remaining = [task for task in tasks if task["id"] != task_id]
    if len(remaining) == len(tasks):
        logger.warning("Task %s not found", task_id)
        return False
    save_tasks(tasks_file, remaining)
    logger.info("Deleted task %s", task_id)
    return True
'''


def _rules(source: str, filename: str = "task_manager/example.py") -> set[int]:
    return {violation.rule for violation in check_source(source, filename)}


def test_violating_pr_code_breaks_exactly_the_documented_rules() -> None:
    assert _rules(VIOLATING_SOURCE) == {1, 2, 4, 5, 7, 8, 9}


def test_compliant_version_of_the_same_feature_has_no_violations() -> None:
    assert check_source(COMPLIANT_SOURCE, "task_manager/example.py") == []


@pytest.mark.parametrize(
    ("rule", "source"),
    [
        (1, 'def read_config(path: str) -> str:\n    """Read a file."""\n    return open(path).read()\n'),
        (2, 'def total(items: list[int]) -> int:\n    """Sum."""\n    val = sum(items)\n    return val\n'),
        (4, 'def show(message: str) -> None:\n    """Show."""\n    print(message)\n'),
        (5, 'def add(left, right):\n    """Add."""\n    return left + right\n'),
        (7, "def add(left: int, right: int) -> int:\n    return left + right\n"),
        (8, 'def safe(value: str) -> int:\n    """Parse."""\n    try:\n        return int(value)\n    except Exception:\n        return 0\n'),
        (9, 'def collect(item: int, bucket: list[int] = []) -> list[int]:\n    """Collect."""\n    bucket.append(item)\n    return bucket\n'),
    ],
)
def test_each_rule_is_detected(rule: int, source: str) -> None:
    assert rule in _rules(source)


def test_rule_6_flags_functions_over_40_lines() -> None:
    body = "\n".join(f"    step_{n} = {n}" for n in range(45))
    source = f'def long_function() -> None:\n    """Too long."""\n{body}\n'
    assert 6 in _rules(source)


def test_print_is_allowed_in_cli_only() -> None:
    source = 'def show(message: str) -> None:\n    """Show."""\n    print(message)\n'
    assert 4 not in _rules(source, "task_manager/cli.py")


def test_reraising_a_broad_exception_is_allowed() -> None:
    source = 'def run() -> None:\n    """Run."""\n    try:\n        pass\n    except Exception:\n        raise\n'
    assert 8 not in _rules(source)


def test_rule_3_flags_public_functions_missing_from_tests() -> None:
    source = 'def covered() -> None:\n    """x"""\n\ndef uncovered() -> None:\n    """x"""\n'
    violations = check_tests_exist(source, "task_manager/x.py", "def test_covered(): covered()")
    assert [v.rule for v in violations] == [3]
    assert "uncovered" in violations[0].message


def test_rule_3_ignores_names_that_only_appear_in_string_literals() -> None:
    source = 'def feature() -> None:\n    """x"""\n'
    tests_code = 'SAMPLE = "def feature(): pass"\n\ndef test_other() -> None:\n    assert True\n'
    assert [v.rule for v in check_tests_exist(source, "task_manager/x.py", tests_code)] == [3]


def test_the_fixture_itself_is_fully_compliant() -> None:
    assert check_project(ROOT) == []
