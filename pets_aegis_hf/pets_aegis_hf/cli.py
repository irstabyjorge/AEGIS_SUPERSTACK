import argparse, json, os, sys, hashlib
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd
from .core import make_manifest, verify_manifest, append_ledger, verify_ledger

OWNERS = ["AEGISGODMODE", "AEGISWALLS"]
TARGET = ".pets-aegis/IP_SHIELD.json"

def discover(api, owners):
    result = []
    for owner in owners:
        for kind, method in (("model", api.list_models), ("dataset", api.list_datasets), ("space", api.list_spaces)):
            try:
                result.extend((item.id, kind) for item in method(author=owner) if getattr(item, "id", None))
            except Exception as exc:
                result.append({"owner": owner, "kind": kind, "error_type": type(exc).__name__})
    return result

def inspect(api, repo_id, kind):
    info = api.repo_info(repo_id=repo_id, repo_type=kind, files_metadata=True)
    files = []
    for item in getattr(info, "siblings", None) or []:
        lfs = getattr(item, "lfs", None)
        files.append({
            "path": getattr(item, "rfilename", None),
            "size_bytes": getattr(item, "size", None),
            "git_blob_id_sha1": getattr(item, "blob_id", None),
            "hub_lfs_sha256": getattr(lfs, "sha256", None) if lfs else None
        })
    return {
        "repo_id": repo_id, "repo_type": kind, "revision": getattr(info, "sha", None),
        "private": getattr(info, "private", None), "gated": getattr(info, "gated", None),
        "last_modified": str(getattr(info, "last_modified", None)),
        "pipeline_tag": getattr(info, "pipeline_tag", None),
        "library_name": getattr(info, "library_name", None),
        "tags": list(getattr(info, "tags", None) or []),
        "files": sorted(files, key=lambda x: x["path"] or ""),
        "file_count": len(files), "evidence_class": "observed"
    }

def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {path.name}")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"Temporary evidence path already exists: {temporary.name}")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def manifest_filename(repo_id, kind):
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in repo_id)
    suffix = hashlib.sha256(repo_id.encode("utf-8")).hexdigest()[:12]
    return f"{safe}__{kind}__{suffix}.json"


def load_verified_index(root):
    root = Path(root)
    index_path = root / "INDEX.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("schema") != "pets.aegis.hf.inventory.v2":
        raise ValueError("Unsupported inventory schema.")
    for item in index.get("repositories", []):
        if item.get("status") != "inventoried":
            continue
        manifest_path = root / item["manifest"]
        if manifest_path.parent != root or not manifest_path.is_file():
            raise ValueError("Manifest path is missing or invalid.")
        if not verify_manifest(json.loads(manifest_path.read_text(encoding="utf-8"))):
            raise ValueError("Manifest integrity check failed; refusing remote operation.")
    ledger_path = root / "audit-ledger.jsonl"
    ledger_state = verify_ledger(ledger_path)
    if not ledger_state["valid"]:
        raise ValueError("Audit ledger integrity check failed; refusing operation.")
    index_hash = hashlib.sha256(index_path.read_bytes()).hexdigest()
    ledger_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not any(
        row.get("event", {}).get("action") == "inventory"
        and row.get("event", {}).get("index_sha256") == index_hash
        for row in ledger_records
    ):
        raise ValueError("Inventory index is not anchored in the verified audit ledger.")
    return index

def inventory(args):
    api = HfApi()
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    root = output_root / ("run-" + run_id)
    root.mkdir(parents=True, exist_ok=False)
    index = {"schema":"pets.aegis.hf.inventory.v2","master":"PETS","module":"AEGIS_OMEGA/HF_IP_SHIELD","repositories":[],"run_id":run_id,"coverage_status":"partial_pending_review","limitations":["Metadata only; no weights or dataset contents downloaded.","Git blob IDs are SHA-1; LFS SHA-256 is Hub-provided metadata.","Not proof of legal ownership, authorship, or trusted time."]}
    targets = []
    for item in discover(api, args.owners):
        if isinstance(item, dict):
            index["repositories"].append({"status":"discovery_error", **item})
        else:
            targets.append(item)
    for repo_id, kind in dict.fromkeys(targets):
        try:
            record = inspect(api, repo_id, kind)
            manifest = make_manifest(record)
            name = manifest_filename(repo_id, kind)
            write_json(root/name, manifest)
            index["repositories"].append({"repo_id":repo_id,"repo_type":kind,"revision":record["revision"],"file_count":record["file_count"],"manifest":name,"status":"inventoried"})
        except Exception as exc:
            index["repositories"].append({"repo_id":repo_id,"repo_type":kind,"status":"error","error_type":type(exc).__name__})
    statuses = [item.get("status") for item in index["repositories"]]
    index["coverage_status"] = "complete" if statuses and all(status == "inventoried" for status in statuses) else "partial"
    write_json(root/"INDEX.json", index)
    append_ledger(root/"audit-ledger.jsonl", {"action":"inventory","index_sha256":hashlib.sha256((root/"INDEX.json").read_bytes()).hexdigest(),"repositories":len(index["repositories"]),"coverage_status":index["coverage_status"]})
    print(json.dumps({"repositories":len(index["repositories"]),"coverage_status":index["coverage_status"],"output":str(root)}, indent=2))

