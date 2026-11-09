"""PETS compatibility switch: choose a verified route, never launch code."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .platforms import PlatformProfile, detect_platform
from .qbyte_format_scanner import FormatProfile


_ARCH_ALIASES = {
    "amd64": "x86_64",
    "x64": "x86_64",
    "arm64": "aarch64",
}


def _norm_arch(value: str) -> str:
    normalized = value.lower()
    return _ARCH_ALIASES.get(normalized, normalized)


@dataclass(frozen=True)
class RuntimeDescriptor:
    runtime_id: str
    formats: tuple[str, ...]
    platforms: tuple[str, ...]
    architectures: tuple[str, ...]
    verified: bool = False
    sandboxed: bool = False


class CompatibilitySwitch:
    """Explicit runtime registry with a plan-only decision boundary."""

    def __init__(self, runtimes: Iterable[RuntimeDescriptor] = ()):
        self._runtimes: dict[str, RuntimeDescriptor] = {}
        for runtime in runtimes:
            self.register(runtime)

    def register(self, runtime: RuntimeDescriptor) -> None:
        if not runtime.runtime_id or runtime.runtime_id in self._runtimes:
            raise ValueError("runtime_id_must_be_nonempty_and_unique")
        if not runtime.formats or not runtime.platforms or not runtime.architectures:
            raise ValueError("runtime_must_declare_formats_platforms_and_architectures")
        self._runtimes[runtime.runtime_id] = runtime

    def inventory(self) -> dict:
        return {
            key: asdict(value)
            for key, value in sorted(self._runtimes.items())
        }

    def plan(self, profile: FormatProfile,
             host: PlatformProfile | None = None) -> dict:
        host = host or detect_platform()
        host_arch = _norm_arch(host.architecture)
        eligible = [
            runtime for runtime in self._runtimes.values()
            if profile.format_id in runtime.formats
            and host.os_name in runtime.platforms
            and host_arch in {_norm_arch(a) for a in runtime.architectures}
            and runtime.verified and runtime.sandboxed
        ]
        if eligible:
            chosen = sorted(eligible, key=lambda item: item.runtime_id)[0]
            return {
                "status": "verified_runtime_candidate",
                "route": "registered_sandboxed_runtime",
                "runtime_id": chosen.runtime_id,
                "format_id": profile.format_id,
                "host_platform": host.os_name,
                "host_architecture": host_arch,
                "execution_performed": False,
                "approval_required": True,
                "blockers": [],
            }

        native_formats = {
            "pe_coff": ("windows",),
            "mach_o": ("macos",),
            "mach_o_universal": ("macos",),
            "elf": ("linux", "android"),
        }
        compatible_hosts = native_formats.get(profile.format_id, ())
        if host.os_name in compatible_hosts and (
            profile.architecture is None
            or _norm_arch(profile.architecture) == host_arch
        ):
            return {
                "status": "native_loader_candidate",
                "route": "host_native_loader",
                "runtime_id": None,
                "format_id": profile.format_id,
                "host_platform": host.os_name,
                "host_architecture": host_arch,
                "execution_performed": False,
                "approval_required": True,
                "blockers": [
                    "No launch performed",
                    "Dependencies, ABI, signatures and application permissions still require validation",
                ],
            }

        if profile.format_id == "wasm_core_module":
            reason = "No verified sandboxed WebAssembly runtime is registered for this host."
        elif profile.format_id == "zip_container":
            reason = "Container recognized; package manifest and contents have not been inspected."
        elif profile.format_id in {"unknown", "dos_mz_or_pe_candidate",
                                   "elf_incomplete_header", "wasm_incomplete_header"}:
            reason = "Format is unknown or incomplete; no runtime route can be selected."
        else:
            reason = "No verified compatible runtime is registered for this format and host."
        return {
            "status": "blocked_no_verified_route",
            "route": None,
            "runtime_id": None,
            "format_id": profile.format_id,
            "host_platform": host.os_name,
            "host_architecture": host_arch,
            "execution_performed": False,
            "approval_required": True,
            "blockers": [reason],
        }
