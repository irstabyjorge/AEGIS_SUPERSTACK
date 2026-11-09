"""QBYTE header-only executable and script format recognition.

This module reads bounded file headers only. It never executes, extracts,
installs, patches, or recursively discovers files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

MAX_HEADER_BYTES = 65_536

_ARCH = {
    0x014C: "x86",
    0x8664: "x86_64",
    0x01C0: "arm",
    0x01C4: "armv7",
    0xAA64: "aarch64",
    0x0003: "x86",
    0x003E: "x86_64",
    0x0028: "arm",
    0x00B7: "aarch64",
    0x00F3: "riscv",
}
_MACH_CPU = {
    7: "x86",
    0x01000007: "x86_64",
    12: "arm",
    0x0100000C: "aarch64",
}


@dataclass(frozen=True)
class FormatProfile:
    format_id: str
    architecture: str | None
    platform_hint: str | None
    runtime_hint: str | None
    confidence: str
    executable_candidate: bool
    evidence: tuple[str, ...]
    inspection_only: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def _profile(format_id: str, architecture: str | None = None,
             platform_hint: str | None = None, runtime_hint: str | None = None,
             confidence: str = "high", executable: bool = True,
             *evidence: str) -> FormatProfile:
    return FormatProfile(format_id, architecture, platform_hint, runtime_hint,
                         confidence, executable, tuple(evidence))


def _script_profile(data: bytes, suffix: str) -> FormatProfile | None:
    extensions = {
        ".py": ("python_source", "python"),
        ".sh": ("shell_source", "posix_shell"),
        ".bash": ("shell_source", "bash"),
        ".zsh": ("shell_source", "zsh"),
        ".ps1": ("powershell_source", "powershell"),
        ".bat": ("windows_batch_source", "cmd"),
        ".cmd": ("windows_batch_source", "cmd"),
        ".js": ("javascript_source", "node_or_browser"),
        ".mjs": ("javascript_source", "node_or_browser"),
        ".cjs": ("javascript_source", "node_or_browser"),
        ".swift": ("swift_source", "swift_toolchain"),
        ".rb": ("ruby_source", "ruby"),
        ".pl": ("perl_source", "perl"),
    }
    if data.startswith(b"#!"):
        first_line = data.splitlines()[0][2:256].decode("utf-8", "replace").strip()
        tokens = first_line.split()
        interpreter = tokens[0].rsplit("/", 1)[-1] if tokens else "unknown"
        if interpreter == "env" and len(tokens) > 1:
            interpreter = tokens[1].rsplit("/", 1)[-1]
        language = {
            "python": "python", "python3": "python", "bash": "bash",
            "sh": "posix_shell", "zsh": "zsh", "node": "node",
            "ruby": "ruby", "perl": "perl",
        }.get(interpreter, interpreter)
        return _profile("script_source", None, None, language, "high", False,
                        "shebang interpreter identified", first_line[:160])
    if suffix in extensions:
        format_id, runtime = extensions[suffix]
        return _profile(format_id, None, None, runtime, "medium", False,
                        f"recognized source extension: {suffix}")
    return None


def scan_bytes(data: bytes, filename: str = "") -> FormatProfile:
    """Recognize a format from a bounded header supplied by the caller."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data_must_be_bytes")
    header = bytes(data[:MAX_HEADER_BYTES])
    suffix = Path(filename).suffix.lower()

    if header.startswith(b"\x7fELF"):
        if len(header) < 20:
            return _profile("elf_incomplete_header", None, None, "ELF loader",
                            "low", True, "ELF magic present; header truncated")
        elf_class = header[4]
        encoding = header[5]
        endian = "little" if encoding == 1 else "big" if encoding == 2 else None
        if endian is None or elf_class not in (1, 2):
            return _profile("elf_unrecognized_variant", None, None, "ELF loader",
                            "low", True, "ELF magic present; invalid class or byte order")
        machine = int.from_bytes(header[18:20], endian)
        arch = _ARCH.get(machine, f"elf_machine_{machine}")
        bits = 32 if elf_class == 1 else 64
        return _profile("elf", arch, "linux_or_android", "ELF-compatible runtime",
                        "high", True, f"{bits}-bit ELF", f"byte_order={endian}",
                        f"e_machine={machine}")

    if header.startswith(b"MZ"):
        if len(header) >= 64:
            pe_offset = int.from_bytes(header[0x3C:0x40], "little")
            if pe_offset <= len(header) - 6 and header[pe_offset:pe_offset + 4] == b"PE\x00\x00":
                machine = int.from_bytes(header[pe_offset + 4:pe_offset + 6], "little")
                arch = _ARCH.get(machine, f"pe_machine_{machine}")
                return _profile("pe_coff", arch, "windows", "Windows PE loader",
                                "high", True, "MZ and PE signatures present",
                                f"machine=0x{machine:04x}")
        return _profile("dos_mz_or_pe_candidate", None, "windows_candidate",
                        "PE validation required", "low", True,
                        "MZ signature present; PE signature not confirmed in bounded header")

    macho = {
        b"\xfe\xed\xfa\xce": ("big", 32),
        b"\xce\xfa\xed\xfe": ("little", 32),
        b"\xfe\xed\xfa\xcf": ("big", 64),
        b"\xcf\xfa\xed\xfe": ("little", 64),
    }
    if len(header) >= 8 and header[:4] in macho:
        endian, bits = macho[header[:4]]
        cpu = int.from_bytes(header[4:8], endian, signed=True)
        return _profile("mach_o", _MACH_CPU.get(cpu, f"macho_cpu_{cpu}"),
                        "macos", "Apple Mach-O loader", "high", True,
                        f"{bits}-bit Mach-O", f"cpu_type={cpu}")

    if header.startswith((b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca")):
        return _profile("mach_o_universal", "multi_arch", "macos",
                        "Apple universal-binary loader", "medium", True,
                        "fat Mach-O magic present; architecture table not expanded")

    if header.startswith(b"\x00asm"):
        if len(header) >= 8:
            version = int.from_bytes(header[4:8], "little")
            return _profile("wasm_core_module", "wasm32", "portable",
                            "WebAssembly runtime (for example, Wasmtime)",
                            "high", True, f"WebAssembly magic; version={version}")
        return _profile("wasm_incomplete_header", None, "portable",
                        "WebAssembly runtime", "low", True,
                        "WebAssembly magic present; version truncated")

    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        candidate = "android_candidate" if suffix == ".apk" else "archive"
        return _profile("zip_container", None, candidate, "ZIP reader",
                        "high", False, "ZIP signature present",
                        "APK status requires archive-manifest inspection")

    script = _script_profile(header, suffix)
    if script is not None:
        return script

    return _profile("unknown", None, None, None, "low", False,
                    "no recognized signature in bounded header")


def scan_file(path: str | Path) -> FormatProfile:
    """Read at most MAX_HEADER_BYTES from one explicitly supplied regular file."""
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("symlink_input_not_allowed")
    if not candidate.is_file():
        raise ValueError("input_must_be_regular_file")
    with candidate.open("rb") as stream:
        header = stream.read(MAX_HEADER_BYTES)
    return scan_bytes(header, candidate.name)
