# Team Conventions

These are the rules we enforce on every PR. Reviewers (human or automated) should
flag violations of these specific rules — not generic style opinions.

1. **Error handling is required around I/O and parsing.** Any code that reads/writes
   files, parses JSON, or does network calls must handle the failure case explicitly
   (try/except with a meaningful action — log, re-raise with context, or return a
   default). Never let these exceptions propagate uncaught.

2. **Names must be descriptive.** No single-letter variable names (except loop
   counters `i`/`j` in tight loops) and no vague names like `data`, `tmp`, `val`,
   `d`, `t`. A reader should understand what a variable holds from its name alone.

3. **Every new public function needs a test.** If a PR adds a new function to
   `task_manager/`, the same PR must add or update a test in `tests/` that covers it.

4. **Use `logging`, never `print()`.** All diagnostic/status output in library code
   (anything under `task_manager/`) must go through the `logging` module, not
   `print()`. CLI-facing user output in `cli.py` is the only exception.

5. **Add type hints to all new function signatures.** Parameters and return types.

6. **Keep functions focused.** A function should do one thing; if it's growing past
   ~40 lines or mixing multiple responsibilities, extract a helper.

7. **Public functions need a docstring.** Every function in `task_manager/` that
   isn't prefixed with `_` must have a one-line docstring describing what it does.

8. **No bare or broad `except`.** Never write `except:` or `except Exception:` to
   silently swallow errors. Catch the specific exception type you expect and either
   log it with context or re-raise.

9. **No mutable default arguments.** Never use `[]`, `{}`, or other mutable objects
   as a default parameter value (e.g. `def f(items=[])`). Use `None` and initialize
   inside the function body instead.
