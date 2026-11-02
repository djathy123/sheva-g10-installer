#!/usr/bin/env python3
"""SHEVA Factory CLI v0.2: portable roadmap, tool checks, Skills, worker smoke and supervised inventory."""
import argparse, datetime as dt, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
HOME=Path.home()
TOOLCHAIN=HOME/"sheva-toolchain"
REPORTS=TOOLCHAIN/"reports"
REG=HERE/"skills/registry.json"
MISSIONS=("m13","figo","future")
CATEGORY={
 "G10-77 manifestes Mac/Linux": "PARTIAL - ARM64 only; Linux pending",
 "G10-78 bootstrap one-command": "PARTIAL - M4 real install PASS, cross-host clean install pending",
 "G10-79 sync encrypted and recovery": "HOLD - synthetic checkpoint only",
 "G10-80 workers Hatchet/LangGraph/ACP": "HOLD - no authenticated cross-host worker",
 "G10-81 dry-run / rollback": "PARTIAL - isolated smoke passed, app rollback pending",
 "G10-82 release/go-no-go": "PARTIAL - local archive and SHA256; no published release",
 "G10-S01 skill inventory": "PARTIAL - 3 pilot skills, 108 backlog",
 "G10-S02 skills registry": "PASS - pilot registry with SHA256",
 "G10-S03 mission M13/FIGO dynamic loading": "PASS - local install/verify/rollback tests",
 "G10-S04 complete 108 skills": "HOLD - not generated or evaluated",
 "G10-S05 multi-agent skill invocation": "HOLD - no authenticated Claude/Codex invocation",
 "G10-S06 distributed worker & observability": "HOLD - Langfuse/Backstage not deployed",
}
BINPATH=TOOLCHAIN/"node-lab/node_modules/.bin"
BINARY={
 "spec_kit":HOME/".local/bin/specify",
 "graphify":HOME/".local/bin/graphify",
 "semgrep":HOME/".local/bin/semgrep",
 "nx":BINPATH/"nx",
 "dependency_cruiser":BINPATH/"depcruise",
 "ast_grep":BINPATH/"ast-grep",
 "orval":BINPATH/"orval",
 "ts_rest":TOOLCHAIN/"node-lab/node_modules/@ts-rest/core",
 "msw":TOOLCHAIN/"node-lab/node_modules/msw",
 "pact":TOOLCHAIN/"node-lab/node_modules/@pact-foundation/pact",
 "playwright":TOOLCHAIN/"node-lab/node_modules/playwright-core",
 "openhands_canvas":BINPATH/"agent-canvas",
 "claude_code_cli":BINPATH/"claude",
 "codex_cli":BINPATH/"codex",
}
# Canonical SHEVA M21 architecture components (not counting Claude/Codex CLIs).
TOOLS_21=("spec_kit","structurizr","graphify","nx","dependency_cruiser","ast_grep",
          "langgraph","hatchet","openhands_agent_server","openhands_canvas",
          "orval","ts_rest","msw","pact","supabase_cli","pgtap_lab",
          "semgrep","playwright","act","langfuse_service","backstage_service")
AGENT_CLI=("claude_code_cli","codex_cli")
RUNTIME_SERVICES={"openhands_agent_server","openhands_canvas","pgtap_lab","langfuse_service","backstage_service"}
TOOL_NOTES={
 "hatchet":"SDK importable, worker Hatchet durable NON certifie",
 "openhands_canvas":"Canvas endpoint HTTP /ready",
 "openhands_agent_server":"Agent Server endpoint HTTP /ready",
 "pgtap_lab":"Labo PostgreSQL pgTAP non deploye",
 "langfuse_service":"Observabilite Langfuse non deployee",
 "backstage_service":"Catalogue Backstage non deploye",
}
def shell(args,timeout=6):
 try:
  r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
  return r.returncode==0,(r.stdout or r.stderr).strip()[:240]
 except (OSError,subprocess.TimeoutExpired) as exc:
  return False,type(exc).__name__
def health(port):
 try:
  with urllib.request.urlopen("http://127.0.0.1:%d/ready"%port,timeout=1.5) as f:return f.status==200
 except Exception:return False
