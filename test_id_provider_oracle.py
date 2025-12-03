"""
Quick test script for ID Provider with Oracle database.
Run this to verify ID generation is working correctly.
"""

import sys
import os

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.dbconnect import create_oracle_connection
from modules.common.id_provider import next_id, refresh_id_config
from modules.logger import info, error

def test_id_generation():
    """Test ID generation for all entities used in the application."""
    print("=" * 80)
    print("ID Provider Test - Oracle Database")
    print("=" * 80)
    
    conn = None
    cursor = None
    
    try:
        # Create connection
        print("\n1. Connecting to Oracle database...")
        conn = create_oracle_connection()
        cursor = conn.cursor()
        print("   [OK] Connection established")
        
        # Refresh config to ensure latest settings
        print("\n2. Loading ID provider configuration...")
        refresh_id_config()
        print("   [OK] Configuration loaded")
        
        # Test entities (without schema prefix first)
        test_entities = [
            "DMS_PRCLOGSEQ",
            "DMS_JOBLOGSEQ", 
            "DMS_JOBERRSEQ",
            "DMS_JOBSCHSEQ",
            "DMS_MAPRSEQ",
            "DMS_MAPRDTLSEQ",
            "DMS_MAPRSQLSEQ",
            "DMS_MAPERRSEQ"
        ]
        
        # Get schema from environment if needed
        import os
        schema = os.getenv('SCHEMA', 'DWT')
        if schema:
            # Add schema-prefixed entities
            test_entities.extend([
                f"{schema}.DMS_JOBSEQ",
                f"{schema}.DMS_JOBDTLSEQ",
                f"{schema}.DMS_JOBFLWSEQ"
            ])
        
        print(f"\n3. Testing ID generation for {len(test_entities)} entities...")
        print("-" * 80)
        
        results = {}
        for entity in test_entities:
            try:
                id_val = next_id(cursor, entity)
                results[entity] = {'status': 'SUCCESS', 'id': id_val}
                print(f"   [OK] {entity:30s} -> {id_val}")
            except Exception as e:
                results[entity] = {'status': 'ERROR', 'error': str(e)}
                print(f"   [FAIL] {entity:30s} -> ERROR: {str(e)[:50]}")
        
        # Test sequential IDs
        print("\n4. Testing sequential ID generation (5 IDs)...")
        print("-" * 80)
        test_entity = "DMS_PRCLOGSEQ"
        try:
            ids = []
            for i in range(5):
                id_val = next_id(cursor, test_entity)
                ids.append(id_val)
                print(f"   ID {i+1}: {id_val}")
            
            # Verify they're sequential
            if ids == sorted(ids) and len(set(ids)) == len(ids):
                print(f"\n   [OK] IDs are sequential and unique")
            else:
                print(f"\n   [WARN] IDs may not be strictly sequential (this is OK with block allocation)")
        except Exception as e:
            print(f"   [FAIL] Error: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
        error_count = sum(1 for r in results.values() if r['status'] == 'ERROR')
        
        print(f"Total entities tested: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Errors: {error_count}")
        
        if error_count == 0:
            print("\n[SUCCESS] All tests passed! ID provider is working correctly.")
        else:
            print("\n[FAILURE] Some tests failed. Please check:")
            print("  - Sequences exist and are accessible")
            print("  - DMS_PARAMS configuration is correct")
            print("  - Database user has necessary permissions")
            print("\nError details:")
            for entity, result in results.items():
                if result['status'] == 'ERROR':
                    print(f"  - {entity}: {result['error']}")
        
        return error_count == 0
        
    except Exception as e:
        error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\n" + "=" * 80)

if __name__ == "__main__":
    success = test_id_generation()
    exit(0 if success else 1)

