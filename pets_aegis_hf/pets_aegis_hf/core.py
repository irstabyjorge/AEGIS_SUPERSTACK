import hashlib, json, datetime
from pathlib import Path

def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

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
            "Hub timestamps are not a trusted timestamp authority."
        ]
    }
    doc["manifest_sha256"] = digest(doc)
    return doc

def verify_manifest(doc):
    claimed = doc.get("manifest_sha256")
    body = dict(doc)
    body.pop("manifest_sha256", None)
    return bool(claimed) and claimed == digest(body)

def append_ledger(path, event):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    sequence = 0
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            last = json.loads(lines[-1])
            previous = last["event_hash"]
            sequence = last["sequence"] + 1
    record = {
        "sequence": sequence,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "previous_hash": previous,
        "event": event
    }
    record["event_hash"] = digest(record)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record

def verify_ledger(path):
    path = Path(path)
    previous = "0" * 64
    count = 0
    if not path.exists():
        return {"valid": True, "events": 0}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        claimed = record.pop("event_hash", None)
        if record.get("previous_hash") != previous or claimed != digest(record):
            return {"valid": False, "events": count, "line": number}
        previous = claimed
        count += 1
    return {"valid": True, "events": count}
