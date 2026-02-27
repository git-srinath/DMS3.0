# Dashboard Creator Implementation Plan

## Document Control
- **Project**: DMS Tool
- **Module**: Dashboard Creator (under Reports)
- **Date**: 2026-02-20
- **Status**: Draft for Review
- **Scope**: Design and phased implementation plan only (no code in this document)

## Naming Convention Note (Critical)
- Metadata tables exist in Oracle and PostgreSQL.
- For PostgreSQL environments, metadata tables and columns are maintained in **lower case**.
- All PostgreSQL migration scripts and SQL references in implementation must use lower-case table names and column names.
- Any cross-database SQL logic must account for Oracle/PostgreSQL naming differences without breaking existing lower-case PostgreSQL metadata.

---

## 1) Objective

Add a **Dashboard Creator** capability to the application so business users can:
- Create dashboards of their choice.
- Use either a table/view source or query-based source.
- Build charts/widgets with guided configuration.
- Apply filters and arrange layouts.
- Save, run, and share dashboards.
- Export dashboard output to **PDF** or **PPT**.

This module must be accessible as a **Card inside the Reports section on the main page**.

---

## 2) Current Application Summary (As-Is)

### Functional areas already available
- Jobs, file management, reports, and operational dashboard are already present.
- Reports module already supports SQL source integration, SQL description, previews, and multi-format output.
- Existing dashboard page currently serves predefined operational analytics (job metrics), not user-defined dashboard authoring.

### Relevant strengths to reuse
- Existing report SQL validation/execution architecture.
- Existing chart stack on frontend.
- Existing role/module access framework.
- Existing export conventions and download flow.

### Gap
- No metadata-driven **self-service dashboard builder** for business users.
- No **PPT export** for dashboards currently.

---

## 3) Business User Experience (To-Be)

## 3.1 Primary user story
As a business user, I can create and maintain dashboards without coding by selecting data, choosing chart types, and exporting the result for presentations/reviews.

## 3.2 End-to-end journey
1. User opens **Home** and clicks **Dashboard Creator** card under Reports group.
2. User clicks **Create Dashboard**.
3. User enters dashboard name/description.
4. User selects data source:
   - **Table/View mode** (guided), or
   - **SQL mode** (advanced).
5. System profiles/validates source columns.
6. User adds widgets (KPI, table, bar, line, pie, etc.) and maps fields.
7. User configures filters (global + widget-level).
8. User previews each widget and overall dashboard.
9. User arranges layout by drag/resize.
10. User saves dashboard.
11. User exports to **PDF** or **PPT** when needed.

## 3.3 UX principles
- Default to guided no-code flow.
- Keep advanced SQL optional.
- Inline validation and clear error messaging.
- Fast preview and safe execution limits.

---

## 4) Scope and Boundaries

## 4.1 In scope
- New Dashboard Creator card placement in Reports section.
- Dashboard CRUD (create/list/edit/delete/clone).
- Widget authoring and configuration.
- Source selection (table/query).
- Filtering and layout persistence.
- Export to PDF and PPT.
- Access control integration.
- Audit logging for creation/export actions.

## 4.2 Out of scope (initial release)
- AI-generated charts/insights.
- Real-time websocket auto-refresh.
- Embedded external BI tool integration.
- Pixel-perfect custom theme builder.

---

## 5) Architecture Design

## 5.1 Frontend architecture
- Add a new route page for dashboard creation and management (e.g., `/dashboard_creator` or `/dashboards`).
- Keep existing `/dashboard` for operational metrics unless explicitly merged later.
- Use existing UI stack and chart libraries already used by the dashboard pages.
- Suggested component split:
  - `DashboardListPage`
  - `DashboardEditorPage`
  - `DataSourceSelector`
  - `WidgetConfigurator`
  - `FilterBuilder`
  - `LayoutCanvas`
  - `DashboardPreview`
  - `ExportDialog`

## 5.2 Backend architecture
- Introduce `dashboard_service.py` (new service layer in dashboard module) with metadata-driven logic.
- Extend dashboard FastAPI router with CRUD, preview, execute, export endpoints.
- Reuse report metadata/query helper patterns where practical to avoid duplicate SQL parsing/validation logic.

## 5.3 Data flow
1. Frontend sends dashboard definition payload.
2. Backend validates source + permissions.
3. Backend stores dashboard metadata + widget JSON.
4. Preview requests execute bounded queries.
5. Export requests run dashboard dataset pipeline, render output document, and return file stream.

---

## 6) Data Model (Proposed)

> Final naming can be aligned with existing DMS table naming conventions.

### 6.1 `DMS_DASH_DEF` (dashboard header)
- `DASH_ID` (PK)
- `DASH_NAME`
- `DESCRIPTION`
- `OWNER_USER_ID`
- `IS_ACTIVE`
- `CURFLG`
- `CRTD_BY`, `CRTD_DT`, `UPDT_BY`, `UPDT_DT`

