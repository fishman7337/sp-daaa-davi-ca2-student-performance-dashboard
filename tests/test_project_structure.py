from __future__ import annotations

import json
from pathlib import Path

from conftest import PROJECT_ROOT


EXPECTED_FILES = [
    ".env.example",
    ".github/README.md",
    ".github/workflows/README.md",
    ".github/workflows/ci.yml",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "app.py",
    "data/README.md",
    "data/processed/README.md",
    "data/raw/README.md",
    "docs/README.md",
    "docs/academic-context.md",
    "docs/data-dictionary.md",
    "docs/declarations/README.md",
    "docs/deployment.md",
    "notebooks/README.md",
    "notebooks/student-performance-intelligence.ipynb",
    "pyproject.toml",
    "render.yaml",
    "reports/README.md",
    "reports/student-performance-intelligence-presentation.pptx",
    "requirements-dev.txt",
    "requirements.txt",
    "tests/README.md",
]

EXPECTED_FOLDERS_WITH_READMES = [
    ".github",
    ".github/workflows",
    "data",
    "data/processed",
    "data/raw",
    "docs",
    "docs/declarations",
    "notebooks",
    "reports",
    "tests",
]


def test_expected_project_files_exist() -> None:
    missing = [path for path in EXPECTED_FILES if not (PROJECT_ROOT / path).exists()]
    assert missing == []


def test_documented_folders_have_readmes() -> None:
    missing = [folder for folder in EXPECTED_FOLDERS_WITH_READMES if not (PROJECT_ROOT / folder / "README.md").exists()]
    assert missing == []


def test_notebook_is_valid_json() -> None:
    notebook_path = PROJECT_ROOT / "notebooks" / "student-performance-intelligence.ipynb"
    with notebook_path.open(encoding="utf-8") as handle:
        notebook = json.load(handle)

    assert notebook["nbformat"] >= 4
    assert any(cell.get("cell_type") == "code" for cell in notebook["cells"])
