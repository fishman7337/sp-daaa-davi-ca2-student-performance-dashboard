# Student Performance Intelligence

Dash analytics dashboard and notebook workflow for the ST1502 Data Visualisation CA2 project.

## Academic Context

This project was completed under Singapore Polytechnic, School of Computing, Diploma in Applied AI & Analytics. It was produced for the Data Visualisation module (`ST1502`) CA2 in AY25/26 Year 2 Semester 2 by Goh Kun Ming and Goh Jenson, DAAA students. The lecturer for the module was Senior Lecturer Peter Lee Wai Tong.

## Project Overview

Student Performance Intelligence analyses student profile, result, survey, and course-code datasets to support course-level and cohort-level insight. The repository contains:

- A deployment-ready Dash dashboard in `app.py`.
- The original analysis and cleaning notebook in `notebooks/`.
- Raw and processed Excel datasets in `data/`.
- Presentation and declaration artifacts in `reports/` and `docs/declarations/`.
- Automated test and CI configuration for quality, security, and reproducibility checks.

## Repository Layout

```text
.
|-- app.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- docs/
|   `-- declarations/
|-- notebooks/
|-- reports/
|-- tests/
|-- .github/
|   `-- workflows/
|-- requirements.txt
|-- requirements-dev.txt
|-- render.yaml
`-- pyproject.toml
```

Every maintained folder includes its own `README.md` explaining what belongs there.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8050` after the server starts.

## Environment Variables

Copy `.env.example` to `.env` for local development if you want to override defaults.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8050` | Local server port. |
| `HOST` | `127.0.0.1` | Local bind address used by `python app.py`. |
| `DASH_DEBUG` | `false` | Enables Dash debug mode when set to `true`. |
| `DAVI_PROCESSED_DATA_DIR` | `data/processed` | Location of cleaned Excel workbooks used by the app. |

## Development Checks

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the core checks:

```powershell
python -m pytest
python -m ruff check . --select E9,F63,F7,F82
python -m bandit -r app.py -ll
python -m pip_audit -r requirements.txt
```

The GitHub Actions workflow runs these checks automatically on pushes and pull requests.

## Deployment

`render.yaml` is configured for Render using:

```text
gunicorn app:server --workers 1 --threads 2 --timeout 180 --graceful-timeout 180
```

The Render service name is `student-performance-intelligence`, and the app reads processed data from `data/processed` unless `DAVI_PROCESSED_DATA_DIR` is overridden.

## Data Notice

The included datasets are assignment artifacts and may contain student-related records. Keep the repository access-controlled where required, avoid committing additional personal data, and remove local exports that are not needed for reproducibility.

## License

This repository is released under the MIT License. See `LICENSE` for details.
