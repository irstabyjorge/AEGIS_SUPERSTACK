"""Minimal, read-only AEGIS Railway entrypoint.

This service intentionally does not expose host inspection, scanning, blocking,
forensic collection, password auditing, or device-control operations.
"""
from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, status

app = FastAPI(
    title="AEGIS OMEGA SUPERSTACK",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("AEGIS_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authenticated API is not configured",
        )
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # Keep the public health response deliberately non-sensitive.
    return {"status": "ok"}


@app.get("/api/v1/status", dependencies=[Depends(require_api_token)])
def status_readonly() -> dict[str, str]:
    return {
        "application": "AEGIS_OMEGA_SUPERSTACK",
        "mode": "read-only-foundation",
        "readiness": "api-online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