def installed():
 result={name:p.exists() for name,p in BINARY.items()}
 legacy=HOME/"sheva-mission-stack"
 alternates={
  "nx":"module-architect/labs/nx-poc/node_modules/.bin/nx",
  "dependency_cruiser":"module-architect/labs/dependency-cruiser/node_modules/.bin/depcruise",
  "ast_grep":"quality/labs/ast-grep/node_modules/.bin/ast-grep",
  "orval":"algo/m21/orval-lab/node_modules/.bin/orval",
  "ts_rest":"algo/m21/ts-rest-lab/node_modules/@ts-rest/core",
  "msw":"algo/m21/orval-lab/node_modules/msw",
  "pact":"algo/m21/pact-lab/node_modules/@pact-foundation/pact",
  "playwright":"algo/m21/real-pg-lab/node_modules/playwright-core",
  "openhands_canvas":"agent-canvas/node_modules/.bin/agent-canvas",
 }
 for key,path in alternates.items():
  result[key]=result[key] or (legacy/path).exists()
 for key,binary in (("claude_code_cli","claude"),("codex_cli","codex")):
  result[key]=result[key] or shutil.which(binary) is not None
 py=TOOLCHAIN/".venv/bin/python"
 if not py.exists():py=legacy/".venv/bin/python"
 for name,mod in [("langgraph","langgraph"),("hatchet","hatchet_sdk")]:
  result[name]=py.exists() and shell([str(py),"-c","import "+mod],timeout=8)[0]
 for name,cmd in [("act","act"),("supabase_cli","supabase"),("structurizr","structurizr")]:
  result[name]=shutil.which(cmd) is not None
 result["act"]=result["act"] or (legacy/"quality/bin/act").exists()
 result["structurizr"]=result["structurizr"] or (legacy/"architecture/structurizr/cli/structurizr.sh").exists()
 result["openhands_agent_server"]=health(18000)
 result["pgtap_lab"]=False
 result["langfuse_service"]=False
 result["backstage_service"]=False
 return result
def skill_state(mission):
 if not REG.is_file():return {"registry":"MISSING","mission":mission,"selected":[]}
 try:
  j=json.loads(REG.read_text())
  mapping=j.get("mission_map",{})
  idx={x["slug"]:x for x in j["skills"]}
  selection=mapping.get(mission,[])
  rows=[]
  for slug in selection:
   item=idx[slug]
   src=HERE/"skills/catalog"/slug/"SKILL.md"
   verified=src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==item["sha256"]
   targets={}
   for agent in ("claude","codex"):
    path=HOME/("."+agent)/"skills"/slug/"SKILL.md"
    targets[agent]="PASS" if verified and path.is_file() and path.read_bytes()==src.read_bytes() else ("CONFLICT" if path.exists() else "MISSING")
   rows.append({"skill":slug,"source_verified":verified,"agents":targets})
  return {"registry":"PASS" if all(x["source_verified"] for x in rows) else "INVALID","mission":mission,"selected":rows}
 except Exception as e:return {"registry":"INVALID","reason":type(e).__name__,"mission":mission,"selected":[]}
def apply_report():
 fallback=None
 for name in ("last-apply.json","last-install.json"):
  p=REPORTS/name
  if p.is_file():
   try:
    a=json.loads(p.read_text())
    if a.get("mode")=="APPLY":
     steps=a.get("steps",[])
     candidate={"path":str(p),"profile":a.get("profile"),"stages":steps}
     if len(steps)>=8 and all(x.get("status")=="PASS" for x in steps):
      return candidate
     fallback=candidate
   except Exception:pass
 log=HOME/"sheva-g10-installer/m4-full-apply-20261102.log"
 if log.is_file():
  content=log.read_text(errors="replace")
  if "INSTALL_STAGES_PASS 10 / 10" in content and "SHEVA_G10_APPLY_EXIT=0" in content:
   return {"profile":"full","status":"PASS_LOG_VERIFIED","evidence":str(log),"stages":10}
 return fallback or {"status":"NONE"}
