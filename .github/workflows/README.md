# Workflows

This folder contains GitHub Actions workflows.

`ci.yml` runs:

- Python dependency installation.
- Pytest.
- Ruff syntax and undefined-name checks.
- Bandit static security analysis.
- `pip-audit` dependency vulnerability checks.
