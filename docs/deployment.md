# Deployment

The dashboard is deployed as a Dash WSGI app. `app.py` exposes `server = dash_app.server`, which allows Gunicorn to serve the app in hosted environments.

## Render

`render.yaml` defines a Python web service named `student-performance-intelligence`.

Build command:

```text
python -m pip install --upgrade pip && pip install -r requirements.txt
```

Start command:

```text
gunicorn app:server --workers 1 --threads 2 --timeout 180 --graceful-timeout 180
```

## Health Check

The app exposes:

```text
/healthz
```

Expected response:

```text
ok
```

## Runtime Configuration

The app reads processed data from `DAVI_PROCESSED_DATA_DIR`, defaulting to `data/processed`.