def overview(mission):
 items=installed()
 role="M4-worker" if platform.machine()=="arm64" and (os.cpu_count() or 0)>=8 and shutil.disk_usage(HOME).free>30*1024**3 else "controller-or-restricted"
 skills=skill_state(mission)
 apply=apply_report()
 roadmap=dict(CATEGORY)
 if apply.get("status")=="PASS_LOG_VERIFIED" or (apply.get("stages") and len(apply.get("stages",[]))>=8):
  roadmap["G10-78 bootstrap one-command"]="PARTIAL - install real completed on this host; full recovery test outstanding"
 else:
  roadmap["G10-78 bootstrap one-command"]="HOLD - no complete APPLY receipt on this host; PLAN/VERIFY not enough"
 if skills.get("registry")!="PASS":
  roadmap["G10-S02 skills registry"]="HOLD - missing or invalid registry"
 else:
  roadmap["G10-S02 skills registry"]="PASS - SHA256 registry verified"
 loaded=bool(skills.get("selected")) and all(
  r["source_verified"] and all(v=="PASS" for v in r["agents"].values())
  for r in skills["selected"])
 roadmap["G10-S03 mission M13/FIGO dynamic loading"]=(
  "PASS - selected mission skills loaded on this host" if loaded else
  "AVAILABLE - not loaded for selected mission; run skills install")
 return {"schema":"sheva.factory.roadmap.v0.2","host":platform.node(),"role_hint":role,"platform":platform.system()+"-"+platform.machine(),
  "date_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
  "free_gib":round(shutil.disk_usage(HOME).free/1024**3,2),
  "tools":items,"counts":{"installed_or_healthy":sum(bool(items.get(k)) for k in TOOLS_21),"total":len(TOOLS_21),
                            "agents_installed":sum(bool(items.get(k)) for k in AGENT_CLI)},
  "tool_registry":list(TOOLS_21),"agent_cli":{k:bool(items.get(k)) for k in AGENT_CLI},
  "services":{"docker_ready":shell(["docker","info","--format","{{.ServerVersion}}"],timeout=7)[0] if shutil.which("docker") else False,
              "canvas_ready":health(18180) or health(18080),"agent_server_ready":health(18000)},
  "skills":skills,"last_real_install":apply,"roadmap":roadmap,
  "constraints":["no secret transfer","M13 real_reset=false","no staging/prod mutations","no authenticated cross-host worker proven"]}
def safe_report(data,name):
 REPORTS.mkdir(parents=True,exist_ok=True)
 p=REPORTS/name
 p.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
 return p
def print_roadmap(d):
 print("SHEVA AI FACTORY CLI v0.3.0 |",d["host"],"|",d["role_hint"],"| mission",d["skills"]["mission"].upper())
 print("SHEVA 21 TOOLS: %s/%s present or healthy (not all integrations certified), disk free %.2f GiB"%(d["counts"]["installed_or_healthy"],d["counts"]["total"],d["free_gib"]))
 print("AGENT CLI EXTRAS: Claude Code=%s Codex=%s"%(d["agent_cli"]["claude_code_cli"],d["agent_cli"]["codex_cli"]))
 print("SERVICES:",json.dumps(d["services"],sort_keys=True))
 print("LAST APPLY:",d["last_real_install"].get("profile",d["last_real_install"].get("status","NONE")))
 print("\nG10 ROADMAP:")
 for stage,status in d["roadmap"].items():print("  %-43s %s"%(stage,status))
 print("\nTOOLS: ")
 for name,ok in d["tools"].items():print("  %-27s %s"%(name,"PRESENT/HEALTHY" if ok else "MISSING/NOT_READY"))
 print("\nMISSION SKILLS (%s):"%d["skills"]["registry"])
 for row in d["skills"]["selected"]:print("  %-27s Claude:%s Codex:%s"%(row["skill"],row["agents"]["claude"],row["agents"]["codex"]))
 print("\nNEXT: sheva-factory install --profile full --mission %s --apply"%d["skills"]["mission"])
 print("NOTE: CLI installation evidence is NOT proof of agent auth, multi-machine workers or approval for M13.")
def smoke():
 py=TOOLCHAIN/".venv/bin/python"
 if not py.exists():py=HOME/"sheva-mission-stack/.venv/bin/python"
 if not py.exists():raise SystemExit("HOLD: Python environment missing")
 program="""from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.sqlite import SqliteSaver
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import TypedDict
class State(TypedDict): value:int
g=StateGraph(State);g.add_node('inc',lambda s:{'value':s['value']+1});g.add_edge(START,'inc');g.add_edge('inc',END)
with TemporaryDirectory(prefix='sheva-worker-smoke-') as temp:
 with SqliteSaver.from_conn_string(str(Path(temp)/'cp.sqlite')) as cp:
  app=g.compile(checkpointer=cp);cfg={'configurable':{'thread_id':'synthetic-only'}}
  assert app.invoke({'value':41},cfg)['value']==42
  assert app.get_state(cfg).values['value']==42
print('SYNTHETIC_WORKER_CHECKPOINT_PASS')
"""
 passed,detail=shell([str(py),"-c",program],timeout=25)
 out={"time_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"worker_smoke":"PASS" if passed else "FAIL","proof":detail,
      "kind":"synthetic-only","distributed_hatchet_worker_connected":False}
 report=safe_report(out,"worker-smoke.json")
 print("WORKER:",out["worker_smoke"],detail,"REPORT:",report)
 if not passed:raise SystemExit(6)
