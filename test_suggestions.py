#!/usr/bin/env python
"""Check what datatype suggestions are returned"""

import sys
sys.path.insert(0, 'D:/DMS/DMSTOOL')

from backend.database.dbconnect import create_metadata_connection
from backend.modules.helper_functions import get_datatype_suggestions

try:
    print("="*60)
    print("Testing get_datatype_suggestions function")
    print("="*60)
    
    conn = create_metadata_connection()
    print("✓ Connected to metadata database")
    
    for target_db in ["ORACLE", "BASIC", "GENERIC"]:
        print(f"\nFetching suggestions for {target_db}...")
        suggestions = get_datatype_suggestions(conn, target_db, based_on_usage=True)
        print(f"  Got {len(suggestions)} suggestions")
        if suggestions and len(suggestions) > 0:
            print(f"  First suggestion: {suggestions[0]}")
    
    conn.close()
    print("\n✓ Test completed")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
