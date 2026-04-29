# Contributing

Thank you for helping improve Student Performance Intelligence. Keep changes focused, reproducible, and respectful of the academic context.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Before Submitting Changes

Run:

```powershell
python -m pytest
python -m ruff check . --select E9,F63,F7,F82
python -m bandit -r app.py -ll
python -m pip_audit -r requirements.txt
```

## Contribution Guidelines

- Keep raw data untouched unless the assignment source data changes.
- Put cleaned or derived datasets in `data/processed/`.
- Put notebooks in `notebooks/` and avoid committing hidden checkpoint folders.
- Keep documentation updated when paths, setup commands, or data contracts change.
- Do not commit `.env`, credentials, tokens, or unrelated personal data.
- Preserve academic attribution and cite external references where applicable.
