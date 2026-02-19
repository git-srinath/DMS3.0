# Phase 2A → Phase 2B Transition Document
**Handoff from Backend API Development to Frontend Implementation**

**Prepared:** February 16, 2026  
**Phase 2A Status:** ✅ COMPLETE  
**Phase 2B Status:** ⏳ READY TO START  
**Estimated Phase 2B Duration:** 3 days (24 hours)

---

## Executive Summary

Phase 2A backend development is **100% complete** with 5 advanced helper functions and 6 new API endpoints. The frontend team now has a complete, well-documented, production-ready API to consume for Phase 2B.

---

## What Frontend Can Use Now

### 14 Ready-to-Use API Endpoints

**Phase 1 Endpoints (Foundation):**
```
GET    /mapping/supported_databases              ← List all databases
POST   /mapping/supported_database_add           ← Add new database
PATCH  /mapping/supported_database_status        ← Enable/disable database
GET    /mapping/datatypes_for_database           ← Get datatypes for DB
GET    /mapping/all_datatype_groups              ← All datatypes grouped
POST   /mapping/validate_datatype_compatibility  ← Check type compatibility
POST   /mapping/clone_datatypes_from_generic     ← Clone to new database
GET    /mapping/validate_parameter_delete        ← Check before delete
```

**Phase 2A Endpoints (Advanced):**
```
POST   /mapping/datatype_suggestions            ← AI suggestions
PUT    /mapping/datatype_update                 ← Edit datatype
DELETE /mapping/datatype_remove                 ← Safe delete
GET    /mapping/datatype_impact_analysis        ← Show impact
GET    /mapping/datatype_usage_stats            ← Usage analytics
POST   /mapping/validate_all_mappings           ← Bulk validation
```

### 23 Helper Functions Available

**Database Management (Phase 1):**
- get_supported_databases()
- add_supported_database()
- get_database_status()
- update_database_status()

**Datatype Management (Phase 1):**
- get_parameter_mapping_datatype_for_db()
- get_all_datatype_groups()
- verify_datatype_compatibility()
- clone_datatypes_from_generic()
- is_datatype_in_use()

**Advanced Features (Phase 2A):**
- get_datatype_suggestions() ← Use for suggestions
- validate_all_mappings_for_database() ← Use for validation
- sync_datatype_changes() ← Use for propagation
- get_datatype_usage_statistics() ← Use for dashboard
- suggest_missing_datatypes() ← Use for gap analysis

**Plus all Phase 1 deletion safeguards (5 functions)**

---

## Frontend Implementation Guide

### Recommended Component Structure

```
src/pages/settings/datatypes/
├─ index.tsx                          ← Main page
├─ DatabaseSelector.tsx               ← Choose database
├─ DatatypesTable.tsx                 ← View all datatypes
├─ DatatypeForm.tsx                   ← Add/edit form
├─ DatatypeEditor.tsx                 ← Edit with impact analysis
├─ DatabaseWizard.tsx                 ← Setup wizard (4 steps)
├─ UsageDashboard.tsx                 ← Charts and stats
├─ ValidationResults.tsx              ← Validation display
└─ hooks/
   ├─ useDatatypeAPI.ts               ← API calls
   ├─ useDataTypeForm.ts              ← Form validation
   └─ useSuggestions.ts               ← Get suggestions with loading
```

### API Integration Pattern

```typescript
// Example: Get suggestions for new database
const response = await fetch(
  '/mapping/datatype_suggestions?target_dbtype=SNOWFLAKE&based_on_usage=true',
  {
    method: 'POST',
    headers: {
      'X-User': currentUser.id,
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();
if (response.ok) {
  // Display suggestions with confidence scores
  setSuggestions(data.suggestions);
} else {
  // Show error message
  showError(data.detail);
}
```

### Form Integration Pattern

```typescript
// Example: Update datatype with validation
const handleUpdateDatatype = async (formData) => {
  try {
    // First, get impact analysis
    const impactResponse = await fetch(
      `/mapping/datatype_impact_analysis?prcd=${formData.prcd}&new_prval=${formData.newValue}&dbtype=${formData.dbtype}`
    );
    const impact = await impactResponse.json();
    
    // Show impact to user for confirmation
    setImpactAnalysis(impact);
    
    // If user confirms, make the update
    if (userConfirmed) {
      const updateResponse = await fetch(
        '/mapping/datatype_update',
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-User': currentUser.id
          },
          body: JSON.stringify(formData)
        }
      );
      
      if (updateResponse.ok) {
        showSuccess('Datatype updated');
        refreshData();
      }
    }
  } catch (error) {
    showError(error.message);
  }
};
```

