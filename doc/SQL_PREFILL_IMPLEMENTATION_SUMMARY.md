# SQL Prefill Feature - Implementation Summary & Recommendations

## Updated Requirements Summary

Based on your feedback, the feature now includes:

1. ✅ **Column Selection** - Users choose which columns to prefill (not all automatically)
2. ✅ **Data Type Suggestions** - Show suggested data types from type mapping before finalizing
3. ✅ **SQL Registration** - Register new SQL to Manage SQL with duplicate detection
4. ✅ **Field Editability** - All fields editable until Save button is clicked

## Key Design Decisions

### 1. Column Selection UI
- **Multi-step dialog** with column selection screen
- Checkboxes for each column
- "Select All" / "Deselect All" options
- Only selected columns are prefilled to form

### 2. Data Type Suggestions
- Backend returns: `suggested_data_type` and `suggested_data_type_options`
- Frontend shows dropdown with suggested type pre-selected
- User can review and change before applying
- Uses existing parameter module (`get_parameter_mapping_datatype`)

### 3. SQL Duplicate Detection - **RECOMMENDED APPROACH**

After analyzing the complexity, I recommend **Option B (Simplified)** for initial implementation:

#### Recommended: Normalization + String Similarity
- **Normalize SQL**: Remove comments, normalize whitespace, case-insensitive
- **Compare**: Use string similarity algorithm (Python's `difflib` or `fuzzywuzzy`)
- **Show matches**: Top 5 queries with similarity > 70%
- **User decision**: View matched SQLs and choose to use existing or register new

**Why this approach:**
- ✅ Simpler to implement (2-3 hours vs 5-6 hours for hybrid)
- ✅ Good enough accuracy for most use cases
- ✅ Fast performance
- ✅ Easy to understand and maintain
- ✅ Can be enhanced later if needed

**Alternative (if more accuracy needed):**
- Use **Option D (Hybrid)** with column/table comparison
- More complex but more accurate
- Better for detecting logical duplicates

### 4. SQL Registration Flow

**When user enters new SQL:**
1. After column extraction → Show dialog: "Save this SQL to Manage SQL?"
2. If Yes:
   - Check for duplicates (using recommended approach)
   - Show results if duplicates found (with similarity scores)
   - User options:
     - **"Use Existing SQL"** - Load that SQLCODE instead
     - **"Register as New"** - Save with new SQLCODE
     - **"Cancel"** - Skip registration, just use for prefill
3. If No: Skip registration, proceed to prefill

**SQLCODE Generation:**
- Auto-generate: `SQL_001`, `SQL_002`, etc. (next available)
- Or let user enter custom SQLCODE
- Validate uniqueness before saving

### 5. Field Editability Behavior

**Before Save:**
- All form fields are editable (no restrictions)
- User can modify any prefilled value
- No validation locks
- Changes tracked but not enforced

**After Save:**
- Form returns to current behavior
- Fields become locked/restricted as per existing logic
- Validation rules apply
- Workflow states enforced

**Implementation:**
- Add state flag: `isUnsavedChanges` or `isPrefillMode`
- Keep all fields editable while flag is true
- Clear flag after Save
- Restore original form behavior

## Questions for Clarification

### 1. SQL Duplicate Detection Threshold
**Question:** What similarity percentage should trigger the duplicate alert?
- **Recommendation:** 70% - catches most duplicates without too many false positives
- **Alternative:** 80% - stricter, fewer alerts but might miss some duplicates

### 2. SQLCODE Auto-generation Format
**Question:** What format for auto-generated SQLCODE?
- **Option A:** `SQL_001`, `SQL_002`, etc. (sequential)
- **Option B:** `SQL_YYYYMMDD_001` (date-based)
- **Option C:** `SQL_<table_name>_001` (table-based)
- **Recommendation:** Option A (simple sequential)

### 3. Column Selection Default Behavior
**Question:** Should all columns be selected by default, or none?
- **Recommendation:** All selected by default (user can deselect)
- **Alternative:** None selected (user must explicitly select)

### 4. Data Type Options Source
**Question:** Should data type dropdown show:
- **Option A:** All available data types from parameter
- **Option B:** Only suggested mappings for source type
- **Recommendation:** Option B (more focused, less overwhelming)

### 5. SQL Registration Prompt Timing
**Question:** When to prompt for SQL registration?
- **Option A:** After column extraction, before applying to form
- **Option B:** After applying to form, as optional step
- **Recommendation:** Option A (capture SQL while it's fresh)

### 6. Duplicate Detection Scope
**Question:** Should duplicate detection check:
- **Option A:** Only current user's SQLs
- **Option B:** All SQLs in system (all users)
- **Recommendation:** Option B (prevent duplicates across all users)

### 7. Connection ID Handling
**Question:** When registering new SQL, should connection_id be:
- **Option A:** Required field (user must select)
- **Option B:** Optional (default to metadata connection)
- **Recommendation:** Option B (optional, with default)

## Implementation Phases

### Phase 1: Core Functionality (8-10 hours)
- Backend: Column extraction API
- Backend: Data type mapping integration
- Frontend: SQL selection dialog
- Frontend: Column selection screen
- Integration: Basic prefill functionality

### Phase 2: SQL Registration (4-5 hours)
- Backend: Duplicate detection API
- Backend: SQL registration API
- Frontend: Registration dialog
- Frontend: Duplicate detection UI

### Phase 3: Polish & Testing (2-3 hours)
- Field editability behavior
- Error handling
- Testing
- Refinement

**Total: 14-18 hours**

## Ready to Proceed?

Once you confirm:
1. Duplicate detection approach (recommended: Option B - Simplified)
2. Answers to clarification questions above
3. Any additional requirements

I can proceed with implementation immediately.

