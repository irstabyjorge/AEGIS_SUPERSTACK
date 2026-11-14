"""Authenticated, read-only AEGIS API with bounded PETS formula evaluation."""
from __future__ import annotations

import hmac
import json
import os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from railway_app.formula import evaluate_objective

app = FastAPI(
    title="AEGIS OMEGA SUPERSTACK",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


ROLE_LEVEL = {"viewer": 1, "operator": 2, "admin": 3}


def load_token_roles() -> dict[str, str]:
    """Load token-to-role mappings from a secret environment variable."""
    raw = os.getenv("AEGIS_API_TOKENS", "")
    roles: dict[str, str] = {}
    if raw:
        try:
            supplied = json.loads(raw)
        except (TypeError, ValueError):
            supplied = {}
        if isinstance(supplied, dict):
            roles.update({
                token: role for token, role in supplied.items()
                if isinstance(token, str) and len(token) >= 24
                and isinstance(role, str) and role in ROLE_LEVEL
            })
    # Backward-compatible single token is treated as admin, but multi-user
    # deployments should use AEGIS_API_TOKENS and distinct least-privilege roles.
    legacy = os.getenv("AEGIS_API_TOKEN")
    if legacy and len(legacy) >= 24:
        roles.setdefault(legacy, "admin")
    return roles


def require_role(required_role: str):
    def dependency(authorization: str | None = Header(default=None)) -> str:
        roles = load_token_roles()
        if not roles:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authenticated API is not configured",
            )
        scheme, _, supplied = (authorization or "").partition(" ")
        role = next(
            (candidate for token, candidate in roles.items()
             if scheme.lower() == "bearer" and hmac.compare_digest(supplied, token)),
            None,
        )
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if ROLE_LEVEL[role] < ROLE_LEVEL[required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return role
    return dependency


require_viewer = require_role("viewer")
require_operator = require_role("operator")

ShortText = Annotated[str, Field(min_length=1, max_length=160)]


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: ShortText
    source: ShortText
    claim: Annotated[str, Field(min_length=1, max_length=2000)]
    observed_at: Annotated[str | None, Field(max_length=80)] = None


class FormulaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective: Annotated[str, Field(min_length=3, max_length=500)]
    evidence: list[EvidenceInput] = Field(default_factory=list, max_length=25)
    domains: list[ShortText] = Field(default_factory=list, max_length=8)
    options: list[ShortText] = Field(default_factory=list, max_length=8)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # Keep the public health response deliberately non-sensitive.
    return {"status": "ok"}


@app.get("/api/v1/status", dependencies=[Depends(require_viewer)])
def status_readonly() -> dict[str, str]:
    return {
        "application": "AEGIS_OMEGA_SUPERSTACK",
        "mode": "read-only-foundation",
        "readiness": "api-online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/formula/evaluate", dependencies=[Depends(require_operator)])
def formula_evaluate(request: FormulaRequest) -> dict:
    """Run a bounded local objective graph; no external or persistent actions."""
    return evaluate_objective(
        objective=request.objective,
        evidence=[item.model_dump() for item in request.evidence],
        domains=request.domains,
        options=request.options,
    )
