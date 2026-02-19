#!/usr/bin/env python
"""Test script to debug datatype_suggestions endpoint"""

import sys
sys.path.insert(0, 'D:/DMS/DMSTOOL')

from backend.database.dbconnect import create_metadata_connection
from backend.modules.helper_functions import get_parameter_mapping_datatype_for_db, get_parameter_mapping_datatype

try:
    print("="*60)
    print("Testing datatype_suggestions endpoint logic")
    print("="*60)
    
    conn = create_metadata_connection()
    print("✓ Connected to metadata database")
    
    target_dbtype = "ORACLE"
    print(f"\nFetching datatypes for {target_dbtype}...")
    
    suggestions = get_parameter_mapping_datatype_for_db(conn, target_dbtype)
    print(f"✓ Got {len(suggestions)} suggestions")
    
    if suggestions:
        print(f"\nFirst suggestion structure:")
        print(f"  {suggestions[0]}")
        print(f"\nKeys in first suggestion: {suggestions[0].keys() if suggestions else 'N/A'}")
    
    print("\n" + "="*60)
    print("Now testing based_on_usage=True path...")
    print("="*60)
    
    # This is what fails - testing the usage filtering logic
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT prcd, prval
            FROM DMS_PARAMS p
            WHERE PRTYP = 'Datatype' AND (DBTYP = %s OR DBTYP = 'GENERIC')
            AND prcd IN (
                SELECT DISTINCT dtyp FROM DMS_MAPDETAIL WHERE dtyp IS NOT NULL
            )
            ORDER BY prval
        """, (target_dbtype,))
        
        usage_rows = cursor.fetchall()
        cursor.close()
        print(f"✓ Query for usage-based filtering returned {len(usage_rows)} rows")
        
        if usage_rows:
            print(f"\nFirst usage row: {usage_rows[0]}")
        
        # Now test the matching logic
        usage_based = []
        for row in usage_rows:
            for sugg in suggestions:
                if sugg.get('PRCD') == row[0]:
                    usage_based.append(sugg)
                    break
        
        print(f"✓ After filtering: {len(usage_based)} suggestions match usage")
        
    except Exception as usage_err:
        print(f"✗ Usage filtering failed (expected if DMS_MAPDETAIL missing):")
        print(f"  {str(usage_err)}")
        print(f"  Will fall back to all suggestions")
    
    conn.close()
    print("\n✓ Test completed successfully")
    
except Exception as e:
    print(f"\n✗ CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
