"""
Script to regenerate job flow for MySQL job after mapper fixes
"""
import sys
import os
sys.path.insert(0, 'd:/DMS/DMSTOOL')

# Set up environment
os.environ['DMS_SCHEMA'] = 'TRG'  # Change this to your metadata schema

try:
    from backend.database.dbconnect import create_metadata_connection
    from backend.modules.jobs.pkgdwjob_python import create_job_flow
except ImportError:
    from database.dbconnect import create_metadata_connection
    from modules.jobs.pkgdwjob_python import create_job_flow

mapref = 'MYSQL_DIM_ACNT_LN2'

print(f"Regenerating job flow for {mapref}...")
print("=" * 70)

try:
    # Create metadata connection
    conn = create_metadata_connection()
    
    # Regenerate job flow
    create_job_flow(conn, mapref)
    
    # Commit changes
    conn.commit()
    
    print("\n" + "=" * 70)
    print(f"✓ Job flow regenerated successfully for {mapref}")
    print("=" * 70)
    print("\nThe job will now:")
    print("  - Use `DIM_ACNT_LN2` (no schema prefix) in INSERT statements")
    print("  - Work correctly with MySQL database connections")
    print("\nNext steps:")
    print("  1. Run the job again from the UI")
    print("  2. Verify data is loaded into CDR.DIM_ACNT_LN2")
    
    conn.close()
    
except Exception as e:
    print(f"\n✗ Error regenerating job flow: {e}")
    import traceback
    traceback.print_exc()
