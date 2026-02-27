# Dashboard Creator Phase 6 UAT and Release Checklist

## Date
2026-02-20

## Purpose
Provide a complete UAT, release, and rollback checklist so full testing can begin and deployment can be controlled.

---

## 1) Environment Readiness
- [ ] Backend dependencies installed (`reportlab`, `python-pptx`)
- [ ] Metadata migration executed successfully
- [ ] `dms_dash_def`, `dms_dash_widget`, `dms_dash_filter`, `dms_dash_share`, `dms_dash_export_log` verified
- [ ] API service restarted after deployment
- [ ] Frontend rebuilt and deployed with latest Dashboard Creator page

---

## 2) Functional UAT Scenarios

### 2.1 Dashboard lifecycle
- [ ] Create dashboard with name/description
- [ ] Add multiple widgets and save
- [ ] Reload dashboard and verify widget persistence
- [ ] Update dashboard metadata and widgets
- [ ] Delete dashboard and verify soft-delete behavior

### 2.2 Data source and SQL
- [ ] DB connections dropdown shows all registered connections
- [ ] SQL describe returns columns for valid query
- [ ] SQL preview returns rows and metadata
- [ ] Invalid SQL returns actionable validation message

### 2.3 Access and navigation
- [ ] Home card navigation to Dashboard Creator works
- [ ] Sidebar entry visibility respects `dashboard_creator` access key
- [ ] Route title and page header render correctly

### 2.4 Export
- [ ] Export PDF downloads successfully
- [ ] Export PPT downloads successfully
- [ ] Export failure returns clean error (when induced)
- [ ] Export history panel shows success/failure operations

### 2.5 Export history
- [ ] History loads for all dashboards
- [ ] History filters by selected dashboard
- [ ] Status, message, file name, and timestamp values are accurate

---

## 3) Negative and Security Tests
- [ ] Non-SELECT SQL rejected
- [ ] DML/DDL SQL keywords rejected
- [ ] Overly long SQL rejected
- [ ] Unsupported widget type rejected
- [ ] Invalid source mode rejected
- [ ] Excessive widget count rejected

---

## 4) Performance Checks
- [ ] Create/update dashboard latency acceptable for target users
- [ ] Preview SQL with row limit performs within SLA
- [ ] Export generation time acceptable for representative datasets
- [ ] UI remains responsive with moderate export history volume

---

## 5) Release Checklist
- [ ] Confirm migration backup snapshot exists
- [ ] Confirm rollback SQL is available
- [ ] Confirm release notes communicated to users
- [ ] Confirm smoke tests pass after deployment
- [ ] Confirm monitoring/logging enabled for export endpoints

---

## 6) Rollback Checklist
- [ ] Disable Dashboard Creator route access if critical issue occurs
- [ ] Roll back backend deployment package
- [ ] Roll back frontend deployment package
- [ ] Restore metadata backup if schema rollback required
- [ ] Communicate rollback status and incident summary

---

## 7) Signoff Matrix
- [ ] Product Owner signoff
- [ ] QA/UAT lead signoff
- [ ] Backend lead signoff
- [ ] Frontend lead signoff
- [ ] Release manager signoff

---

## 8) Go-Live Recommendation
Proceed to production after all critical checklist items pass and no unresolved P1/P2 defects remain.
