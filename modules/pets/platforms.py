"""Portable PETS platform profile and explicit adapter registry.

Detects only the current Python runtime; it does not enumerate or probe devices.
"""
from __future__ import annotations
import platform
import sys
from typing import Protocol
from dataclasses import dataclass

SUPPORTED_ARCH = {"x86_64", "amd64", "aarch64", "arm64", "armv7l", "riscv64"}

@dataclass(frozen=True)
class PlatformProfile:
    os_name: str
    architecture: str
    python_implementation: str
    python_version: str
    supported_runtime: bool
    notes: tuple[str, ...] = ()

def detect_platform() -> PlatformProfile:
    raw = sys.platform
    os_name = "linux" if raw.startswith("linux") else ("windows" if raw.startswith("win") else ("macos" if raw == "darwin" else "unsupported"))
    arch = platform.machine().lower() or "unknown"
    supported = os_name in {"linux", "windows", "macos"} and arch in SUPPORTED_ARCH
    notes = []
    if os_name == "macos": notes.append("macOS runtime detected; iOS/iPadOS require a native Apple app bridge.")
    if os_name == "unsupported": notes.append("No native runtime adapter is registered for this operating system.")
    if arch not in SUPPORTED_ARCH: notes.append("Architecture is not yet in the validated support matrix.")
    return PlatformProfile(os_name, arch, platform.python_implementation(), platform.python_version(), supported, tuple(notes))

class PlatformAdapter(Protocol):
    adapter_id: str
    platforms: tuple[str, ...]
    def health_check(self) -> bool: ...

class PlatformAdapterRegistry:
    """Explicit registry; adapters are never auto-discovered or auto-started."""
    def __init__(self) -> None:
        self._adapters: dict[str, PlatformAdapter] = {}
    def register(self, adapter: PlatformAdapter) -> None:
        if not adapter.adapter_id or adapter.adapter_id in self._adapters:
            raise ValueError("adapter_id must be non-empty and unique")
        if not adapter.platforms:
            raise ValueError("adapter must declare at least one platform")
        self._adapters[adapter.adapter_id] = adapter
    def for_platform(self, os_name: str) -> tuple[PlatformAdapter, ...]:
        return tuple(a for a in self._adapters.values() if os_name in a.platforms)
    def health(self) -> dict[str, bool]:
        return {key: adapter.health_check() for key, adapter in self._adapters.items()}

def supported_targets() -> dict[str, tuple[str, ...]]:
    """Intended targets, not a claim that native bridges exist or are tested."""
    return {
        "linux": ("x86_64", "aarch64", "armv7l", "riscv64"),
        "windows": ("x86_64", "amd64", "arm64"),
        "macos": ("arm64", "x86_64"),
        "android": ("arm64", "armv7l", "x86_64"),
        "ios_ipados": ("arm64",),
        "embedded_iot": ("armv7l", "aarch64", "riscv64"),
    }