### Error Handling Pattern

```typescript
// Handle different HTTP status codes appropriately
if (response.status === 400) {
  // Validation error - show field errors
  showValidationErrors(data.errors);
} else if (response.status === 404) {
  // Not found - show not found message
  showError('Datatype not found');
} else if (response.status === 409) {
  // Conflict - in use, can't delete
  showWarning(`Cannot delete: ${data.message}`);
} else if (response.status === 422) {
  // Business logic violation
  showError(`Business logic error: ${data.message}`);
} else if (response.status === 500) {
  // Server error
  showError('Server error - please try again');
}
```

---

## User Workflows for Phase 2B

### Workflow 1: Add New Database Type
```
1. User clicks "Add Database"
2. Enter database type: SNOWFLAKE
3. Click "Get Suggestions"
   └─ Calls: POST /mapping/datatype_suggestions
   └─ Gets: List with confidence scores (0.95, 0.98, etc.)
4. Review suggestions (can customize)
5. Click "Create Database"
   └─ Calls: POST /mapping/supported_database_add
6. Click "Clone Datatypes"
   └─ Calls: POST /mapping/clone_datatypes_from_generic
   └─ Shows: 10 datatypes cloned, 0 skipped
7. Success message
```

### Workflow 2: Edit Datatype Definition
```
1. User finds INT datatype in table
2. Clicks "Edit"
3. Form shows current value: NUMBER(10,0)
4. User changes to: NUMBER(10,0) (or wants to change it)
5. Click "Show Impact"
   └─ Calls: GET /mapping/datatype_impact_analysis
   └─ Shows: "Used in 5 mappings" (severity: MEDIUM)
   └─ Shows: Warnings and recommendations
6. User reviews impact
7. Clicks "Update"
   └─ Calls: PUT /mapping/datatype_update
   └─ Returns: Success with warnings
8. Data refreshed, user sees updated value
```

### Workflow 3: Delete Datatype (Safe)
```
1. User selects datatype to delete
2. Clicks "Delete"
3. System checks: GET /mapping/validate_parameter_delete?prcd=INT
4. System responds:
   a) If safe: Show confirmation dialog "Sure you want to delete?"
      └─ User confirms
      └─ Calls: DELETE /mapping/datatype_remove
      └─ Shows: Success
   b) If in use: Show warning "Cannot delete - in use by 5 mappings"
      └─ Show link to affected mappings
      └─ No delete button
```

### Workflow 4: Review Usage Dashboard
```
1. User clicks "Analytics"
2. Dashboard loads and calls: GET /mapping/datatype_usage_stats
3. Shows:
   a) Pie chart: INT (25), VARCHAR (40), DATE (15), etc.
   b) By database: ORACLE (10 types), POSTGRESQL (8 types)
   c) Most used: VARCHAR
   d) Unused: FLOAT, CUSTOM_TYPE
4. User clicks "Missing Types for Snowflake"
   └─ Calls: GET /mapping/suggest_missing_datatypes?dbtype=SNOWFLAKE
   └─ Shows: JSON (priority: HIGH), CUSTOM_TYPE (MEDIUM)
```

### Workflow 5: Deploy Safety Check
```
1. User finishes datatype changes
2. Clicks "Validate Before Deploy"
3. System calls: POST /mapping/validate_all_mappings?dbtype=ORACLE
4. System returns:
   a) If all valid: Green checkmark, "All 15 mappings valid"
   b) If invalid: Red warning, "2 mappings have errors"
      └─ Shows details of what's wrong
      └─ Provides remediation help
5. User can deploy or cancel based on results
```

---

## API Response Patterns to Handle

### Success Response Pattern (200 OK)
```json
{
  "status": "success",
  "message": "Operation completed",
  "data": { /* operation-specific data */ }
}
```

### Validation Error Pattern (400)
```json
{
  "status": "error",
  "detail": "Required field missing",
  "errors": [
    {
      "field": "PRVAL",
      "message": "Cannot be empty",
      "suggestion": "Enter a valid value"
    }
  ]
}
```

### Not Found Pattern (404)
```json
{
  "status": "error",
  "detail": "Datatype INT not found for ORACLE"
}
```

### Conflict Pattern (409)
```json
{
  "status": "error",
  "detail": "Cannot delete: referenced by mappings",
  "blocking_references": 5,
  "blocking_types": ["mappings"]
}
```

### Server Error Pattern (500)
```json
{
  "status": "error",
  "detail": "Database connection failed"
}
```

---

## Frontend Dependencies

