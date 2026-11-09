"""Provider-neutral PETS Universal Intermediate Representation.

The IR describes approved, structured tasks. It is not a general-purpose
programming language and does not carry executable machine code or shell text.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_ID = "PETS_UNIVERSAL_IR"
SCHEMA_VERSION = "1.0.0"
MAX_IR_BYTES = 65_536
ALLOWED_PLATFORMS = {
    "linux", "windows", "macos", "android", "ios_ipados",
    "embedded_iot", "wasm",
}
OPERATIONS = {
    "inspect_file_header": {"required": {"file_name": str}, "optional": {}},
    "analyze_text": {"required": {"text": str}, "optional": {"language": str}},
    "transcribe_audio": {"required": {"asset_ref": str}, "optional": {"language": str}},
    "translate_text": {"required": {"text": str, "target_language": str},
                       "optional": {"source_language": str}},
    "translate_audio": {"required": {"asset_ref": str, "target_language": str},
                        "optional": {"source_language": str}},
    "summarize_recording": {"required": {"asset_ref": str},
                            "optional": {"language": str}},
    "generate_report": {"required": {"title": str, "sections": list},
                        "optional": {"language": str}},
}


@dataclass(frozen=True)
class UniversalOperation:
    operation: str
    arguments: dict[str, Any]
    source_language: str | None = None
    target_language: str | None = None
    target_platforms: tuple[str, ...] = ()
    request_text: str | None = None
    approval_required: bool = True
    execution_mode: str = "plan_only"

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            **asdict(self),
        }


def build_operation(*, operation: str, arguments: dict[str, Any],
                    source_language: str | None = None,
                    target_language: str | None = None,
                    target_platforms: tuple[str, ...] = (),
                    request_text: str | None = None) -> UniversalOperation:
    """Validate and normalize one structured task; never execute it."""
    if operation not in OPERATIONS:
        raise ValueError("operation_not_allowlisted")
    if not isinstance(arguments, dict):
        raise ValueError("arguments_must_be_object")
    schema = OPERATIONS[operation]
    required, optional = schema["required"], schema["optional"]
    if set(arguments) - (set(required) | set(optional)):
        raise ValueError("unknown_argument")
    for key, expected in required.items():
        if key not in arguments or not isinstance(arguments[key], expected):
            raise ValueError(f"invalid_or_missing_argument:{key}")
    for key, expected in optional.items():
        if key in arguments and not isinstance(arguments[key], expected):
            raise ValueError(f"invalid_argument_type:{key}")
    if any(not isinstance(value, str) for value in
           (source_language, target_language, request_text) if value is not None):
        raise ValueError("language_and_request_fields_must_be_strings")
    if any(platform not in ALLOWED_PLATFORMS for platform in target_platforms):
        raise ValueError("target_platform_not_allowlisted")
    normalized = {
        "operation": operation,
        "arguments": arguments,
        "source_language": source_language,
        "target_language": target_language,
        "target_platforms": tuple(target_platforms),
        "request_text": request_text,
        "approval_required": True,
        "execution_mode": "plan_only",
    }
    try:
        encoded = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("arguments_must_be_json_serializable") from exc
    if len(encoded.encode("utf-8")) > MAX_IR_BYTES:
        raise ValueError("ir_payload_too_large")
    return UniversalOperation(**normalized)