### 6.2 `DMS_DASH_WIDGET` (widgets)
- `WIDGET_ID` (PK)
- `DASH_ID` (FK)
- `WIDGET_NAME`
- `WIDGET_TYPE` (KPI, TABLE, BAR, LINE, PIE, AREA, etc.)
- `SOURCE_MODE` (TABLE, SQL, REPORT_REF optional)
- `SQL_SOURCE_ID` (nullable)
- `ADHOC_SQL` (nullable)
- `DB_CONNECTION_ID` (nullable)
- `CONFIG_JSON` (field mapping, aggregation, sorting, formatting)
- `LAYOUT_JSON` (x, y, w, h)
- `ORDER_NO`
- `IS_ACTIVE`

### 6.3 `DMS_DASH_FILTER`
- `FILTER_ID` (PK)
- `DASH_ID` (FK)
- `SCOPE` (GLOBAL/WIDGET)
- `WIDGET_ID` (nullable)
- `FILTER_KEY`
- `FILTER_TYPE` (DATE_RANGE, LIST, NUMERIC_RANGE, TEXT)
- `FILTER_CONFIG_JSON`

### 6.4 `DMS_DASH_SHARE`
- `SHARE_ID` (PK)
- `DASH_ID` (FK)
- `SHARE_TYPE` (USER/ROLE)
- `SHARE_REF_ID`
- `CAN_VIEW`, `CAN_EDIT`, `CAN_EXPORT`

### 6.5 `DMS_DASH_EXPORT_LOG`
- `EXPORT_ID` (PK)
- `DASH_ID` (FK)
- `EXPORT_FORMAT` (PDF/PPT)
- `EXPORTED_BY`
- `EXPORTED_AT`
- `STATUS`
- `MESSAGE`

---

## 7) API Design (Proposed)

## 7.1 Dashboard management
- `GET /api/dashboards`
- `POST /api/dashboards`
- `GET /api/dashboards/{dashboardId}`
- `PUT /api/dashboards/{dashboardId}`
- `DELETE /api/dashboards/{dashboardId}`
- `POST /api/dashboards/{dashboardId}/clone`

## 7.2 Data/source support
- `GET /api/dashboards/sql-sources`
- `POST /api/dashboards/describe-sql`
- `POST /api/dashboards/preview-widget`
- `POST /api/dashboards/{dashboardId}/preview`

## 7.3 Execution/export
- `POST /api/dashboards/{dashboardId}/execute`
- `POST /api/dashboards/{dashboardId}/export` with payload `{ format: "PDF" | "PPT", filters: {...} }`

## 7.4 Response standards
- Follow existing success/error envelope patterns used in current reports APIs.
- Include error codes for validation, permission, SQL safety, timeout, and unsupported chart config.

---

## 8) Security and Governance

## 8.1 Access control
- Add module keys as required:
  - `dashboard_creator` (new)
  - retain existing `dashboard` (operational page) behavior
- Optionally split by action permissions in API layer:
  - view, edit, export

## 8.2 SQL safety controls
- Restrict to read-only SQL.
- Reject DDL/DML statements.
- Enforce row limits and execution timeout for preview/export.
- Validate selected connection and user entitlement.

## 8.3 Data governance
- Audit create/update/delete/export actions.
- Maintain ownership and sharing rules.
- Prevent cross-user access unless shared/authorized.

---

## 9) Export Strategy (PDF + PPT)

## 9.1 PDF export
- Render dashboard title, filters used, chart snapshots, and optional data summary tables.
- Use server-side generation for consistency and controlled formatting.

## 9.2 PPT export
- Generate presentation with:
  - Title slide (dashboard metadata and run timestamp)
  - One slide per widget (chart image + key metrics)
  - Optional appendix slides for raw tables
- Recommended backend package: `python-pptx`.

## 9.3 Dependency impact
- Backend requirements update expected:
  - add `reportlab` (if not already installed in environment)
  - add `python-pptx`
- Keep frontend dependencies minimal by handling export server-side.

---

## 10) Non-Functional Requirements

- **Performance**: preview under acceptable SLA for bounded row limits.
- **Scalability**: widget queries should support pagination/sampling where needed.
- **Reliability**: export jobs must fail gracefully and return actionable errors.
- **Maintainability**: common query/validation helpers should be shared with reports logic.
- **Observability**: structured logs for API, query, and export stages.

---

## 11) Validation Rules (Initial)

- Dashboard name required and unique per owner (or globally as per policy).
- Widget must have valid type and required field mappings.
- Aggregation + data type compatibility checks.
- Global filter references must map to existing fields.
- Export only for saved dashboards (optional policy).

---

## 12) Error Handling Design

