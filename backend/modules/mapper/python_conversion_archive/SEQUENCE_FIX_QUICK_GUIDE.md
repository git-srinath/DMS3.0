# Quick Fix: Missing Oracle Sequences

## ⚠️ Issue
```
Error: Error in PKGDMS_MAPR.CREATE_UPDATE_SQL [133]: SqlCode=testsqlcd123 - 
ORA-02289: sequence does not exist
```

## ✅ Quick Solution

You have **two options** to create the missing sequences:

---

### **Option 1: Use Your Existing DDL File** ⭐ **RECOMMENDED**

The sequences are already defined in your existing DDL file!

**File Location:** `D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql`

**Steps:**

1. **Open your SQL client** (SQL*Plus, SQL Developer, etc.)

2. **Connect to your database:**
   ```sql
   sqlplus your_username/your_password@your_database
   ```

3. **Run the DDL file:**
   ```sql
   @D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql
   ```

   **OR** just run the sequence creation parts:

   ```sql
   -- From DWT_DDL_DWT.sql (lines 31, 58, 208, 402)
   CREATE SEQUENCE DMS_MAPRSEQ START WITH 1 INCREMENT BY 1;
   CREATE SEQUENCE DMS_MAPRDTLSEQ START WITH 1 INCREMENT BY 1;
   CREATE SEQUENCE DMS_MAPERRSEQ START WITH 1 INCREMENT BY 1;
   CREATE SEQUENCE DMS_MAPRSQLSEQ START WITH 1 INCREMENT BY 1;
   COMMIT;
   ```

4. **Verify:**
   ```sql
   SELECT sequence_name, last_number 
   FROM user_sequences 
   WHERE sequence_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ');
   ```

---

### **Option 2: Use the New Script**

If you prefer a standalone script with more options:

**File Location:** `D:\CursorTesting\DWTOOL\backend\modules\mapper\CREATE_SEQUENCES.sql`

```sql
@D:\CursorTesting\DWTOOL\backend\modules\mapper\CREATE_SEQUENCES.sql
```

---

## 🧪 Test After Fix

1. **Test in SQL:**
   ```sql
   SELECT DMS_MAPRSQLSEQ.NEXTVAL FROM DUAL;  -- Should return 1 (or next number)
   ```

2. **Test in Application:**
   - Go to **Manage SQL** module
   - Enter SQL Code: `testsqlcd123`
   - Enter SQL Query: `SELECT * FROM your_table`
   - Click **Create**
   - ✅ Should work now!

---

## 📝 Sequence Details

| Sequence | Purpose | Table | Line in DDL |
|----------|---------|-------|-------------|
| `DMS_MAPRSQLSEQ` | SQL query mappings | DMS_MAPRSQL | Line 402 |
| `DMS_MAPRSEQ` | Mappings | DMS_MAPR | Line 31 |
| `DMS_MAPRDTLSEQ` | Mapping details | DMS_MAPRDTL | Line 58 |
| `DMS_MAPERRSEQ` | Error logs | DMS_MAPERR | Line 208 |

---

## ⚠️ Important Notes

### If Sequences Already Exist in Another Schema:

Check if they exist elsewhere:
```sql
SELECT owner, sequence_name 
FROM all_sequences 
WHERE sequence_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ');
```

If they exist in a different schema (e.g., `DWT`), you need to either:

**A) Grant Access:**
```sql
-- Run as the schema owner or DBA
GRANT SELECT ON DWT.DMS_MAPRSQLSEQ TO your_username;
GRANT SELECT ON DWT.DMS_MAPRSEQ TO your_username;
GRANT SELECT ON DWT.DMS_MAPRDTLSEQ TO your_username;
GRANT SELECT ON DWT.DMS_MAPERRSEQ TO your_username;
```

**B) Create Synonyms:**
```sql
-- Run as your user
CREATE SYNONYM DMS_MAPRSQLSEQ FOR DWT.DMS_MAPRSQLSEQ;
CREATE SYNONYM DMS_MAPRSEQ FOR DWT.DMS_MAPRSEQ;
CREATE SYNONYM DMS_MAPRDTLSEQ FOR DWT.DMS_MAPRDTLSEQ;
CREATE SYNONYM DMS_MAPERRSEQ FOR DWT.DMS_MAPERRSEQ;
```

(You can find synonym examples in `DWT_DDL_CDR.sql` file)

---

## 🔍 Check Your Setup

Based on your existing files, it looks like you have a two-schema setup:
- **DWT** schema (main schema with sequences and tables)
- **CDR** schema (using synonyms to access DWT objects)

**Check which schema you're connected as:**
```sql
SELECT USER FROM DUAL;
```

**If you're connected as CDR schema**, make sure synonyms exist:
```sql
SELECT synonym_name, table_owner, table_name 
FROM user_synonyms 
WHERE synonym_name IN ('DMS_MAPRSQLSEQ', 'DMS_MAPRSEQ', 'DMS_MAPRDTLSEQ', 'DMS_MAPERRSEQ');
```

**If synonyms don't exist, create them:**
See file: `D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_CDR.sql` (lines 34, 38, 42)

---

## ✅ Checklist

- [ ] Connected to correct database/schema
- [ ] Ran sequence creation SQL
- [ ] Verified sequences exist (`user_sequences` query)
- [ ] Can execute `.NEXTVAL` on sequences
- [ ] If using multiple schemas, checked synonyms/grants
- [ ] Tested in application - SQL creation works

---

## 📞 Still Having Issues?

### Error: "Insufficient privileges"
```sql
-- Need CREATE SEQUENCE privilege
GRANT CREATE SEQUENCE TO your_username;
```

### Error: "Table or view does not exist"
You also need to create the tables first. Run the full DDL:
```sql
@D:\Git-Srinath\DWTOOL\PLSQL\DWT_DDL_DWT.sql
```

---

**Estimated Time to Fix:** 2-5 minutes  
**Difficulty:** Easy  
**Impact:** HIGH (Application won't work without this)

---

*Issue Date: November 12, 2025*  
*Last Updated: November 12, 2025*

