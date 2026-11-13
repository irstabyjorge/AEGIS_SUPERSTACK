import datetime
import hashlib
import json
from pathlib import Path


ZERO_HASH = "0" * 64


def canonical_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def make_manifest(repository):
    doc = {
        "schema": "pets.aegis.hf.repo-manifest.v2",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "master_system": "PETS",
        "protection_module": "AEGIS_OMEGA/HF_IP_SHIELD",
        "repository": repository,
        "evidence_limits": [
            "Hub LFS SHA-256 values are provider metadata, not independently recomputed file hashes.",
            "Git blob identifiers are SHA-1; this tool does not download model weights or dataset contents.",
            "Metadata does not prove authorship, ownership, originality, or legal registration.",
            "Hub timestamps are not a trusted timestamp authority.",
            "A local hash chain is tamper-evident, not immutable against an administrator controlling its storage."
        ]
    }
    doc["manifest_sha256"] = digest(doc)
    return doc


def verify_manifest(doc):
    if not isinstance(doc, dict):
        return False
    claimed = doc.get("manifest_sha256")
    body = dict(doc)
    body.pop("manifest_sha256", None)
    try:
        return isinstance(claimed, str) and len(claimed) == 64 and claimed == digest(body)
    except (TypeError, ValueError):
        return False


def verify_ledger(path):
    path = Path(path)
    previous = ZERO_HASH
    count = 0
    if not path.exists():
        return {"valid": True, "events": 0}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return {"valid": False, "events": 0, "error": type(exc).__name__}
    for number, line in enumerate(lines, 1):
        if not line.strip():
            return {"valid": False, "events": count, "line": number, "error": "blank_record"}
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("record_not_object")
            claimed = record.get("event_hash")
            body = dict(record)
            body.pop("event_hash", None)
            if record.get("sequence") != count:
                return {"valid": False, "events": count, "line": number, "error": "sequence_mismatch"}
            if record.get("previous_hash") != previous:
                return {"valid": False, "events": count, "line": number, "error": "previous_hash_mismatch"}
            if not isinstance(claimed, str) or claimed != digest(body):
                return {"valid": False, "events": count, "line": number, "error": "event_hash_mismatch"}
            previous = claimed
            count += 1
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"valid": False, "events": count, "line": number, "error": "invalid_record"}
    return {"valid": True, "events": count, "head_hash": previous}


def append_ledger(path, event):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = verify_ledger(path)
    if not state["valid"]:
        raise ValueError("Audit ledger verification failed; refusing to append.")
    record = {
        "sequence": state["events"],
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "previous_hash": state.get("head_hash", ZERO_HASH),
        "event": event
    }
    record["event_hash"] = digest(record)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
    return record
