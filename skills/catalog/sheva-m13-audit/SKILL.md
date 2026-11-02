---
name: sheva-m13-audit
description: Plan and audit SHEVA OS M13 RESET V2 in a non-destructive worktree, collecting evidence without triggering staging, production or REAL_RESET.
---
# SHEVA M13 audit (pilot v0.1)

Load `sheva-mission-safety` first. Use the verified M13 worktree or an operator-authorized clone. Identify current HEAD and status without changing the source tree.

Workflow:
1. Locate M13 requirements and gates; separate facts from assumptions.
2. Run local static project inventory (Graphify, dependency-cruiser, Semgrep) only after verifying their availability and path scopes.
3. Use Spec Kit to create/test an acyclic task DAG; LangGraph decides allowed next step, Hatchet retries/checkpoints execution, OpenHands ACP delegates only within a sandbox.
4. Capture synthetic local tests first: checksums, exit codes, negative tests, and a simulated interruption/recovery.
5. Classify each result PASS, HOLD or FAIL. A CLI installed does not mean ACP authorization; local pass does not imply staging/production pass.

Hard gate: `REAL_RESET=false`. No real reset, staging/production mutations, external DB operations, git push, merges or release without separate explicit approval and a documented rollback. Do not place protected source or credentials on a friend's M4 machine.
Output: `reports/m13/<date>/` manifest, task DAG, SHA256, checkpoint IDs, blockers, independent review and GO/NO-GO.
