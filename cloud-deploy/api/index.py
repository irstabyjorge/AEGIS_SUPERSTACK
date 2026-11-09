"""Vercel ASGI entrypoint for the read-only AEGIS/PETS WSGI control plane."""
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from cloud_control_plane import create_app

app = FastAPI(
    title="AEGIS/PETS Cloud Control Plane",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount("/", WSGIMiddleware(create_app()))
