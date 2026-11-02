#!/usr/bin/env python3
"""SHEVA Skills mission-scoped installer v0.3: provenance-aware, safe rollback."""
import argparse, hashlib, json, os, shutil, sys, tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parent
CATALOG=BASE/"skills"/"catalog"
REG=BASE/"skills"/"registry.json"
MANAGED=Path.home()/".sheva"/"skills"
STATE=MANAGED/"state.json"
AGENTS={"claude":Path.home()/".claude"/"skills","codex":Path.home()/".codex"/"skills"}
SCHEMA="sheva.skills.state.v2"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def registry():
    data=json.loads(REG.read_text())
    if data.get("schema")!="sheva.skills.registry.v1":raise RuntimeError("BAD_REGISTRY_SCHEMA")
    mapping=data.get("mission_map")
    entries={e["slug"]:e for e in data["skills"]}
    if not isinstance(mapping,dict) or not mapping:raise RuntimeError("BAD_MISSION_MAP")
    for name,slugs in mapping.items():
        if not name.isascii() or not name.replace("-","").isalnum():raise RuntimeError("UNSAFE_MISSION_ID")
        if not isinstance(slugs,list) or not slugs:raise RuntimeError("EMPTY_MISSION")
        for slug in slugs:
            if slug not in entries or not slug.isascii() or not slug.replace("-","").isalnum():
                raise RuntimeError("UNSAFE_SKILL_ID")
            f=CATALOG/slug/"SKILL.md"
            if not f.is_file() or f.is_symlink() or sha(f)!=entries[slug]["sha256"]:
                raise RuntimeError("SKILL_MANIFEST_MISMATCH:"+slug)
            if f.stat().st_size>12000:raise RuntimeError("SKILL_TOO_LARGE")
            content=f.read_text()
            if not content.startswith("---\n") or "\nname: "+slug+"\n" not in content:
                raise RuntimeError("BAD_SKILL_METADATA")
    return data,mapping

def read_state():
    if not STATE.exists():
        return {"schema":SCHEMA,"active_missions":{},"created_files":{}}
    if STATE.is_symlink():raise RuntimeError("STATE_IS_SYMLINK")
    data=json.loads(STATE.read_text())
    if data.get("schema")!=SCHEMA:raise RuntimeError("UNKNOWN_STATE_SCHEMA")
    if not isinstance(data.get("active_missions"),dict) or not isinstance(data.get("created_files"),dict):
        raise RuntimeError("INVALID_STATE_DATA")
    return data

def save_state(st):
    MANAGED.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w",dir=MANAGED,prefix=".state-",delete=False) as f:
        path=Path(f.name)
        os.chmod(path,0o600)
        json.dump(st,f,sort_keys=True,indent=2)
        f.write("\n")
    os.replace(path,STATE)

def location(agent,slug):
    return AGENTS[agent]/slug/"SKILL.md"

def local_status(agent,slug):
    dest=location(agent,slug)
    if dest.parent.is_symlink() or dest.is_symlink():return "CONFLICT"
    if dest.is_file():
        return "PASS" if sha(dest)==sha(CATALOG/slug/"SKILL.md") else "CONFLICT"
    if dest.exists() or dest.parent.exists():return "CONFLICT"
    return "MISSING"

def main():
    p=argparse.ArgumentParser(prog="sheva-skills")
    p.add_argument("action",choices=["list","plan","install","verify","rollback"])
    p.add_argument("--mission",default="m13")
    p.add_argument("--agents",choices=["claude","codex","both"],default="both")
    args=p.parse_args()
    reg,mapping=registry()
    if args.mission not in mapping:p.error("Unknown mission")
    agents=["claude","codex"] if args.agents=="both" else [args.agents]
    selected=mapping[args.mission]
    st=read_state()
    result={"schema":"sheva.skills.action.v2","action":args.action,
            "mission":args.mission,"selected":selected,"agents":agents,"results":[],
            "secret_transfer":False,"user_files_overwritten":False}
    all_rows=[(agent,slug) for agent in agents for slug in selected]
    if args.action in ("list","plan","verify"):
        for agent,slug in all_rows:
            result["results"].append({"agent":agent,"skill":slug,"status":local_status(agent,slug)})
        print(json.dumps(result,indent=2))
        if args.action=="verify" and any(x["status"]!="PASS" for x in result["results"]):
            raise SystemExit(3)
        return
    if args.action=="install":
        problems=[(a,slug,local_status(a,slug)) for a,slug in all_rows if local_status(a,slug)=="CONFLICT"]
        if problems:
            print(json.dumps({"error":"CONFLICT_NO_OVERWRITE","details":problems}))
            raise SystemExit(4)
        created=[]
        try:
            for agent,slug in all_rows:
                dest=location(agent,slug)
                old=local_status(agent,slug)
                if old=="MISSING":
                    dest.parent.mkdir(parents=True,exist_ok=False)
                    shutil.copy2(CATALOG/slug/"SKILL.md",dest)
                    created.append((agent,slug))
                    st["created_files"][agent+"/"+slug]=sha(dest)
                result["results"].append({"agent":agent,"skill":slug,
                                          "status":local_status(agent,slug),
                                          "ownership":"created" if (agent+"/"+slug) in st["created_files"] else "preexisting"})
            current=set(st["active_missions"].get(args.mission,[]))
            st["active_missions"][args.mission]=sorted(current|set(agents))
            save_state(st)
        except Exception:
            for agent,slug in reversed(created):
                dest=location(agent,slug)
                if dest.is_file() and sha(dest)==sha(CATALOG/slug/"SKILL.md"):
                    dest.unlink()
                    if not list(dest.parent.iterdir()):dest.parent.rmdir()
            raise
    else: # rollback
        current=set(st["active_missions"].get(args.mission,[]))
        remaining=current-set(agents)
        if remaining:st["active_missions"][args.mission]=sorted(remaining)
        else:st["active_missions"].pop(args.mission,None)
        for agent,slug in all_rows:
            dest=location(agent,slug)
            key=agent+"/"+slug
            status=local_status(agent,slug)
            in_use=any(agent in active and slug in mapping.get(mission,[])
                       for mission,active in st["active_missions"].items())
            if in_use:
                outcome="SHARED_SKILL_RETAINED"
            elif key not in st["created_files"]:
                outcome="UNMANAGED_LEFT_UNTOUCHED"
            elif status!="PASS" or st["created_files"][key]!=sha(dest):
                outcome="CONFLICT_LEFT_UNTOUCHED"
            else:
                dest.unlink()
                if not list(dest.parent.iterdir()):dest.parent.rmdir()
                del st["created_files"][key]
                outcome="ROLLED_BACK"
            result["results"].append({"agent":agent,"skill":slug,"status":outcome})
        save_state(st)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
