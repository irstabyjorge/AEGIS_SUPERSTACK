"""Minimal, read-only AEGIS/PETS cloud control plane.

This module deliberately does not import or invoke host-forensics, scanners,
network listeners, schedulers, blocklists, or autonomous response modules.
It exposes only health and static governance metadata.
"""
from __future__ import annotations

import hmac
import json
import os
from typing import Callable, Iterable


API_TOKEN_ENV = "AEGIS_CLOUD_API_TOKEN"
MIN_TOKEN_LENGTH = 32

PETS_POLICY = {
    "name": "PETS",
    "version": "0.1.0",
    "mode": "read_only",
    "evidence_handling": {
        "collects_host_data": False,
        "stores_personal_data": False,
        "accepts_uploads": False,
        "retention": "No evidence is collected or retained by this control plane.",
        "provenance_fields": [
            "record_id", "source", "observed_at", "collected_by",
            "integrity_sha256", "classification", "consent_basis",
        ],
    },
    "governance": {
        "human_approval_required_for_state_changes": True,
        "automatic_blocking": False,
        "remote_host_scanning": False,
        "public_forensics": False,
    },
}


def _response(start_response: Callable, status: str, payload: dict):
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
    ]
    start_response(status, headers)
    return [body]


def create_app(token: str | None = None):
    """Create a WSGI app. Configure a unique token of at least 32 chars."""
    configured_token = token if token is not None else os.getenv(API_TOKEN_ENV)

    def app(environ: dict, start_response: Callable) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if path == "/healthz":
            if method != "GET":
                return _response(start_response, "405 Method Not Allowed", {"error": "method_not_allowed"})
            return _response(start_response, "200 OK", {"status": "ok"})

        routes = {
            "/api/v1/pets/status": {
                "service": "AEGIS/PETS Cloud Control Plane",
                "mode": "read_only",
                "production_deployment": False,
                "state_changes_enabled": False,
            },
            "/api/v1/pets/evidence-policy": PETS_POLICY,
        }
        if path not in routes:
            return _response(start_response, "404 Not Found", {"error": "not_found"})
        if method != "GET":
            return _response(start_response, "405 Method Not Allowed", {"error": "method_not_allowed"})

        if not configured_token or len(configured_token) < MIN_TOKEN_LENGTH:
            return _response(start_response, "503 Service Unavailable", {"error": "service_not_configured"})

        supplied = environ.get("HTTP_AUTHORIZATION", "")
        prefix = "Bearer "
        if not supplied.startswith(prefix):
            return _response(start_response, "401 Unauthorized", {"error": "unauthorized"})
        candidate = supplied[len(prefix):]
        if not hmac.compare_digest(candidate.encode("utf-8"), configured_token.encode("utf-8")):
            return _response(start_response, "401 Unauthorized", {"error": "unauthorized"})

        return _response(start_response, "200 OK", routes[path])

    return app


application = create_app()
