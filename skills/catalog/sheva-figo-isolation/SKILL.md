---
name: sheva-figo-isolation
description: Design and validate FIGO Logistics as an isolated application that may reuse SHEVA OS architecture without sharing user accounts, operational data or secrets.
---
# SHEVA FIGO architecture isolation (pilot v0.1)

Load `sheva-mission-safety` first. Do not confuse FIGO with SHEVA OS or merge their production databases, sessions, employees or tenancy.

Workflow:
1. Read the actual FIGO requirements before selecting modules and architecture. Never fabricate source documents.
2. Reuse shared architecture and generic UI components only through explicitly versioned, permission-safe interfaces.
3. Define isolated FIGO identity/roles, projects, databases or namespaces, storage buckets, audit logs, RLS, secrets, and deployment targets.
4. Draft module dependency graph via Graphify/Nx and frontend/backend API contract; run Pact, pgTAP and Playwright on synthetic FIGO records in an isolated local lab.
5. Test cross-tenant/cross-project denial and rollback. No access to SHEVA OS business data; authenticate FIGO accounts separately.
6. Produce a decision report and evidence; no production deployment or DB write without explicit approval.

Output: `reports/figo/<date>/` architecture, source provenance, tests, SHA256, isolation matrix, gaps and GO/NO-GO.
