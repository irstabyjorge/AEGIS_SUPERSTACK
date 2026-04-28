from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import json, os, time
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://nats.aegis.svc.cluster.local:4222")
QUANTUM_PRECHECK_RISK = float(os.getenv("QUANTUM_PRECHECK_RISK", "0.72"))
app = FastAPI(title="AEGIS Scheduler API", version="1.0.0")
nc = NATS()


class Task(BaseModel):
    type: str
    priority: int = Field(5, ge=0, le=10)
    requires_gpu: bool = False
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    payload: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None


@app.on_event("startup")
async def startup():
    await nc.connect(NATS_URL)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "nats_connected": nc.is_connected, "time": time.time()}


@app.post("/task")
async def submit_task(task: Task):
    if not nc.is_connected:
        raise HTTPException(status_code=503, detail="NATS unavailable")
    envelope = task.model_dump()
    envelope["scheduler_ts"] = time.time()
    if task.risk_score >= QUANTUM_PRECHECK_RISK or task.type == "identity_event":
        subject = "tasks.quantum"
    elif task.requires_gpu or task.type == "rag_query":
        subject = "tasks.gpu"
    elif task.type == "telemetry_event":
        subject = "tasks.stream"
    else:
        subject = "tasks.cpu"
    await nc.publish(subject, json.dumps(envelope).encode())
    return {"status": "queued", "subject": subject, "trace_id": task.trace_id}
