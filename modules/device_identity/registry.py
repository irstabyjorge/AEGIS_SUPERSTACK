"""Read-only historical device registry and report helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = MODULE_DIR / "data" / "historical_devices.json"
VALID_CLASSES = {"HISTORICAL", "USER_CONFIRMED", "INDEPENDENTLY_VERIFIED"}


def load_registry(path: Path | str = REGISTRY_PATH) -> dict[str, Any]:
    """Load registry JSON without changing the source file."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_registry(data)
    return data


def validate_registry(data: dict[str, Any]) -> None:
    """Reject malformed records and prevent accidental promotion of history."""
    if data.get("schema_version") != "1.0":
        raise ValueError("Unsupported registry schema_version")
    devices = data.get("devices")
    if not isinstance(devices, list):
        raise ValueError("devices must be a list")
    seen = set()
    for device in devices:
        if not isinstance(device, dict):
            raise ValueError("Each device entry must be an object")
        required = {"record_id", "model", "classification", "verified", "source"}
        if not required.issubset(device):
            raise ValueError(f"Missing required fields: {sorted(required - set(device))}")
        if device["classification"] not in VALID_CLASSES:
            raise ValueError("Unknown classification")
        if device["record_id"] in seen:
            raise ValueError("Duplicate record_id")
        seen.add(device["record_id"])
        if device["classification"] == "HISTORICAL" and device["verified"] is not False:
            raise ValueError("Historical records must remain unverified")


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    """Create a timestamped summary; does not mutate registry data."""
    validate_registry(data)
    counts = {name: 0 for name in sorted(VALID_CLASSES)}
    for device in data["devices"]:
        counts[device["classification"]] += 1
    return {
        "project": data.get("project", "PETS–AEGIS"),
        "report_generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_registry": str(REGISTRY_PATH.name),
        "device_count": len(data["devices"]),
        "classification_counts": counts,
        "devices": data["devices"],
        "limitations": [
            "Historical mentions do not independently prove device ownership.",
            "No unique hardware identifiers were recovered or inferred.",
            "A device or browser fingerprint is not proof of a person's identity.",
            "No live device scan or online impersonation search was performed.",
        ],
    }


def sha256_file(path: Path | str) -> str:
    """Hash a file in read-only mode; return its SHA-256 digest."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
