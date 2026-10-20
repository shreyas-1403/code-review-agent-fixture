"""Deterministic checker for the mechanical rules in conventions.md.

Gives the benchmark a ground truth: for any version of task_manager/, it reports which
numbered conventions are violated and where, so an AI reviewer's findings can be scored
against facts instead of opinions.

Rules 3 and 6 are approximations (see the functions below); the rest are exact.

Usage:  python -m tools.check_conventions [--root DIR]
Exit code is 1 if any violation is found.
"""
import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWED_SHORT_NAMES = {"i", "j", "_"}
VAGUE_NAMES = {"data", "tmp", "val", "d", "t"}
BROAD_EXCEPTIONS = {"Exception", "BaseException"}
MAX_FUNCTION_LINES = 40
PRINT_ALLOWED_IN = {"cli.py"}
IO_METHODS = {"read_text", "write_text", "read_bytes", "write_bytes"}
JSON_IO_METHODS = {"load", "loads", "dump"}


@dataclass(frozen=True)
class Violation:
    rule: int
    file: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: rule {self.rule}: {self.message}"


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _is_public(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return not function.name.startswith("_")


def _is_io_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "open"
    if isinstance(func, ast.Attribute):
        is_json = isinstance(func.value, ast.Name) and func.value.id == "json"
        return (is_json and func.attr in JSON_IO_METHODS) or func.attr in IO_METHODS
    return False


def _handler_is_meaningful(handler: ast.ExceptHandler) -> bool:
    """A specific exception type and a body that does something (not just `pass`)."""
    is_specific = handler.type is not None and not (
        isinstance(handler.type, ast.Name) and handler.type.id in BROAD_EXCEPTIONS
    )
    does_something = any(not isinstance(stmt, ast.Pass) for stmt in handler.body)
    return is_specific and does_something


def _is_guarded(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """True if `node` sits in the body of a try with a meaningful handler (same function)."""
    previous, current = node, parents.get(node)
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if isinstance(current, ast.Try) and previous in current.body:
            if any(_handler_is_meaningful(handler) for handler in current.handlers):
                return True
        previous, current = current, parents.get(current)
    return False


def _bad_name(name: str) -> bool:
    if name in ALLOWED_SHORT_NAMES:
        return False
    return len(name) == 1 or name in VAGUE_NAMES


def _missing_annotations(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    args = function.args
    params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    params += [p for p in (args.vararg, args.kwarg) if p is not None]
    missing = [p.arg for p in params if p.annotation is None and p.arg not in ("self", "cls")]
    if function.returns is None:
        missing.append("return")
    return missing


def _has_mutable_default(default: ast.AST) -> bool:
    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
        return True
    return (
        isinstance(default, ast.Call)
        and isinstance(default.func, ast.Name)
        and default.func.id in {"list", "dict", "set"}
    )


def check_source(source: str, filename: str) -> list[Violation]:
    """Check rules 1, 2, 4, 5, 6, 7, 8 and 9 on one module's source text."""
    tree = ast.parse(source)
    parents = _parent_map(tree)
    found: list[Violation] = []

    def add(rule: int, node: ast.AST, message: str) -> None:
        found.append(Violation(rule, filename, getattr(node, "lineno", 0), message))

    for node in ast.walk(tree):
        if _is_io_call(node) and not _is_guarded(node, parents):
            add(1, node, "I/O or JSON parsing without a try/except that handles the failure")
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and _bad_name(node.id):
            add(2, node, f"non-descriptive name '{node.id}'")
        if isinstance(node, ast.arg) and node.arg not in ("self", "cls") and _bad_name(node.arg):
            add(2, node, f"non-descriptive parameter name '{node.arg}'")
        if isinstance(node, ast.ExceptHandler):
            if node.name and _bad_name(node.name):
                add(2, node, f"non-descriptive name '{node.name}'")
            is_broad = node.type is None or (
                isinstance(node.type, ast.Name) and node.type.id in BROAD_EXCEPTIONS
            )
            reraises = any(isinstance(stmt, ast.Raise) for stmt in ast.walk(node))
            if is_broad and not reraises:
                add(8, node, "bare or broad except that does not re-raise")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and Path(filename).name not in PRINT_ALLOWED_IN
        ):
            add(4, node, "print() in library code; use logging")

    for function in _functions(tree):
        missing = _missing_annotations(function)
        if missing:
            add(5, function, f"{function.name}: missing type hints for {', '.join(missing)}")
        length = (function.end_lineno or function.lineno) - function.lineno + 1
        if length > MAX_FUNCTION_LINES:
            add(6, function, f"{function.name} is {length} lines (limit {MAX_FUNCTION_LINES})")
        if _is_public(function) and not ast.get_docstring(function):
            add(7, function, f"public function {function.name} has no docstring")
        defaults = [*function.args.defaults, *[d for d in function.args.kw_defaults if d is not None]]
        if any(_has_mutable_default(default) for default in defaults):
            add(9, function, f"{function.name}: mutable default argument")

    return found


def _referenced_names(code: str) -> set[str]:
    """Names used as code (variables, attributes, imports) - string literals don't count."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add(node.name.split(".")[-1])
    return names


def check_tests_exist(source: str, filename: str, tests_code: str) -> list[Violation]:
    """Rule 3 (approximation): every public function must be referenced as code in tests/.

    A name that only appears inside a string literal (e.g. test data) does not count.
    """
    referenced = _referenced_names(tests_code)
    return [
        Violation(3, filename, function.lineno,
                  f"public function {function.name} is not referenced in tests/")
        for function in _functions(ast.parse(source))
        if _is_public(function) and function.name not in referenced
    ]


def check_project(root: Path) -> list[Violation]:
    """Check every module under <root>/task_manager against all nine rules."""
    tests_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((root / "tests").glob("*.py"))
    )
    found: list[Violation] = []
    for path in sorted((root / "task_manager").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        name = path.relative_to(root).as_posix()
        found += check_source(source, name) + check_tests_exist(source, name, tests_text)
    return sorted(found, key=lambda v: (v.file, v.line, v.rule))


def main(argv: list[str] | None = None) -> int:
    """Print all violations under --root and return a process exit code."""
    parser = argparse.ArgumentParser(description="Check task_manager/ against conventions.md")
    parser.add_argument("--root", type=Path, default=Path("."), help="fixture repo root")
    args = parser.parse_args(argv)

    violations = check_project(args.root)
    for violation in violations:
        print(violation)
    rules = sorted({v.rule for v in violations})
    print(f"{len(violations)} violation(s); rules violated: {rules or 'none'}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
