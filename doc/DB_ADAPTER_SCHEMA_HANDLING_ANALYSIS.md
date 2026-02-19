# Database Adapter Schema Handling Analysis

## Issue Summary
MySQL adapter's `format_table_ref()` was generating `schema.table`  format (e.g., `CDR.DIM_ACNT_LN2`), causing "Unknown database 'CDR'" error when the connection was made to a different database than specified in `trgschm`.

## Root Cause
In MySQL:
- Schema and Database are synonymous (no separate schema concept within a database)
- Connection parameter: `database=dbsrvnm` (from DMS_DBCONDTLS)
- Job parameter: `trgschm='CDR'` (from DMS_JOB)
- If `dbsrvnm != trgschm`, CREATE TABLE with `trgschm.table` fails

## Fix Applied
**MySQL Adapter** ([mysql_adapter.py](backend/modules/common/db_adapter/mysql_adapter.py))
```python
def format_table_ref(self, schema: Optional[str], table: str) -> str:
    """
    MySQL uses database-level connections, so schema is the database name.
    Since the connection already selects the database, we only use table name
    in DDL statements (CREATE/ALTER TABLE).
    """
    return table  # Do NOT prefix with schema/database name
```

## Analysis of Other Adapters

### ✅ CORRECT (No changes needed)

**PostgreSQL** - Supports real schemas within databases:
- Connection: `database=dbsrvnm` 
- Schema: Can be different from database (e.g., connect to `mydb` database, use `public` or `analytics` schema)
- DDL Format: `schema.table` is CORRECT
- Example: Connect to database `warehouse`, create table `analytics.sales`

**MSSQL/SQL Server** - Supports schemas within databases:
- Connection: `DATABASE=dbsrvnm`
- Schema: Typically `dbo` or custom schemas within the database
- DDL Format: `schema.table` is CORRECT
- Example: Connect to database `SalesDB`, create table `dbo.Customers`

**Sybase** - Supports owners (similar to schemas):
- Connection: `DATABASE=dbsrvnm`
- Owner: Database owner or specific user
- DDL Format: `owner.table` is CORRECT
- Example: Connect to database `mydb`, create table `guest.orders`

**Oracle** - Schema-based organization:
- Connection: No database parameter, uses DSN/service name
- Schema: User/schema name
- DDL Format: `schema.table` is CORRECT
- Example: Connect to Oracle instance, create table `HR.EMPLOYEES`

**Hive** - Uses database.table format:
- Connection: Can specify database or use default
- DDL should check if cross-database references are needed
- Current implementation: `database.table` format used
- Status: CORRECT for Hive semantics

**Redshift** - Based on PostgreSQL:
- Connection: `database=dbsrvnm`
- Schema: Supports schemas within database (like PostgreSQL)
- DDL Format: `schema.table` is CORRECT

**Snowflake** - Multi-level hierarchy (database.schema.table):
- Connection: Specifies database context
- Schema: Supports schemas within database
- DDL Format: `schema.table` (within connection database) is CORRECT
- Note: Full format is `database.schema.table`, but connection context handles database

**DB2** - Schema-based organization:
- Connection: `DATABASE=dbname` parameter in connection string
- Schema: User/schema name (similar to Oracle)
- DDL Format: `schema.table` is CORRECT
- Example: Connect to DB2 database, create table `MYSCHEMA.ORDERS`

## Key Distinction

**MySQL is unique** because:
1. Schema = Database (no hierarchy)
2. Cannot create tables in different databases from current connection without explicit `USE <database>` statement
3. `trgschm` must match `dbsrvnm` or the CREATE TABLE fails

**All other databases**:
1. Schema is a namespace WITHIN a database
2. Connection selects database, but schemas can be referenced within that database
3. `schema.table` format works correctly

## Recommendation for Users

When creating jobs with MySQL targets:
- Ensure `trgschm` (target schema in job) matches `dbsrvnm` (database in connection config)
- Or leave `trgschm` empty/NULL to use the connection's default database
- MySQL does not support cross-database table creation without changing connection context

## Testing

### Test Case 1: MySQL with matching database
- Connection: `dbsrvnm='CDR'`
- Job: `trgschm='CDR'`
- Expected DDL: `CREATE TABLE DIM_ACNT_LN2` (no prefix)
- Status: ✅ Should work

### Test Case 2: PostgreSQL with schema
- Connection: `database='warehouse'`
- Job: `trgschm='analytics'`
- Expected DDL: `CREATE TABLE "analytics"."sales"` (with schema prefix)
- Status: ✅ Should work

### Test Case 3: MSSQL with schema
- Connection: `DATABASE='SalesDB'`
- Job: `trgschm='dbo'`
- Expected DDL: `CREATE TABLE dbo.Customers` (with schema prefix)
- Status: ✅ Should work

---

**Date**: 2026-02-18  
**Version**: Post-Adapter Refactor  
**Related Files**:
- [backend/modules/common/db_adapter/mysql_adapter.py](backend/modules/common/db_adapter/mysql_adapter.py)
- [backend/database/dbconnect.py](backend/database/dbconnect.py)
- [backend/modules/jobs/pkgdwjob_python.py](backend/modules/jobs/pkgdwjob_python.py)
