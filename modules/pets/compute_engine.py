"""Safe compute backend selection with deterministic CPU fallback.

Optional GPU packages are detected by metadata only. No drivers are loaded,
no devices are enumerated, and no code is installed automatically.
"""
from __future__ import annotations
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Protocol

@dataclass(frozen=True)
class BackendStatus:
    backend_id: str
    available: bool
    selected: bool
    detail: str

class ComputeBackend(Protocol):
    backend_id: str
    def health_check(self) -> bool: ...
    def execute(self, operation: str, payload: dict) -> dict: ...

class CPUBackend:
    backend_id = "cpu"
    def health_check(self) -> bool: return True
    def execute(self, operation: str, payload: dict) -> dict:
        if operation != "identity":
            raise ValueError("CPU baseline currently supports only the identity test operation")
        return {"backend": self.backend_id, "result": payload, "verified": True}

class ComputeEngine:
    """CPU-first engine; GPU selection requires an explicitly registered adapter."""
    OPTIONAL_GPU_PACKAGES = ("torch", "cupy", "pyopencl")
    def __init__(self) -> None:
        self._backends: dict[str, ComputeBackend] = {"cpu": CPUBackend()}
        self.selected_backend = "cpu"
    def register_backend(self, backend: ComputeBackend) -> None:
        if not backend.backend_id or backend.backend_id == "cpu" or backend.backend_id in self._backends:
            raise ValueError("backend id must be unique and cannot replace CPU")
        self._backends[backend.backend_id] = backend
    def select(self, backend_id: str) -> str:
        if backend_id not in self._backends:
            raise ValueError("backend is not registered")
        if not self._backends[backend_id].health_check():
            self.selected_backend = "cpu"
            return "cpu"
        self.selected_backend = backend_id
        return backend_id
    def execute(self, operation: str, payload: dict) -> dict:
        backend = self._backends[self.selected_backend]
        try:
            return backend.execute(operation, payload)
        except Exception:
            if self.selected_backend == "cpu":
                raise
            self.selected_backend = "cpu"
            result = self._backends["cpu"].execute(operation, payload)
            result["fallback_reason"] = "selected backend failed; CPU fallback used"
            return result
    def inventory(self) -> dict:
        packages = {name: find_spec(name) is not None for name in self.OPTIONAL_GPU_PACKAGES}
        statuses = [BackendStatus(k, bool(v.health_check()), k == self.selected_backend, "registered adapter") for k, v in self._backends.items()]
        return {
            "selected_backend": self.selected_backend,
            "registered_backends": [s.__dict__ for s in statuses],
            "optional_gpu_packages_detected": packages,
            "gpu_hardware_verified": False,
            "note": "Package presence is not proof of a working GPU. Register and validate a vendor/backend adapter before GPU selection.",
        }
