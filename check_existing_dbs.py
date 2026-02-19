#!/usr/bin/env python
"""Check what databases already exist"""

import sys
sys.path.insert(0, 'D:/DMS/DMSTOOL')

from backend.database.dbconnect import create_metadata_connection

try:
    print("="*60)
    print("Checking existing databases in DMS_SUPPORTED_DATABASES")
    print("="*60)
    
    conn = create_metadata_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DBTYP, DBDESC, STATUS FROM DMS_SUPPORTED_DATABASES ORDER BY DBTYP")
    
    rows = cursor.fetchall()
    print(f"\nFound {len(rows)} databases:\n")
    
    for row in rows:
        print(f"  {row[0]:20} - {row[1]:40} [{row[2]}]")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
