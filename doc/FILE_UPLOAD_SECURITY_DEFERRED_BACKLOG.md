# File Upload Security - Deferred Backlog (Current vs Future)

## Purpose
This document captures **security controls not yet fully implemented** in the current file upload module, so implementation can be resumed later without losing scope.

It also clarifies what is currently safe to deploy for customers using the present application behavior.

---

## Current Implementation (Working Today)

The following are already active in current runtime:
- File upload config CRUD (`DMS_FLUPLD`, `DMS_FLUPLDDTL`)
- Column mapping, derivation logic, audit column handling
- File parsing, transformation, target table creation, data loading
- Batch-size driven loading (`batch_size` is used)
- Execution history and error capture (`DMS_FLUPLD_RUN`, `DMS_FLUPLD_ERR`)
- Upload scheduling metadata (`DMS_FLUPLD_SCHD`)

### Core runtime references
- `backend/modules/file_upload/file_upload_service.py`
- `backend/modules/file_upload/file_upload_executor.py`
- `backend/modules/file_upload/fastapi_file_upload.py`

---

## Deferred Security Scope (Not Fully Wired Yet)

### 1) File integrity & verification metadata on `DMS_FLUPLD`
Deferred columns (design exists, runtime not fully enforcing yet):
- `FLHASH`, `FLSZ`, `FLMIMTYP`
- `FLVRFYFLG`, `FLVRFYDT`, `FLVRFYBY`
- `FLQRNFLG`, `FLQRNRSN`
- `FLSCNFLG`, `FLSCNDT`, `FLSCNRSLT`
- `FLACCLVL`, `FLENCFLG`, `FLENCALG`
- `FLUPLDCNT`, `FLLSTACCTM`, `FLACCCNT`
- `FLRTRNTM`, `FLRTRNPLCY`

### 2) Security control tables (planned, not fully active in flow)
- `DMS_FLUPLDACCLG` (access audit)
- `DMS_FLUPLDVLD` (validation rules)
- `DMS_FLUPLDSEC` (global security policy)

### 3) Runtime enforcement still pending
- MIME and magic-byte verification enforcement
- Hash generation + comparison enforcement
- Malware scanner integration (e.g., ClamAV/Defender/custom adapter)
- Quarantine workflow
- Access-level authorization checks during file operations
- Encryption policy enforcement (at-rest/in-transit flags)
- Retention policy execution (expiry and cleanup jobs)
- Centralized policy-read from `DMS_FLUPLDVLD` and `DMS_FLUPLDSEC` in upload execution path

---

## What Was Prepared for Later

### Existing artifacts available to resume from
- Security plan: `doc/FILE_UPLOAD_SECURITY_PLAN.md`
- Security migration: `doc/database_migration_file_upload_security_columns.sql`
- Full install scripts (include deferred security schema):
  - `doc/database_install_postgresql_full.sql`
  - `doc/database_install_oracle_full.sql`

### Customer-safe baseline install scripts (current app aligned)
These scripts intentionally exclude deferred security schema so deployment matches current runtime:
- `doc/database_install_postgresql_current_baseline.sql`
- `doc/database_install_oracle_current_baseline.sql`

---

## Recommended Implementation Phases (Later)

### Phase S1: Metadata activation
- Add deferred columns/tables in target environments
- Add repository/service methods to read/write these fields
- Keep controls in monitor mode (no hard blocking yet)

### Phase S2: Validation & scan enforcement
- Enforce file-type/size/content rules from `DMS_FLUPLDVLD`
- Integrate malware scan and quarantine handling
- Persist scan/verify outcomes in `DMS_FLUPLD`

### Phase S3: Access/audit and policy hardening
- Write all access events into `DMS_FLUPLDACCLG`
- Enforce `FLACCLVL` and related permission checks
- Add policy fallback behavior if scanner/config unavailable

### Phase S4: Retention & closure
- Implement retention scheduler/cleanup using `FLRTRNTM` / `FLRTRNPLCY`
- Add dashboards/reports for security operations
- Final UAT and go-live checklist

---

## Definition of Done (Security Completion)

Security implementation can be considered complete when all are true:
1. Invalid/malicious files are reliably blocked or quarantined per policy.
2. `DMS_FLUPLD` security lifecycle fields are updated by runtime, not manually.
3. `DMS_FLUPLDVLD` and `DMS_FLUPLDSEC` drive behavior (no hardcoded policy logic).
4. `DMS_FLUPLDACCLG` records traceable access/audit events.
5. Retention actions execute automatically and are auditable.
6. Automated tests + UAT signoff cover happy path and failure scenarios.

---

## Notes for Deployment Teams

- If deploying current functionality only, use the `*_current_baseline.sql` scripts.
- If planning immediate security rollout, use `*_full.sql` plus phased app wiring.
- Keep migration path reversible: baseline -> security migration -> feature toggles -> enforce mode.
