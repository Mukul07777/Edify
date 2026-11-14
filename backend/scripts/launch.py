"""Start Edify: pick a free port, open the browser when the server is healthy, run uvicorn.

Used by run.bat, but works anywhere:  python scripts/launch.py [--no-browser]
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _stream in (sys.stdout, sys.stderr):  # a console or log file in an old Windows code page: print "?" for an arrow, don't stop
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

import app  # noqa: E402,F401  (Windows MSVC runtime preload happens on import)
import uvicorn  # noqa: E402

from app.core.buildinfo import fingerprint  # noqa: E402
from app.core.config import settings  # noqa: E402


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((settings.HOST, port))
            return True
        except OSError:
            return False


def edify_health(port: int, timeout: float = 1.0) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as r:
            data = json.loads(r.read())
            return data if data.get("status") == "ok" else None  # the public health check names no app or models
    except Exception:
        return None


def lan_addresses() -> list[str]:
    """This computer's addresses on the local network (what a phone on the same Wi-Fi types)."""
    found: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:  # (no packet is sent: this only picks the outgoing interface)
            s.connect(("10.255.255.255", 1))
            found.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        found += [a for a in socket.gethostbyname_ex(socket.gethostname())[2] if not a.startswith("127.")]
    except OSError:
        pass
    return list(dict.fromkeys(a for a in found if not a.startswith("127.")))


def open_when_ready(port: int, url: str) -> None:
    for _ in range(120):
        health = edify_health(port)
        if health:
            llm = health["llm"]
            print(f"\n  Edify is ready at {url}")
            if settings.HOST == "0.0.0.0":  # open to the local network (mobile/serve_for_phone.bat)
                for address in lan_addresses():
                    print(f"  On your phone : http://{address}:{port}   (same Wi-Fi; type this in the Edify app)")
            # the models and OCR engines are in the log lines above (the public health check leaves them out)
            print(f"  AI notes : {'ON' if llm['available'] else 'OFFLINE mode - add GROQ_API_KEY to backend/.env for AI notes'}")
            print("\n  Keep this window open while you study. Press Ctrl+C to stop.\n")
            if "--no-browser" not in sys.argv:
                webbrowser.open(url)
            return
        time.sleep(0.5)
    print("  ! The server did not become healthy within 60 s — see the messages above.")


def start_local_coach() -> None:
    """Edify Coach on this PC (MARITIME_COACH_URL=http://127.0.0.1:<port>): the same agent Maritime runs, started
    alongside Edify and stopped with it. Each student's memory is kept apart under backend/storage/coach."""
    from urllib.parse import urlparse

    url = urlparse(settings.MARITIME_COACH_URL)
    if url.hostname not in ("127.0.0.1", "localhost") or (settings.MARITIME_API_KEY and settings.MARITIME_COACH_REPO):
        return  # on Maritime, or a coach somewhere else: nothing to start here
    port = url.port or 8787
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1):
            print(f"  Edify Coach is already running on port {port}")
            return
    except Exception:
        pass
    import atexit
    import subprocess

    server = BACKEND.parent / "agents" / "edify-coach" / "server.py"
    env = {**os.environ, "PORT": str(port), "COACH_DATA": str(BACKEND / "storage" / "coach"),
           "LLM_API_KEY": settings.llm_api_key, "LLM_BASE_URL": settings.LLM_BASE_URL,
           "COACH_MODEL": settings.LLM_MODEL.split(",")[0].strip()}
    proc = subprocess.Popen([sys.executable, str(server)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    atexit.register(proc.terminate)
    print(f"  Edify Coach   : on this PC (port {port}); set MARITIME_COACH_REPO to run it on Maritime")


def main() -> None:
    start_local_coach()
    preferred = int(os.environ.get("PORT") or settings.PORT)
    running = edify_health(preferred)
    if running and running.get("build") == fingerprint():
        url = f"http://localhost:{preferred}"
        print(f"  Edify is already running at {url} — opening it.")
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        return
    if running:  # an older Edify (started before the last update) still holds the port: don't send people to it
        print(f"  The Edify on port {preferred} is an older version — starting the updated one alongside it.")
        print("  (Close the old Edify window when you get a chance.)")
    port = next((p for p in range(preferred, preferred + 20) if port_free(p)), None)
    if port is None:
        sys.exit(f"  ! Ports {preferred}-{preferred + 19} are all busy. Set PORT in backend/.env.")
    if port != preferred:
        print(f"  Port {preferred} is busy, using {port} instead.")
    host = "localhost" if settings.HOST in ("127.0.0.1", "0.0.0.0") else settings.HOST
    url = f"http://{host}:{port}"
    print(f"  Starting Edify on {url} ...")
    threading.Thread(target=open_when_ready, args=(port, url), daemon=True).start()
    try:
        uvicorn.run("app.main:app", host=settings.HOST, port=port, log_level="warning", timeout_keep_alive=75)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
