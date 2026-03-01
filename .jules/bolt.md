## 2025-03-01 - [Deferred Imports for CLI Startup]
**Learning:** Initializing heavy libraries like `astral`, `pytz`, and `requests` at the top level of a CLI entry point significantly penalizes startup time, especially for commands that should be near-instant like `--help` or when user input is invalid.
**Action:** Defer imports to inside the `main()` function or specific execution paths to avoid unnecessary overhead in common CLI interactions.

## 2025-03-01 - [Polar Day/Night Detection in Astral 3.2]
**Learning:** `astral.sun.sun()` raises `ValueError` in certain polar conditions where specific events don't occur. Detecting polar conditions reliably requires checking sun elevation at solar noon when `sunrise`/`sunset` fail.
**Action:** Use `elevation(city.observer, noon_utc)` to distinguish between polar day and polar night after a `ValueError` in `sunrise`/`sunset`.