User-facing error categories:
- Invalid source selection.
- SQL parse/validation failure.
- Unauthorized access.
- Query timeout/row limit breach.
- Unsupported chart configuration.
- Export generation failure.

Each error response should include:
- `message`
- `code`
- `details` (field/widget-level where applicable)

---

## 13) Six-Phase Implementation Plan

## Phase 1: Foundation & Data Model
**Goal**: introduce metadata schema and security baseline.
- Add migration scripts for dashboard tables.
- Add/extend module access keys for creator/view/export.
- Prepare backend model helpers/repositories.
- Define seed/default values and indexes.

**Deliverables**:
- SQL migration script(s)
- access-control updates
- schema documentation

## Phase 2: Backend APIs (Core CRUD + Preview)
**Goal**: functional backend for dashboard definitions and data preview.
- Implement dashboard CRUD endpoints.
- Implement source discovery + SQL describe endpoint.
- Implement widget preview endpoint with bounded limits.
- Add validation and error code contracts.

**Deliverables**:
- FastAPI endpoints with tests
- service layer implementation
- API contract draft

## Phase 3: Frontend Dashboard Creator UX
**Goal**: business-user authoring flow.
- Add Dashboard Creator card in Reports section on Home page.
- Build dashboard list/create/edit screens.
- Implement widget builder and layout canvas.
- Implement preview interactions and save/update flow.

**Deliverables**:
- new frontend pages/components
- integrated navigation/card
- basic UX acceptance scenarios

## Phase 4: Export Engine (PDF + PPT)
**Goal**: production-ready exports.
- Add backend PDF export pipeline.
- Add backend PPT export pipeline.
- Add frontend export dialog and download handling.
- Add export logs/audit persistence.

**Deliverables**:
- export endpoints
- PDF/PPT output templates
- audit trail records

## Phase 5: Hardening & Quality
**Goal**: robustness, security, and performance.
- SQL safety hardening and stricter validation.
- timeout/row-limit policy enforcement.
- retry/partial-failure handling in export pipeline.
- role/ownership test coverage.

**Deliverables**:
- security/performance test evidence
- finalized error taxonomy
- runbook updates

## Phase 6: UAT, Documentation, and Release
**Goal**: user readiness and controlled rollout.
- UAT scripts for business users.
- user guide and admin guide.
- release checklist and rollback plan.
- phased enablement by role/team.

**Deliverables**:
- UAT signoff artifacts
- operational documentation
- release plan

---

## 14) Testing Strategy

## 14.1 Backend tests
- CRUD and validation tests.
- SQL describe/preview tests across supported DB adapters.
- security/authorization tests.
- export generation tests (PDF/PPT existence and structure checks).

## 14.2 Frontend tests
- Create/edit/delete dashboard flows.
- Widget config and validation states.
- Filter interactions.
- Export UX and failure messaging.

## 14.3 UAT scenarios
- non-technical user creates dashboard from table source.
- advanced user creates dashboard from SQL source.
- role-based sharing and access enforcement.
- successful PDF and PPT export for presentation use.

---

## 15) Risks and Mitigations

1. **Complex SQL misuse**
   - Mitigation: read-only checks, guardrails, preview limits.

2. **Large dataset performance issues**
   - Mitigation: sampling/pagination, async export if required.

3. **PPT formatting inconsistencies**
   - Mitigation: fixed templates and standardized slide layout.

4. **Permission drift**
   - Mitigation: central module-key governance and API checks.

5. **Cross-database behavior differences**
   - Mitigation: adapter-aware query handling and dedicated tests.

---

## 16) Implementation Readiness Checklist

- [ ] Finalize route name (`/dashboard_creator` vs `/dashboards`)
- [ ] Approve table names/DDL
- [ ] Approve API payload schema
- [ ] Approve widget types for v1
- [ ] Approve export layout style (PDF/PPT)
- [ ] Approve access control matrix
- [ ] Approve phased timeline and owner mapping

---

## 17) Suggested Next Step After Approval

After this document is approved, begin **Phase 1** by creating:
1. migration SQL scripts for dashboard tables,
2. backend scaffold (router/service/repository placeholders),
3. frontend card entry + route scaffold.

This keeps the implementation incremental and reviewable per phase.

---

## 18) Phase 1 Implementation Artifacts (Executed)

The following Phase 1 foundation artifacts are now prepared:

1. **Oracle migration script**
   - `doc/database_migration_dashboard_creator_oracle.sql`
   - Creates dashboard metadata tables, indexes, comments, and sequences.

2. **PostgreSQL migration script (lower-case identifiers)**
   - `doc/database_migration_dashboard_creator_postgresql.sql`
   - Uses lower-case table names and lower-case column names throughout.

3. **Access control groundwork**
   - Updated `backend/modules/security/utils.py`
   - Added module key: `dashboard_creator` under `report_management`.

These artifacts complete the initial Phase 1 setup for schema and module-access readiness.
