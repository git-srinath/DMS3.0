# MySQL Adapter Fix Summary

**Date**: 2026-02-18  
**Issue**: MySQL job creation failed with "Unknown database 'CDR'" error  
**Status**: ✅ RESOLVED

## Problem
When creating a job with MySQL as target database, the system generated:
```sql
CREATE TABLE CDR.DIM_ACNT_LN2 (...)
```

MySQL interpreted `CDR` as a database name and failed with:
```
Error 1049 (42000): Unknown database 'CDR'
```

## Root Cause
- **MySQL**: Schema and Database are synonymous (no separate schema concept)
- Connection already selects a database via `database=dbsrvnm` parameter
- Prefixing table names with schema/database name causes error
- Unlike PostgreSQL/MSSQL/Oracle, MySQL cannot reference schemas within a database

## Solution
Modified [backend/modules/common/db_adapter/mysql_adapter.py](backend/modules/common/db_adapter/mysql_adapter.py):

```python
def format_table_ref(self, schema: Optional[str], table: str) -> str:
    """
    MySQL uses database-level connections, so schema is the database name.
    Since the connection already selects the database, we only use table name
    in DDL statements (CREATE/ALTER TABLE).
    """
    return table  # Do NOT prefix with schema/database name
```

## Changes Made
1. ✅ Fixed MySQL adapter to return table name only (no schema prefix)
2. ✅ Verified all other adapters still use correct schema.table format
3. ✅ Created test script [test_adapter_table_ref.py](test_adapter_table_ref.py)
4. ✅ Created analysis document [doc/DB_ADAPTER_SCHEMA_HANDLING_ANALYSIS.md](doc/DB_ADAPTER_SCHEMA_HANDLING_ANALYSIS.md)

## Test Results
```
MYSQL        | CDR             . DIM_ACNT_LN2         => DIM_ACNT_LN2
POSTGRESQL   | analytics       . sales                => "analytics"."sales"
MSSQL        | dbo             . Customers            => dbo.Customers
ORACLE       | HR              . EMPLOYEES            => HR.EMPLOYEES
SYBASE       | guest           . orders               => guest.orders
DB2          | MYSCHEMA        . ORDERS               => MYSCHEMA.ORDERS
REDSHIFT     | public          . events               => public.events
SNOWFLAKE    | sales_schema    . transactions         => sales_schema.transactions
HIVE         | warehouse       . fact_sales           => warehouse.fact_sales
```

## Impact
- **MySQL jobs**: Now correctly generate `CREATE TABLE table_name` without database prefix
- **All other databases**: Continue to use `schema.table` format as expected
- **No breaking changes**: Other database types unaffected

## User Guidance
When creating MySQL jobs:
- Ensure target schema (`trgschm`) matches database name in connection (`dbsrvnm`)
- Or leave schema empty to use connection's default database
- MySQL requires connection to specific database; cannot cross-reference databases in DDL

## Related Files
- [backend/modules/common/db_adapter/mysql_adapter.py](backend/modules/common/db_adapter/mysql_adapter.py) - Fixed adapter
- [backend/database/dbconnect.py](backend/database/dbconnect.py) - Connection logic
- [backend/modules/jobs/pkgdwjob_python.py](backend/modules/jobs/pkgdwjob_python.py) - Job execution
- [doc/DB_ADAPTER_SCHEMA_HANDLING_ANALYSIS.md](doc/DB_ADAPTER_SCHEMA_HANDLING_ANALYSIS.md) - Detailed analysis
- [test_adapter_table_ref.py](test_adapter_table_ref.py) - Test script

## Next Steps
✅ Ready for MySQL job creation testing  
✅ No additional changes required for other database types