def main():
 p=argparse.ArgumentParser(prog="sheva-factory",description="G10 machine-local CLI without conversation dependency")
 p.add_argument("command",choices=["status","roadmap","tools","doctor","install","skills","worker","supervise","reports"])
 p.add_argument("action",nargs="?",default=None)
 p.add_argument("--mission",choices=MISSIONS,default="m13")
 p.add_argument("--profile",choices=["controller","worker","full","gpu"],default="full")
 p.add_argument("--agents",choices=["both","claude","codex"],default="both")
 p.add_argument("--apply",action="store_true",help="perform actual installation")
 p.add_argument("--json",action="store_true")
 p.add_argument("--watch",action="store_true",help="refresh local supervision until interrupted")
 p.add_argument("--interval",type=int,default=15,help="watch interval seconds")
 p.add_argument("--count",type=int,default=0,help="max watch updates (0 unlimited)")
 a=p.parse_args()
 if a.command=="skills":
  action=a.action or "plan"
  if action not in ("list","plan","install","verify","rollback"):p.error("skills: list|plan|install|verify|rollback")
  r=subprocess.run([sys.executable,str(HERE/"sheva-skills.py"),action,"--mission",a.mission,"--agents",a.agents],check=False)
  raise SystemExit(r.returncode)
 if a.command=="install":
  args=[sys.executable,str(HERE/"sheva-install.py"),"--profile",a.profile,"--mission",a.mission]
  if a.apply:args+=["--apply"]
  r=subprocess.run(args,check=False)
  raise SystemExit(r.returncode)
 if a.command=="worker" and a.action=="smoke":smoke();return
 if a.command=="worker" and a.action not in ("status",None,"smoke"):p.error("worker: status|smoke")
 if a.command=="reports":
  print("REPORT DIRECTORY:",REPORTS)
  for name in ("last-apply.json","last-verify.json","last-install.json","worker-smoke.json","supervision.json","roadmap.json"):
   path=REPORTS/name
   print(name,"PRESENT" if path.exists() else "MISSING")
  return
 d=overview(a.mission)
 if a.command=="tools":
  print("SHEVA ARCHITECTURE — 21 COMPONENTS",d["host"])
  print("VERIFIED PRESENT / HEALTHY:",d["counts"]["installed_or_healthy"],"/21")
  for idx,name in enumerate(TOOLS_21,1):
   present=d["tools"].get(name,False)
   status=("READY_HTTP_200" if name in {"openhands_agent_server","openhands_canvas"} and present
           else ("PRESENT_ONLY" if present else "NOT_READY"))
   print(f"{idx:02d}. {name:27} {status} {TOOL_NOTES.get(name,'')}")
  print("EXTRA AGENT CLIS",d["agent_cli"])
  print("REPORT",safe_report(d,"tools-21.json"))
 elif a.command=="supervise":
  if a.action not in ("once",None):p.error("supervise: once")
  if a.watch:
   if not 2<=a.interval<=3600 or a.count<0:p.error("invalid watch interval/count")
   i=0
   while True:
    d=overview(a.mission)
    path=safe_report(d,"supervision.json")
    print("SUPERVISION",d["date_utc"],d["counts"],d["services"],"record",path,flush=True)
    i+=1
    if a.count and i>=a.count:break
    time.sleep(a.interval)
  else:
   path=safe_report(d,"supervision.json")
   print("SHEVA SUPERVISION PASS (one snapshot, not a running daemon) ->",path)
 elif a.command in ("doctor","worker"):
  path=safe_report(d,"doctor.json")
  print("SHEVA HEALTH INVENTORY",d["host"],"REPORT:",path)
  print("Services:",d["services"],"registered_remote_workers=NOT_CONFIGURED")
 else:
  path=safe_report(d,"roadmap.json")
  if a.json: print(json.dumps(d,indent=2,ensure_ascii=False))
  else:print_roadmap(d)
  print("\nLOCAL EVIDENCE:",path)
if __name__=="__main__":main()
