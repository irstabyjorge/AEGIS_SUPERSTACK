"""Owner-token protected ASGI entrypoint for the read-only AEGIS/PETS control plane."""
import hashlib
import hmac

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.wsgi import WSGIMiddleware

from cloud_control_plane import create_app

# SHA-256 of a high-entropy owner token; the raw token is not stored in source.
OWNER_TOKEN_SHA256 = "b9bc73211b483be0bf2ce6b60b736c47836f65bd73849347b9264aea890eb279"
_INTERNAL_GATE_TOKEN = "AEGIS_INTERNAL_GATE_TOKEN_NOT_ACCEPTED_FROM_NETWORK"

app = FastAPI(
    title="AEGIS/PETS Cloud Control Plane",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.middleware("http")
async def owner_only(request: Request, call_next):
    authorization = request.headers.get("authorization", "")
    scheme, separator, candidate = authorization.partition(" ")
    candidate_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest() if separator else ""
    if scheme.lower() != "bearer" or not hmac.compare_digest(candidate_hash, OWNER_TOKEN_SHA256):
        return JSONResponse(
            {"error": "unauthorized"},
            status_code=401,
            headers={"Cache-Control": "no-store", "WWW-Authenticate": "Bearer"},
        )

    # Pass a private internal credential to the existing WSGI app after the
    # external owner token has been verified.
    headers = [(key, value) for key, value in request.scope["headers"] if key.lower() != b"authorization"]
    headers.append((b"authorization", f"Bearer {_INTERNAL_GATE_TOKEN}".encode("ascii")))
    request.scope["headers"] = headers
    return await call_next(request)

app.mount("/", WSGIMiddleware(create_app(token=_INTERNAL_GATE_TOKEN)))
