# DB Adapter Refactor Plan (Jobs/Mapper/File Upload/Reports)

## Purpose
Create a database-adapter layer so Jobs, Mapping, File Upload, and Reports work across new target databases without code changes.

## Goals
- Centralize DB-specific SQL syntax in adapters.
- Keep business logic and datatype selection unchanged.
- Preserve current behavior for Oracle and PostgreSQL.
- Add MySQL support and simplify future DB onboarding.
- Avoid breaking Mapping, File Upload, and Reports flows.

## Non-Goals
- No schema changes required.
- No API contract changes unless explicitly noted.
- No UI changes required.

## Current Issue Summary
- DB type detection and SQL syntax are scattered in modules.
- Oracle-style binds can leak into non-Oracle paths when detection fails.
- Adding a new DB requires multiple code edits across modules.

## Proposed Design

### 1) Adapter Interface
Create a small adapter contract used by all modules that touch target DBs:

- detect_db_type(connection) -> str
- table_exists(cursor, schema, table) -> bool
- column_exists(cursor, schema, table, column) -> bool
- build_create_table(schema, table, columns, table_type) -> str
- build_alter_table(schema, table, columns) -> str
- supports_sequence() -> bool
- build_sequence_sql(schema, table) -> Optional[str]
- normalize_identifier(name) -> str

### 2) Adapter Registry
Map DBTYP to adapter class:

- ORACLE -> OracleAdapter
- POSTGRESQL -> PostgresAdapter
- MYSQL -> MysqlAdapter
- GENERIC -> GenericAdapter (safe fallback, minimal features)

Registry lookup rules:
- Prefer DBTYP from metadata (DMS_DBCONNECT) when available.
- Fallback to driver-based detection only if DBTYP is missing.
- If adapter missing: return clear error "Unsupported DBTYP" or use GENERIC with warning.

### 3) Module Integration

#### Jobs
- Replace per-DB if/else blocks in create_target_table with adapter calls.
- Keep DBTYP filtering of DMS_PARAMS (target + GENERIC fallback) intact.
- Use adapter to:
  - check table/column existence
  - build CREATE/ALTER DDL
  - handle sequence or AUTO_INCREMENT

#### Mapping
- No query changes required if using datatype lookup helpers.
- Ensure target DBTYP is passed to datatype selection APIs.
- Adapter not required for metadata reads.

#### File Upload
- Table creation should use the same adapter functions as Jobs.
- _resolve_data_types remains unchanged (DBTYP + GENERIC logic).

#### Reports
- Reports do not build DDL directly.
- Ensure any target-DB SQL formatting uses adapter (if present).
- No change needed if reports only read metadata and execute user SQL.

## Backward Compatibility
- Existing Oracle and PostgreSQL flows remain unchanged in output.
- Existing calls keep the same signature.
- GENERIC fallback continues to work if DBTYP cannot be detected.

## Test Plan (High-Level)

### Unit Tests
- Adapter contract tests: table_exists, column_exists, DDL generation.
- Jobs create_target_table uses adapter for each DB type.
- File Upload table creation uses adapter.

### Integration Tests
- Create job with Oracle target -> validate Oracle DDL and column types.
- Create job with PostgreSQL target -> validate PostgreSQL DDL.
- Create job with MySQL target -> validate MySQL DDL and no sequence.
- File upload creates tables for each DB type.
- Mapping datatype suggestions use target DBTYP (no regression).
- Reports run on existing datasets (no regression).

## Files To Touch (Proposed)
- backend/modules/common/db_adapter/
  - base_adapter.py (new)
  - oracle_adapter.py (new)
  - postgres_adapter.py (new)
  - mysql_adapter.py (new)
  - registry.py (new)
- backend/modules/jobs/pkgdwjob_python.py
- backend/modules/file_upload/table_creator.py
- backend/modules/jobs/pkgdwjob_create_job_flow.py (if DDL logic is present)

## Rollout Steps
1. Add adapter layer with Oracle/Postgres/MySQL implementations.
2. Wire Jobs create_target_table to adapter (no logic change in DMS_PARAMS).
3. Wire File Upload table creation to adapter.
4. Run unit/integration tests for each DB type.
5. Validate Mapping and Reports for no regression.

## Open Questions
- Confirm preferred behavior when DBTYP is unknown: fail fast or use GENERIC.
- Confirm MySQL audit column types (DATETIME vs TIMESTAMP).
- Confirm SKEY strategy for MySQL (AUTO_INCREMENT vs sequence table).

## Success Criteria
- New DB type onboarding requires adapter + DMS_PARAMS entries only.
- No code changes in Jobs/Mapping/File Upload/Reports for new DBs.
- Existing Oracle/Postgres jobs continue to work without changes.