### Required Libraries
- React 18+
- Next.js 14+
- Material-UI (@mui/material)
- Axios or fetch API
- React Query (optional, recommended)
- Chart.js or Recharts (for dashboard)

### API Client Setup
```typescript
// Example: Create API client
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'X-User': getUserId()
  }
});

// Add interceptor for errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    handleApiError(error.response);
    return Promise.reject(error);
  }
);
```

---

## Testing Phase 2B Components

### Unit Tests
- Form validation (required fields, format)
- API response handling (success, errors)
- UI state management

### Integration Tests
- End-to-end workflows (add database, edit datatype, etc.)
- API integration (confirm endpoints are called correctly)
- Error handling (proper messages shown)

### Manual Testing
1. Add new database with suggestions
2. Edit datatype and see impact
3. Check validation results
4. View usage statistics
5. Try deleting in-use datatype (should be prevented)

---

## Documentation for Frontend

### API Documentation Location
- Full API docs: `/doc/PHASE2A_IMPLEMENTATION_COMPLETE.md`
- Quick reference: `/PHASE1_QUICK_REFERENCE.md`
- Curl examples in completion summary

### Code Documentation
- All helper functions have docstrings
- All endpoints have descriptions
- Examples provided for each endpoint

### Live API Documentation
- Swagger UI: `/docs` (when using FastAPI)
- ReDoc: `/redoc` (alternative documentation)

---

## Estimated Phase 2B Timeline

| Component | Duration | Difficulty |
|-----------|----------|-----------|
| Database selector + list | 2 hours | Easy |
| Datatype table & basic CRUD | 4 hours | Medium |
| Database wizard (4 steps) | 4 hours | Medium |
| Impact analysis display | 3 hours | Medium |
| Usage dashboard + charts | 4 hours | Medium |
| Validation results view | 3 hours | Easy |
| Error handling throughout | 2 hours | Easy |
| Testing & bug fixes | 2 hours | Medium |
| **Total Phase 2B** | **24 hours** | |

**Estimated Completion: February 19, 2026**

---

## Phase 2B Success Criteria

✅ All 14 API endpoints consumed successfully  
✅ Database wizard guides user through 4 steps  
✅ Datatype editor shows impact analysis  
✅ Usage dashboard displays statistics  
✅ Validation works before deployment  
✅ Error messages helpful and clear  
✅ All workflows from above work smoothly  
✅ Performance acceptable (< 2s page load)  
✅ Mobile responsive design  
✅ Accessibility compliant (WCAG 2.1)  

---

## Common Pitfalls to Avoid

❌ Not checking HTTP status codes (always check!)  
❌ Not sending X-User header (needed for audit)  
❌ Not handling 409 Conflict properly  
❌ Not showing impact analysis before updates  
❌ Failing to validate suggestions before use  
❌ Not handling async loading states  
❌ Over-fetching data (use filters)  

---

## Quick Reference for Frontend Dev

**API Base URL:** `http://localhost:8000`

**Required Headers:**
```json
{
  "Content-Type": "application/json",
  "X-User": "<current_user_id>"
}
```

**Most Important Endpoints (for Phase 2B):**
1. `POST /mapping/datatype_suggestions` - Pre-fill forms
2. `GET /mapping/datatype_impact_analysis` - Show impact
3. `GET /mapping/datatype_usage_stats` - Dashboard data
4. `POST /mapping/validate_all_mappings` - Pre-deploy check

**Error Codes to Handle:**
- 200/201: Success
- 400: Validation error
- 404: Not found
- 409: Conflict (in use)
- 422: Business logic error
- 500: Server error

---

## Next Phase: Phase 3 (Module Integration)

After Phase 2B, Phase 3 will integrate:
- Mapper module (update datatype references)
- Jobs module (adapt to new database types)
- File Upload module (adjust column mappings)
- Reports module (update datatype usage)

Phase 2B provides the foundation for these integrations.

---

## Questions or Issues During Phase 2B?

Refer to:
1. `/doc/PHASE2A_IMPLEMENTATION_COMPLETE.md` - Full API documentation
2. `/PHASE1_QUICK_REFERENCE.md` - Quick lookup
3. Function docstrings in `helper_functions.py`
4. Endpoint docstrings in `fastapi_parameter_mapping.py`

---

## Sign-Off: Phase 2A → Phase 2B

**Phase 2A Complete:** ✅  
**API Ready:** ✅  
**Documentation Complete:** ✅  
**Frontend Can Begin:** ✅

Phase 2B frontend development can start immediately.

---

*Prepared by: Backend Team*  
*Date: February 16, 2026*  
*Status: Ready for Frontend Handoff*
