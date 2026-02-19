"""
Diagnostic script to check MySQL job execution flow
"""
import sys
import os
sys.path.insert(0, 'd:/DMS/DMSTOOL')

os.environ['DMS_SCHEMA'] = 'TRG'  # Change this to your metadata schema

try:
    from backend.database.dbconnect import create_metadata_connection
except ImportError:
    from database.dbconnect import create_metadata_connection

print("=" * 80)
print("MySQL Job Diagnostic Checks")
print("=" * 80)

try:
    conn = create_metadata_connection()
    cursor = conn.cursor()
    
    # Check job configuration
    print("\n1. Job Configuration:")
    print("-" * 80)
    
    # Try Oracle syntax first
    try:
        cursor.execute("""
            SELECT j.jobid, j.mapref, j.trgschm, j.trgtbnm, j.trgtbtyp,
                   j.blkprcrows,
                   jf.sqlconid as source_conn_id, 
                   jf.trgconid as target_conn_id
            FROM DMS_JOB j
            LEFT JOIN DMS_JOBFLW jf ON j.mapref = jf.mapref AND jf.curflg = 'Y'
            WHERE j.mapref = :mapref
              AND j.curflg = 'Y'
        """, {'mapref': 'MYSQL_DIM_ACNT_LN2'})
    except:
        # Try PostgreSQL syntax
        cursor.execute("""
            SELECT j.jobid, j.mapref, j.trgschm, j.trgtbnm, j.trgtbtyp,
                   j.blkprcrows,
                   jf.sqlconid as source_conn_id, 
                   jf.trgconid as target_conn_id
            FROM dms_job j
            LEFT JOIN dms_jobflw jf ON j.mapref = jf.mapref AND jf.curflg = 'Y'
            WHERE j.mapref = %s
              AND j.curflg = 'Y'
        """, ('MYSQL_DIM_ACNT_LN2',))
    
    job_row = cursor.fetchone()
    if job_row:
        print(f"  Job ID: {job_row[0]}")
        print(f"  Mapref: {job_row[1]}")
        print(f"  Target Schema: {job_row[2]}")
        print(f"  Target Table: {job_row[3]}")
        print(f"  Table Type: {job_row[4]}")
        print(f"  Bulk Process Rows: {job_row[5]}")
        print(f"  Source Connection ID (SQLCONID): {job_row[6]} (Oracle)")
        print(f"  Target Connection ID (TRGCONID): {job_row[7]} (MySQL)")
        
        # Verify meta connection details
        print(f"\n  Metadata Connection: PostgreSQL (current connection)")
        
        if job_row[6] is None:
            print("\n  ⚠ WARNING: Source Connection ID (SQLCONID) is NULL!")
            print("     Job will fail - must have separate Oracle source connection")
        if job_row[7] is None:
            print("\n  ⚠ WARNING: Target Connection ID (TRGCONID) is NULL!")
            print("     Job will use metadata connection instead of MySQL - WRONG!")
    else:
        print("  ✗ Job configuration not found!")
    
    # Check recent execution logs
    print("\n2. Recent Execution Logs (Last 3 runs):")
    print("-" * 80)
    
    try:
        cursor.execute("""
            SELECT prcid, srcrows, trgrows, stflg, 
                   SUBSTR(ermsg, 1, 100) as error_snippet,
                   TO_CHAR(reccrdt, 'YYYY-MM-DD HH24:MI:SS') as run_time
            FROM DMS_PRCLOG
            WHERE mapref = :mapref
            ORDER BY reccrdt DESC
            FETCH FIRST 3 ROWS ONLY
        """, {'mapref': 'MYSQL_DIM_ACNT_LN2'})
    except:
        cursor.execute("""
            SELECT prcid, srcrows, trgrows, stflg, 
                   SUBSTRING(ermsg, 1, 100) as error_snippet,
                   reccrdt as run_time
            FROM dms_prclog
            WHERE mapref = %s
            ORDER BY reccrdt DESC
            LIMIT 3
        """, ('MYSQL_DIM_ACNT_LN2',))
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  Run: {row[5]}")
            print(f"    PrcID: {row[0]}")
            print(f"    Source Rows: {row[1] if row[1] is not None else 'NULL'}")
            print(f"    Target Rows: {row[2] if row[2] is not None else 'NULL'}")
            print(f"    Status: {row[3]}")
            if row[4]:
                print(f"    Error: {row[4]}")
            print()
    else:
        print("  No execution logs found")
    
    # Check connection details
    print("\n3. Connection Details:")
    print("-" * 80)
    
    if job_row:
        source_conn_id = job_row[6]
        target_conn_id = job_row[7]
        
        if source_conn_id:
            try:
                cursor.execute("""
                    SELECT dbtyp, dbnam, dbhost, dbport 
                    FROM dms_dbcondtls 
                    WHERE conid = %s AND curflg = 'Y'
                """, (source_conn_id,))
            except:
                cursor.execute("""
                    SELECT dbtyp, dbnam, dbhost, dbport 
                    FROM DMS_DBCONDTLS 
                    WHERE conid = :conid AND curflg = 'Y'
                """, {'conid': source_conn_id})
            
            src_details = cursor.fetchone()
            if src_details:
                print(f"  Source Connection (ID {source_conn_id}):")
                print(f"    DB Type: {src_details[0]}")
                print(f"    DB Name: {src_details[1]}")
                print(f"    Host: {src_details[2]}:{src_details[3]}")
                if src_details[0] != 'ORACLE':
                    print(f"    ⚠ WARNING: Source should be ORACLE, but is {src_details[0]}")
            else:
                print(f"  ✗ Source connection {source_conn_id} not found in DMS_DBCONDTLS!")
        else:
            print("  ✗ No source connection ID configured!")
        
        if target_conn_id:
            try:
                cursor.execute("""
                    SELECT dbtyp, dbnam, dbhost, dbport 
                    FROM dms_dbcondtls 
                    WHERE conid = %s AND curflg = 'Y'
                """, (target_conn_id,))
            except:
                cursor.execute("""
                    SELECT dbtyp, dbnam, dbhost, dbport 
                    FROM DMS_DBCONDTLS 
                    WHERE conid = :conid AND curflg = 'Y'
                """, {'conid': target_conn_id})
            
            tgt_details = cursor.fetchone()
            if tgt_details:
                print(f"\n  Target Connection (ID {target_conn_id}):")
                print(f"    DB Type: {tgt_details[0]}")
                print(f"    DB Name: {tgt_details[1]}")
                print(f"    Host: {tgt_details[2]}:{tgt_details[3]}")
                if tgt_details[0] != 'MYSQL':
                    print(f"    ⚠ WARNING: Target should be MYSQL, but is {tgt_details[0]}")
            else:
                print(f"  ✗ Target connection {target_conn_id} not found in DMS_DBCONDTLS!")
        else:
            print("  ✗ No target connection ID configured!")
    
    # Check source data availability
    print("\n4. Source Table Check:")
    print("-" * 80)
    
    if job_row and job_row[6]:  # If source connection ID exists
        try:
            from backend.database.dbconnect import create_target_connection
            source_conn = create_target_connection(job_row[6])
            source_cursor = source_conn.cursor()
            
            # Try to count source records
            source_cursor.execute("""
                SELECT COUNT(*) FROM stg.ln_acct_dtls WHERE flg_mnt_status = 'A'
            """)
            count = source_cursor.fetchone()[0]
            print(f"  ✓ Source table accessible: {count} rows with flg_mnt_status='A'")
            
            source_cursor.close()
            source_conn.close()
        except Exception as e:
            print(f"  ✗ Source table check failed: {e}")
    else:
        print("  ⚠ No source connection ID configured")
    
    # Check target table
    print("\n5. Target Table Check:")
    print("-" * 80)
    
    if job_row and job_row[7]:  # If target connection ID exists
        try:
            from backend.database.dbconnect import create_target_connection
            target_conn = create_target_connection(job_row[7])
            target_cursor = target_conn.cursor()
            
            # Try to count target records
            target_cursor.execute(f"SELECT COUNT(*) FROM {job_row[3]} LIMIT 1")
            count = target_cursor.fetchone()[0]
            print(f"  ✓ Target table accessible: {count} rows currently")
            
            target_cursor.close()
            target_conn.close()
        except Exception as e:
            print(f"  ✗ Target table check failed: {e}")
    else:
        print("  ⚠ No target connection ID configured")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("Connection Architecture Validation")
    print("=" * 80)
    
    if job_row:
        print("\nExpected 3-Connection Setup:")
        print("  1. Metadata Connection: PostgreSQL (✓ currently connected)")
        print(f"  2. Source Connection (SQLCONID {job_row[6]}): Oracle - for SELECT queries")
        print(f"  3. Target Connection (TRGCONID {job_row[7]}): MySQL - for INSERT/UPDATE/TRUNCATE")
        
        if job_row[6] is None or job_row[7] is None:
            print("\n✗ CONNECTION CONFIGURATION ERROR:")
            if job_row[6] is None:
                print("  - Missing Source Connection ID (SQLCONID)")
            if job_row[7] is None:
                print("  - Missing Target Connection ID (TRGCONID)")
            print("\nAction Required: Configure both SQLCONID and TRGCONID in DMS_JOBFLW table")
        else:
            print("\n✓ Job flow has all required connection IDs configured")
    
    print("\n" + "=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Diagnostic failed: {e}")
    import traceback
    traceback.print_exc()
