"""Serve the latest dashboard PNG on the home LAN.

Lifebook runs this next to Home Assistant. The only picture it hands out
is ``GET /current.png``, and that request must carry the bearer token.
"""
from __future__ import annotations

import hmac
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from weather_display.paths import state_dir

DEFAULT_PORT = 8765

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t[%(levelname)s]\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def tokens_match(header: str, token: str) -> bool:
    expected = f"Bearer {token}".encode()
    given = header.encode()
    if len(given) != len(expected):
        return False
    return hmac.compare_digest(given, expected)


class DashboardHandler(BaseHTTPRequestHandler):
    directory: Path
    token: str

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, b"ok", "text/plain")
            return
        if path != "/current.png":
            self._send(404, b"not found", "text/plain")
            return
        if not tokens_match(self.headers.get("Authorization", ""), self.token):
            self._send(401, b"unauthorized", "text/plain")
            return
        picture = self.directory / "current.png"
        try:
            payload = picture.read_bytes()
        except OSError:
            self._send(404, b"not ready", "text/plain")
            return
        page = _page_name(self.directory)
        self._send(
            200,
            payload,
            "image/png",
            {"X-Dashboard-Page": page, "Cache-Control": "no-store"},
        )

    def log_message(self, fmt: str, *args) -> None:
        logging.info("request %s", fmt % args)

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)


def _page_name(directory: Path) -> str:
    try:
        return (directory / "current.page").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def make_server(directory: Path, token: str, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
    class Handler(DashboardHandler):
        pass

    Handler.directory = directory
    Handler.token = token
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def listen_port() -> int:
    raw = os.environ.get("DASHBOARD_PORT", str(DEFAULT_PORT)).strip() or str(DEFAULT_PORT)
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_PORT


def main() -> int:
    token = os.environ.get("DASHBOARD_TOKEN", "").strip()
    if not token:
        logging.error("DASHBOARD_TOKEN is required")
        return 1
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    server = make_server(directory, token, port=listen_port())
    logging.info("Serving dashboard images from %s on port %s", directory, server.server_address[1])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
