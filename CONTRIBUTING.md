# Contributing to localShare

Thank you for considering a contribution.

## Development Setup

1. Install [uv](https://docs.astral.sh/uv/) and Python 3.14.
2. Clone the repository.
3. Sync dependencies:
   ```
   uv sync --group dev
   ```
4. Run tests:
   ```
   uv run pytest -q
   ```
5. Lint:
   ```
   uv run ruff check .
   ```

## Guidelines

- Keep changes focused and minimal.
- Follow the existing code style (ruff-enforced).
- Add or update tests for behavioral changes.
- Use English for code, comments, and commit messages.
- Use Conventional Commits (e.g. `feat:`, `fix:`, `chore:`).

## Pull Requests

- Open a PR against `main`.
- Describe the change, motivation, and testing performed.
- Ensure CI is green before requesting review.

## Reporting Issues

Use the issue templates. Include reproduction steps, expected vs. actual
behavior, and environment details (OS, Python version, app version).
