"""
Vercel ASGI entry (FastAPI only — no project imports).

Streamlit and the data pipeline are not installed on Vercel; run them locally.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parent
DASHBOARD_HTML = ROOT / "output" / "dashboard.html"

app = FastAPI(title="Tourism analytics", version="1.0")

_LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tourism analytics</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto;
           padding: 0 1rem; background: #141915; color: #f5f0e6; line-height: 1.5; }
    a { color: #95d5b2; }
    code, pre { background: #1b4332; padding: 0.2rem 0.45rem; border-radius: 6px; font-size: 0.9em; }
    pre { padding: 1rem; overflow: auto; }
  </style>
</head>
<body>
  <h1>Tourism analytics</h1>
  <p>Vercel serves this FastAPI app. The interactive UI is <strong>Streamlit</strong> — run it locally or on
     <a href="https://streamlit.io/cloud" rel="noopener">Streamlit Community Cloud</a>.</p>
  <p>Local run:</p>
  <pre>pip install -r requirements-pipeline.txt
python main.py
python -m streamlit run streamlit_app.py</pre>
  <p>Static Plotly export: <a href="/dashboard">/dashboard</a> (if <code>output/dashboard.html</code> is deployed).</p>
</body>
</html>"""


@app.get("/")
def index() -> HTMLResponse:
    return HTMLResponse(_LANDING)


@app.get("/dashboard")
def dashboard() -> HTMLResponse:
    try:
        if DASHBOARD_HTML.is_file():
            html = DASHBOARD_HTML.read_text(encoding="utf-8")
            return HTMLResponse(html)
    except OSError:
        pass
    return HTMLResponse(
        "<p>No <code>output/dashboard.html</code> in this deployment.</p>",
        status_code=404,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
