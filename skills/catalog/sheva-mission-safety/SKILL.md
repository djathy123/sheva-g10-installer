---
name: sheva-mission-safety
description: Apply SHEVA AI Factory scope, isolation, approval and evidence gates before any M13, FIGO, or future coding mission.
---
# SHEVA mission-safety (pilot v0.1)

Before tool use, record mission ID, project ID, source repo HEAD, branch, worktree, allowed operations, resource budget, and synthetic vs real datasets. Treat every external workspace as untrusted until verified.

- No real RESET, staging/production write, migration, git push/merge, secret export or credential login without a fresh explicit operator approval for that exact action.
- A passed CLI check is not proof that an actual multi-agent workflow or remote worker works.
- Keep projects separate: separate worktrees, namespaces, database credentials, logs and rollback/checkpoint stores.
- Agent delegates only to installed and tested tools. Missing dependency => HOLD with evidence, never fictional PASS.
- Use synthetic fixtures on hardware owned by a third party; don't store private repositories, business records, authentication or cloud credentials there.
- Report each operation's actual exit code, validation assertions, tool versions, SHA256 evidence, elapsed time, and GO/HOLD/NO-GO.
- This Skill provides guidance and does not grant permissions or invoke tools itself.
