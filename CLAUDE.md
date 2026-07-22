# Screenshot Cropper — Project Rules

Condensed from `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\COMMON_RULES.md` and
`PYTHON_RULES.md`. Consult those files for the full text.

## Project Overview

CLI tool that crops/composites screenshots based on JSON configuration.
Entry point: `main.py`. Package code in `src/`. Run with `uv run python main.py --directory <dir>`.

## Tooling (uv)

- `pyproject.toml` is the single source of truth for dependencies and tool config. `uv.lock` is committed.
- Add dependencies with `uv add <pkg>` (dev: `uv add --dev <pkg>`) — never edit requirements files or pip install directly.
- Confirm new dependency versions with the user before adding.
- Setup: `install.bat` (uv sync + tests). Update deps: `update.bat`. Local dev of adobe-document-handler: `install_local.bat`.
- Lint/type-check: `uv run ruff check src/ tests/`, `uv run mypy src/`.

## Required Batch Files

- `start.bat` — starts the app (`uv run python main.py %*`)
- `tools/run_tests.bat` — unit tests (`tests/unit`)
- `tools/run_integration_tests.bat` — integration tests (`tests/integration`)

## Testing

- pytest; unit tests in `tests/unit`, integration tests in `tests/integration`. Both mandatory.
- TDD for features and bug fixes: write the failing test first, then implement.
- No network in unit tests; use tmp dirs/fixtures, no reliance on machine state.
- Mocks always use `spec=RealClass` to catch interface mismatches.

## Code Rules

- Type hints on all public functions/classes (params + return). Avoid `Any` except at I/O boundaries.
- Max 300 lines per file — split by domain when exceeded (exceptions: generated/config/test files).
- No god classes: one responsibility per class; inject collaborators via constructor, never `new` a service inside a method.
- Bundle related values into dataclasses/DTOs instead of many parameters; public APIs return typed objects, never raw dicts crossing module boundaries.
- Centralize string constants (`src/constants.py`) — no scattered raw strings.
- Comments explain *why*, not *what*. KISS/YAGNI/DRY.
- No hardcoded environment values (paths, hosts, ports) — use config with env overrides.
- Validate input at boundaries (CLI args, JSON config files); fail fast with clear errors.
- Naming: files/functions/variables `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Logging

- All logging goes through the central logger (`src/logger.py`) — never `print()` in `src/`.
- Levels decided centrally; callers just pass debug/info/warning/error.
- (Rule target is an `AppLogger` class in `app_logger.py`; current code uses `setup_logger()` in `src/logger.py` — keep routing through it until refactored.)

## Security

- Never commit secrets. Keep dependencies updated (`update.bat`).
