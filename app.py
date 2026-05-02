"""
Vercel serverless ASGI entry (FastAPI).

`main.py` is the offline data pipeline — it does not export `app`, so this file
is the Python entry Vercel expects.

Note: Streamlit cannot run on Vercel's Python runtime. Use this deployment for
a landing page + optional static `output/dashboard.html`, or run Streamlit locally / on Streamlit Cloud.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

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
  <p>Vercel serves this FastAPI app. The interactive UI is <strong>Streamlit</strong> — run it on your machine or
     <a href="https://streamlit.io/cloud" rel="noopener">Streamlit Community Cloud</a> (not on Vercel serverless).</p>
  <p>Local run:</p>
  <pre>pip install -r requirements.txt
python main.py
python -m streamlit run streamlit_app.py</pre>
  <p>Static Plotly export: <a href="/dashboard">/dashboard</a> (only if <code>output/dashboard.html</code> exists in the deployment).</p>
</body>
</html>"""


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(_LANDING)


@app.get("/dashboard")
async def dashboard() -> FileResponse | HTMLResponse:
    if DASHBOARD_HTML.is_file():
        return FileResponse(DASHBOARD_HTML, media_type="text/html", filename="dashboard.html")
    return HTMLResponse(
        "<p>No <code>output/dashboard.html</code> in this deployment. "
        "Build it locally with <code>python main.py</code> and commit or upload the file if you need it here.</p>",
        status_code=404,
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
