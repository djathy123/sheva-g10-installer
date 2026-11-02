#!/usr/bin/env python3
"""SHEVA G10 portable installer v0.1. Non-destructive, no account login or secret transfer."""
import argparse, datetime, hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path

VERSION = "0.2.2"
ROOT = Path.home() / "sheva-toolchain"
PACKAGES_PY = ["langgraph==1.1.10", "langgraph-checkpoint-sqlite==3.1.3", "hatchet-sdk==1.44.0"]
PACKAGES_NODE = ["@openhands/agent-canvas@1.34.0", "nx@24.0.3", "dependency-cruiser@18.7.0",
                 "@ast-grep/cli@0.51.0", "orval@8.46.0", "@ts-rest/core@3.52.1",
                 "msw@3.0.3", "@pact-foundation/pact@17.1.4", "playwright-core@1.64.1",
                 "@anthropic-ai/claude-code@2.1.72", "@openai/codex@0.155.0"]
PACKAGES_TOOLS = ["graphifyy==0.9.56", "specify-cli==1.2.5", "semgrep==1.183.0"]
PROFILES = {
    "controller": ["prereqs", "python", "py-tools", "node","cli"],
    "worker": ["prereqs", "python", "py-tools", "node", "orchestration", "node-lab", "act", "supabase","cli"],
    "full": ["prereqs", "python", "py-tools", "node", "orchestration", "node-lab", "act", "supabase", "structurizr","cli"],
    "gpu": ["prereqs", "python", "py-tools", "node", "orchestration", "node-lab", "act", "supabase", "ollama","cli"],
}
COMPONENTS = {
    "spec_kit": "uv tool: specify-cli", "graphify": "uv tool: graphifyy",
    "semgrep": "uv tool: semgrep", "nx": "npm isolated", "dependency_cruiser": "npm isolated",
    "ast_grep": "npm isolated", "orval": "npm isolated", "ts_rest": "npm isolated",
    "msw": "npm isolated", "pact": "npm isolated", "playwright": "npm isolated",
    "langgraph": "Python venv", "hatchet": "Python SDK; worker service still needs provisioning",
    "openhands_canvas": "npm isolated; sandbox must be configured", "openhands_agent_server": "Canvas backend runtime; startup not automatic",
    "act": "Homebrew CLI", "supabase_cli": "Homebrew CLI; requires separate login",
    "structurizr": "Homebrew CLI (full profile)",
    "pgtap_lab": "separate isolated Docker lab REQUIRED",
    "langfuse_service": "separate Docker Compose deployment REQUIRED",
    "backstage_service": "separate scaffold/deployment REQUIRED"
}
def have(cmd): return shutil.which(cmd) is not None
def call(args, *, cwd=None, timeout=1800):
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=cwd, timeout=timeout, check=False)
    if result.returncode: raise RuntimeError("exit " + str(result.returncode) + ": " + " ".join(args))
def version(cmd):
    if not have(cmd): return "MISSING"
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=6)
        return (r.stdout or r.stderr).strip().splitlines()[0][:80]
    except Exception: return "CHECK_FAILED"
