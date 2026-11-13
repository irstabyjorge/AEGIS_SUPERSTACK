#!/usr/bin/env python3
"""Create a provenance-only snapshot of a Git repository; never copies source contents."""
import argparse, datetime as dt, hashlib, json, os, subprocess, sys
from pathlib import Path

MAX_FILES, MAX_COMMITS, CHUNK = 25000, 500, 65536

def git(*args, check=True):
    p=subprocess.run(["git",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace").strip())
    return p.stdout

def inventory(head):
    raw=git("ls-tree","-r","-l","-z",head)
    entries=[]
    for rec in raw.split(b"\0"):
        if not rec: continue
        meta,path=rec.split(b"\t",1)
        mode,kind,oid,size=meta.decode("ascii").split(" ",3)
        if kind=="blob":
            entries.append((path.decode("utf-8","surrogateescape"),mode,oid,int(size) if size.isdigit() else 0))
    total=len(entries); selected=entries[:MAX_FILES]
    if not selected: return [],total,False
    p=subprocess.Popen(["git","cat-file","--batch"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p.stdin.write(b"".join(x[2].encode()+b"\n" for x in selected)); p.stdin.close()
    rows=[]
    for path,mode,oid,size in selected:
        header=p.stdout.readline().split()
        if len(header)!=3 or header[1]!=b"blob" or header[0].decode()!=oid:
            p.kill(); raise RuntimeError("Invalid git object stream")
        remaining=int(header[2]); h=hashlib.sha256()
        while remaining:
            block=p.stdout.read(min(CHUNK,remaining))
            if not block: p.kill(); raise RuntimeError("Truncated git object")
            h.update(block); remaining-=len(block)
        if p.stdout.read(1)!=b"\n": p.kill(); raise RuntimeError("Invalid git object boundary")
        rows.append({"path":path,"mode":mode,"git_blob_oid":oid,"bytes":size,"sha256":h.hexdigest()})
    if p.wait()!=0: raise RuntimeError("git cat-file failed")
    return rows,total,total>len(selected)

def history(head):
    total=int(git("rev-list","--count",head).decode().strip() or "0")
    raw=git("log",f"-n{MAX_COMMITS}","--format=%H%x09%an%x09%ae%x09%aI%x09%s",head)
    rows=[]
    for line in raw.decode("utf-8","replace").splitlines():
        parts=line.split("\t",4)
        if len(parts)!=5: continue
        sha,name,email,date,subject=parts
        rows.append({"sha":sha,"author_name_declared":name,
          "author_email_sha256":hashlib.sha256(email.lower().encode()).hexdigest(),
          "authored_at_declared":date,"subject":subject})
    return rows,total,total>len(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",default=".ip-shield/report.json")
    out=Path(ap.parse_args().output)
    try:
        head=git("rev-parse","HEAD").decode().strip()
        tree=git("rev-parse",head+"^{tree}").decode().strip()
        files,nfiles,files_cut=inventory(head)
        commits,ncommits,commits_cut=history(head)
        doc={
          "manifest_type":"AEGIS_GITHUB_IP_SHIELD_PROVENANCE","manifest_version":"1.0",
          "generated_at_utc_runner_clock":dt.datetime.now(dt.timezone.utc).isoformat(),
          "repository":os.getenv("GITHUB_REPOSITORY"),"source_ref":os.getenv("GITHUB_REF"),
          "source_ref_name":os.getenv("GITHUB_REF_NAME"),"source_commit":head,"source_tree":tree,
          "workflow_run_id":os.getenv("GITHUB_RUN_ID"),
          "inventory":{"tracked_blob_count_total":nfiles,"tracked_blob_count_recorded":len(files),
                       "truncated":files_cut,"files":files},
          "history":{"commit_count_total":ncommits,"commit_count_recorded":len(commits),
                     "truncated":commits_cut,"commits":commits},
          "limits":[
            "Git author names and timestamps are self-declared commit metadata, not verified identity or trusted time.",
            "SHA-256 fingerprints identify snapshot bytes; they do not prove authorship, originality, ownership or infringement.",
            "No source-file contents are included; commit email addresses are hashed.",
            "A ledger branch is versioned evidence, not immutable storage; administrators can rewrite it.",
            "Only this configured repository and triggering refs are covered; this does not monitor every account repository."
          ]}
        out.parent.mkdir(parents=True,exist_ok=True)
        data=(json.dumps(doc,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
        out.write_bytes(data)
        out.with_suffix(out.suffix+".sha256").write_text(hashlib.sha256(data).hexdigest()+"  "+out.name+"\n")
        print(f"Recorded {len(files)} file fingerprints for {head}; report={out}")
        return 0
    except Exception as e:
        print(f"IP SHIELD ERROR: {e}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
