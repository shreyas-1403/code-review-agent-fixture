# code-review-agent-fixture

A tiny task-manager CLI used as a **controlled test bed for AI code reviewers**.
It pairs a written standard ([`conventions.md`](conventions.md), 9 numbered rules) with
code whose compliance is *known*, so a reviewer's output can be graded against facts.

| Branch | Purpose | Convention violations |
|---|---|---|
| `main` | Compliant baseline | **0** |
| `feature/search-tasks` | Demo PR: adds `search_tasks` and `delete_task` | **22 findings across 8 of the 9 rules** (all but rule 6) |

## Ground truth

`tools/check_conventions.py` is a deterministic (AST-based) checker for the nine rules:

```bash
python -m tools.check_conventions --root .
```

Rules 1-2 and 4-9 are exact; rule 3 ("new public functions need a test") is approximated
by checking that each public function is referenced as code under `tests/`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Includes a test that fails if `main` ever stops being fully compliant, and tests proving
the checker flags the demo PR's code (and accepts a compliant rewrite of the same feature).

## Usage

```bash
python -m task_manager.cli add "Write tests"
python -m task_manager.cli list
python -m task_manager.cli done 1
```

Reviewed by the code-review-agent project (a convention-aware GitHub PR reviewer).
