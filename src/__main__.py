"""
CLI entrypoint for running the TrueLend platform: `python -m src`

Per specs/app_spec.md §3:
  Applies migrations, seeds if empty, builds frontend/dist if missing and npm exists,
  serves API + UI on :8000.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

import uvicorn

from src.main import create_app


def build_frontend_if_needed() -> None:
    dist_dir = os.path.join("frontend", "dist")
    index_html = os.path.join(dist_dir, "index.html")
    if not os.path.exists(index_html) and os.path.exists("frontend"):
        npm_bin = shutil.which("npm")
        if npm_bin:
            print("Building frontend distribution assets via npm run build...")
            subprocess.run([npm_bin, "run", "build"], cwd="frontend", check=False)


def main() -> None:
    build_frontend_if_needed()
    app = create_app()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting TrueLend Platform on http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