def brew(package, cask=False):
    if not have("brew"): raise RuntimeError("Homebrew missing: https://brew.sh")
    check = ["brew", "list", "--cask" if cask else "--formula", package]
    if subprocess.run(check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        call(["brew", "install"] + (["--cask"] if cask else []) + [package])
    else:
        print("SKIP installed brew:", package)
def node_major():
    try: return int(version("node").lstrip("v").split(".")[0])
    except Exception: return 0
def inventory():
    free = shutil.disk_usage(Path.home()).free / (1024**3)
    mem = None
    if platform.system() == "Darwin":
        mem = round(int(subprocess.check_output(["sysctl","-n","hw.memsize"])) / 1024**3, 1)
    return {"host": platform.node(), "platform": platform.system()+"-"+platform.machine(),
            "macos": platform.mac_ver()[0], "ram_gib": mem, "disk_free_gib": round(free, 2),
            "node": version("node"), "uv": version("uv"), "git": version("git"),
            "docker_cli": version("docker"), "python": version("python3")}
def verify():
    found = {}
    checks = {
        "spec_kit": ["specify"], "graphify": ["graphify"], "semgrep": ["semgrep"],
        "act": ["act"], "supabase_cli": ["supabase"], "structurizr": ["structurizr"]
    }
    for key, cmds in checks.items():
        found[key] = any(have(x) or (Path.home()/".local"/"bin"/x).is_file() for x in cmds)
    labs = ROOT / "node-lab" / "node_modules"
    nodes = {"nx": "nx", "dependency_cruiser": "depcruise", "ast_grep": "ast-grep", "orval": "orval",
             "playwright": "playwright-core", "msw": "msw", "ts_rest": "@ts-rest/core",
             "pact": "@pact-foundation/pact", "openhands_canvas": "@openhands/agent-canvas"}
    nodes.update(claude_code_cli="claude", codex_cli="codex")
    for key, pkg in nodes.items():
        found[key] = (labs/pkg).exists() if pkg.startswith("@") or key in ("playwright", "msw") else (labs/".bin"/pkg).exists()
    py = ROOT / ".venv" / "bin" / "python"
    if py.exists():
        for key, mod in [("langgraph", "langgraph"), ("hatchet", "hatchet_sdk")]:
            try:
                found[key] = subprocess.run([str(py), "-c", "import "+mod], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=6).returncode == 0
            except Exception: found[key] = False
    else: found.update(langgraph=False, hatchet=False)
    for key in ["openhands_agent_server", "pgtap_lab", "langfuse_service", "backstage_service"]:
        found[key] = False  # never equate installed package with running/healthy service
    return found
def install_step(step):
    if step == "prereqs":
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise RuntimeError("Only macOS ARM64 qualified; Linux requires a separately tested lockfile")
        if not have("brew"): raise RuntimeError("Homebrew must be installed separately by owner")
        brew("git")
        if not have("uv"): brew("uv")
        if node_major() < 24: brew("node")
    elif step == "python":
        call(["uv", "python", "install", "3.12"])
    elif step == "py-tools":
        for pkg in PACKAGES_TOOLS: call(["uv","tool","install","--python","3.12",pkg])
    elif step == "node":
        if node_major() < 24: raise RuntimeError("Node >= 24 required")
    elif step == "orchestration":
        ROOT.mkdir(parents=True, exist_ok=True)
        if not (ROOT/".venv"/"bin"/"python").exists():
            call(["uv","venv","--python","3.12",str(ROOT/".venv")])
        call(["uv","pip","install","--python",str(ROOT/".venv"/"bin"/"python"),*PACKAGES_PY])
    elif step == "node-lab":
        d = ROOT/"node-lab"
        d.mkdir(parents=True, exist_ok=True)
        manifest = d/"package.json"
        if not manifest.exists(): manifest.write_text(json.dumps({"name":"sheva-g10-node-lab","private":True,"version":"0.1.0"})+"\n")
        call(["npm","install","--prefix",str(d),"--save-exact","--no-audit","--no-fund",*PACKAGES_NODE])
    elif step == "act": brew("act")
    elif step == "supabase":
        if not have("supabase"): call(["brew","install","supabase/tap/supabase"])
    elif step == "structurizr": brew("structurizr")
    elif step == "cli":
        path=Path.home()/".local/bin/sheva-factory"
        src=Path(__file__).with_name("sheva-factory").resolve()
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.is_symlink() and path.resolve()==src:
            print("SKIP CLI symlink already configured")
        elif path.exists() or path.is_symlink():
            raise RuntimeError("CLI_SYMLINK_CONFLICT: "+str(path))
        else:
            path.symlink_to(src)
        rc=Path.home()/".zshrc"
        entry='export PATH="$HOME/.local/bin:$PATH"'
        existing=rc.read_text() if rc.exists() else ""
        if entry not in existing:
            with rc.open("a") as f:
                f.write("\n# SHEVA G10 tools and CLI\n"+entry+"\n")
            print("ZSH_PATH_CONFIGURED: restart terminal or source ~/.zshrc")
    elif step == "ollama": brew("ollama")
    else: raise RuntimeError("unknown step: "+step)
def report(profile, mode, outcomes):
    data = {"schema":"sheva.g10.install-report.v1", "version": VERSION, "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "profile":profile,"mode":mode,"machine":inventory(),"steps":outcomes,"components":verify(),
            "not_auto_provisioned":["openhands_agent_server","pgtap_lab","langfuse_service","backstage_service"],
            "safety":{"copies_secrets":False,"requires_cloud_login":False,"staging_write":False,"production_write":False,"real_reset":False}}
    if mode != "PLAN":
        directory=ROOT/"reports";directory.mkdir(parents=True,exist_ok=True)
        path=directory/("last-apply.json" if mode=="APPLY" else "last-verify.json")
        path.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        if mode=="APPLY":
            with (directory/"install-history.jsonl").open("a") as history:
                history.write(json.dumps({"time_utc":data["time_utc"],"profile":profile,"stages":outcomes,"mode":mode})+"\n")
        print("REPORT",str(path),"SHA256",hashlib.sha256(path.read_bytes()).hexdigest())
    return data
def main():
    p=argparse.ArgumentParser(description="SHEVA AI Factory one-command bootstrap (macOS arm64)")
    p.add_argument("--profile", choices=sorted(PROFILES), default="worker")
    actions=p.add_mutually_exclusive_group()
    actions.add_argument("--apply",action="store_true",help="actually install toolchain")
    actions.add_argument("--verify",action="store_true",help="local health/inventory only")
    p.add_argument("--mission",choices=["m13","figo","future"],help="install only Skills for selected mission after toolchain stages")
    p.add_argument("--only",choices=list(set(sum(PROFILES.values(),[]))),help="install a single stage")
    args=p.parse_args()
    inv=inventory(); plan=[args.only] if args.only else PROFILES[args.profile]
    mode="APPLY" if args.apply else ("VERIFY" if args.verify else "PLAN")
    print("SHEVA_G10",VERSION, mode, args.profile, json.dumps(inv,sort_keys=True))
    print("STAGES",json.dumps(plan))
    if not args.apply:
        report(args.profile,mode,[])
        print("NO_CHANGES_PERFORMED")
        return
    if inv["platform"]!="Darwin-arm64": raise SystemExit("NO_GO: only darwin-arm64 is qualified")
    minimum=10 if args.profile=="controller" else 25
    if inv["disk_free_gib"] < minimum: raise SystemExit("NO_GO: requires "+str(minimum)+" GiB free, no install")
    if args.profile=="full" and (inv["ram_gib"] or 0)<12: raise SystemExit("NO_GO: full profile requires 12 GiB RAM")
    outcomes=[]
    for stage in plan:
        try:
            install_step(stage); outcomes.append({"stage":stage,"status":"PASS"})
            report(args.profile,mode,outcomes)
        except Exception as exc:
            outcomes.append({"stage":stage,"status":"FAIL","reason":str(exc)[:250]})
            report(args.profile,mode,outcomes)
            raise SystemExit("NO_GO at stage "+stage+": "+str(exc))
    if args.mission:
        try:
            call([sys.executable,str(Path(__file__).with_name("sheva-skills.py")),"install","--mission",args.mission],timeout=30)
            outcomes.append({"stage":"skills:"+args.mission,"status":"PASS"})
        except Exception as exc:
            outcomes.append({"stage":"skills:"+args.mission,"status":"FAIL","reason":str(exc)[:250]})
            report(args.profile,mode,outcomes)
            raise SystemExit("NO_GO at mission skills "+args.mission+": "+str(exc))
    r=report(args.profile,mode,outcomes)
    print("INSTALL_STAGES_PASS",len(outcomes),"/",len(plan)+(1 if args.mission else 0))
    print("IMPORTANT: installed components != healthy running services, auth, or full architecture integration")
    print("SECURITY: no credentials copied; no permissions changed for other user accounts")
if __name__=="__main__":main()
