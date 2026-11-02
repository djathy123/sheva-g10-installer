#!/usr/bin/env python3
"""SHEVA Skills: lazy mission installer with source hashes and safe rollback.
No secret scanning claims; only allowlisted original files in this signed-in bundle.
"""
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CATALOG = BASE / "skills" / "catalog"
REG = BASE / "skills" / "registry.json"
MANAGED = Path.home() / ".sheva" / "skills"
MISSION_MAP = {"m13":["sheva-mission-safety","sheva-m13-audit"],
               "figo":["sheva-mission-safety","sheva-figo-isolation"],
               "future":["sheva-mission-safety"]}
AGENTS = {"claude":Path.home()/".claude"/"skills",
          "codex":Path.home()/".codex"/"skills"}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_reg():
    r=json.loads(REG.read_text(encoding="utf-8"))
    assert r["schema"]=="sheva.skills.registry.v1"
    seen=set()
    for x in r["skills"]:
        slug=x["slug"]
        assert slug not in seen and slug in {x for vs in MISSION_MAP.values() for x in vs}
        assert slug.isascii() and slug.replace("-","").isalnum()
        p=CATALOG/slug/"SKILL.md"
        assert p.is_file(),str(p)
        assert digest(p)==x["sha256"], "Skill modified: "+slug
        assert p.stat().st_size<12000
        content=p.read_text(encoding="utf-8")
        assert content.startswith("---\n") and "\nname: "+slug+"\n" in content
        seen.add(slug)
    return r
def selection(reg, mission):
    entries={x["slug"]:x for x in reg["skills"]}
    return [entries[x] for x in MISSION_MAP[mission]]
def dest_for(agent,slug):
    return AGENTS[agent]/slug/"SKILL.md"
def state(slug,agent):
    src=CATALOG/slug/"SKILL.md"
    dst=dest_for(agent,slug)
    if dst.is_file():return "PASS" if digest(dst)==digest(src) else "CONFLICT"
    if dst.exists() or dst.parent.is_symlink():return "CONFLICT"
    return "MISSING"
def print_json(d):print(json.dumps(d,indent=2,ensure_ascii=False,sort_keys=True))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["list","plan","install","verify","rollback"])
    p.add_argument("--mission",choices=sorted(MISSION_MAP),default="m13")
    p.add_argument("--agents",choices=["claude","codex","both"],default="both")
    args=p.parse_args()
    reg=read_reg(); skills=selection(reg,args.mission)
    names=["claude","codex"] if args.agents=="both" else [args.agents]
    summary={"schema":"sheva.skills.action.v1","action":args.action,"mission":args.mission,
             "selected":[x["slug"] for x in skills], "agents":names,
             "results":[],"forbidden":{"secret_transfer":True,"overwrite_existing":True,"project_data_transfer":True}}
    if args.action in ("list","plan","verify"):
        for e in skills:
            for a in names:summary["results"].append({"skill":e["slug"],"agent":a,"status":state(e["slug"],a)})
        print_json(summary)
        if args.action=="verify" and any(v["status"]!="PASS" for v in summary["results"]):raise SystemExit(3)
        return
    if args.action=="install":
        pre=[(x["slug"],a,state(x["slug"],a)) for x in skills for a in names]
        if any(s=="CONFLICT" for _,_,s in pre):
            print_json({"error":"CONFLICT; refusing to overwrite","details":pre});raise SystemExit(4)
        for slug,a,old in pre:
            dst=dest_for(a,slug)
            if old=="MISSING":
                dst.parent.mkdir(parents=True,exist_ok=False)
                shutil.copy2(CATALOG/slug/"SKILL.md",dst)
            summary["results"].append({"skill":slug,"agent":a,"status":state(slug,a)})
    elif args.action=="rollback":
        for e in skills:
            slug=e["slug"]
            for a in names:
                dst=dest_for(a,slug)
                status=state(slug,a)
                if status=="PASS":
                    dst.unlink()
                    if not list(dst.parent.iterdir()):dst.parent.rmdir()
                    summary["results"].append({"skill":slug,"agent":a,"status":"ROLLED_BACK"})
                elif status=="MISSING":
                    summary["results"].append({"skill":slug,"agent":a,"status":"ALREADY_ABSENT"})
                else:
                    summary["results"].append({"skill":slug,"agent":a,"status":"CONFLICT_LEFT_UNTOUCHED"})
    print_json(summary)
if __name__=="__main__":main()
