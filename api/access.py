"""Access check for local-network mode.

When PC-Sahayak is shared on the local network, the launcher sets an access
code (PC_SAHAYAK_ACCESS_CODE). Requests from this computer itself are always
allowed; any other device must first open the share link (``/?access=<code>``),
which stores a cookie so the code never has to be typed again. Without a code
configured (the default, localhost-only mode) nothing is checked.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

COOKIE = "pcs_access"
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}

DENIED_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>PC-Sahayak</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#F1F4F9;color:#141B2D;
font:16px/1.55 system-ui,sans-serif;padding:16px}main{max-width:420px;text-align:center}
h1{font-size:22px;margin:0 0 8px}p{margin:0;color:#5D6880}
@media (prefers-color-scheme:dark){body{background:#0D1221;color:#E8ECF5}p{color:#97A2B8}}</style>
</head><body><main><h1>PC-Sahayak needs an access link</h1>
<p>Ask the person running PC-Sahayak for the share link shown in its window, then open that link on this device.</p>
</main></body></html>"""


def _token(code: str) -> str:
    """Cookie value derived from the code, so the code itself isn't stored in the browser."""
    return hmac.new(code.encode(), b"pc-sahayak-access", hashlib.sha256).hexdigest()


def is_local(request: Request) -> bool:
    return bool(request.client) and request.client.host in LOCAL_HOSTS


def install_access_check(app: FastAPI, code: Optional[str]) -> None:
    code = (code or "").strip()
    if not code:
        return
    token = _token(code)

    @app.middleware("http")
    async def access_check(request: Request, call_next):
        if is_local(request):
            return await call_next(request)
        given = request.query_params.get("access")
        if given is not None:
            if hmac.compare_digest(given.strip(), code):
                # Drop the code from the address bar; the cookie remembers it.
                resp = RedirectResponse(url=request.url.path or "/", status_code=303)
                resp.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
                return resp
        elif hmac.compare_digest(request.cookies.get(COOKIE, ""), token):
            return await call_next(request)
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "This device needs the PC-Sahayak access link."}, status_code=401)
        return HTMLResponse(DENIED_PAGE, status_code=401)