def verify(args):
    root = Path(args.evidence)
    results = []
    for path in root.glob("*__*.json"):
        try:
            results.append({"file":path.name,"valid":verify_manifest(json.loads(path.read_text(encoding="utf-8")))})
        except Exception as exc:
            results.append({"file":path.name,"valid":False,"error_type":type(exc).__name__})
    ledger = verify_ledger(root/"audit-ledger.jsonl")
    print(json.dumps({"manifests":results,"ledger":ledger}, indent=2))
    if any(not x["valid"] for x in results) or not ledger["valid"]:
        sys.exit(2)

def audit(args):
    api = HfApi()
    root = Path(args.evidence)
    index = load_verified_index(root)
    changes = []
    for old in index.get("repositories", []):
        if old.get("status") != "inventoried":
            continue
        try:
            current = inspect(api, old["repo_id"], old["repo_type"])
            changes.append({"repo_id":old["repo_id"],"previous_revision":old["revision"],"current_revision":current["revision"],"changed":old["revision"] != current["revision"]})
        except Exception as exc:
            changes.append({"repo_id":old["repo_id"],"error_type":type(exc).__name__})
    write_json(root/"AUDIT.json", {"schema":"pets.aegis.hf.audit.v1","changes":changes})
    append_ledger(root/"audit-ledger.jsonl", {"action":"audit","results":changes})
    print(json.dumps(changes, indent=2))

def publish(args):
    if not args.confirm_write:
        raise SystemExit("Explicit --confirm-write is required.")
    api = HfApi()
    root = Path(args.evidence)
    index = load_verified_index(root)
    outcomes = []
    for item in index.get("repositories", []):
        if item.get("status") != "inventoried":
            continue
        try:
            info = api.repo_info(repo_id=item["repo_id"], repo_type=item["repo_type"], files_metadata=True)
            paths = {x.rfilename for x in (info.siblings or [])}
            if TARGET in paths:
                status = "skipped-existing"
            else:
                source = root/item["manifest"]
                api.create_commit(repo_id=item["repo_id"], repo_type=item["repo_type"], operations=[CommitOperationAdd(path_in_repo=TARGET, path_or_fileobj=source)], commit_message="Add PETS/AEGIS IP Shield manifest")
                status = "committed"
        except Exception as exc:
            status = "error_type: " + type(exc).__name__
        outcomes.append({"repo_id":item["repo_id"],"status":status})
    write_json(root/"PUBLISH.json", {"outcomes":outcomes})
    append_ledger(root/"audit-ledger.jsonl", {"action":"publish","outcomes":outcomes})
    print(json.dumps(outcomes, indent=2))

def main():
    parser = argparse.ArgumentParser(prog="pets-aegis-hf")
    sub = parser.add_subparsers(dest="command", required=True)
    q = sub.add_parser("inventory"); q.add_argument("--owners", nargs="+", default=OWNERS); q.add_argument("--output", default="pets-aegis-evidence"); q.set_defaults(func=inventory)
    q = sub.add_parser("verify"); q.add_argument("--evidence", required=True); q.set_defaults(func=verify)
    q = sub.add_parser("audit"); q.add_argument("--evidence", required=True); q.set_defaults(func=audit)
    q = sub.add_parser("publish"); q.add_argument("--evidence", required=True); q.add_argument("--confirm-write", action="store_true"); q.set_defaults(func=publish)
    args = parser.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
