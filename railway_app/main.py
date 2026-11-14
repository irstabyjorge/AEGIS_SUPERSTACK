"""Authenticated, read-only AEGIS API with bounded PETS formula evaluation."""
from __future__ import annotations

import hmac
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


@app.get("/api/v1/status", dependencies=[Depends(require_api_token)])
def status_readonly() -> dict[str, str]:
    return {
        "application": "AEGIS_OMEGA_SUPERSTACK",
        "mode": "read-only-foundation",
        "readiness": "api-online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/formula/evaluate", dependencies=[Depends(require_api_token)])
def formula_evaluate(request: FormulaRequest) -> dict:
    """Run a bounded local objective graph; no external or persistent actions."""
    return evaluate_objective(
        objective=request.objective,
        evidence=[item.model_dump() for item in request.evidence],
        domains=request.domains,
        options=request.options,
    )
