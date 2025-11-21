"""
Diagnostic script to test SCHEMA environment variable and sequence accessibility
Run this to diagnose ORA-00942 errors with sequences
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.dbconnect import create_db_connection
from modules.logger import info, error

def test_schema_config():
    """Test SCHEMA environment variable configuration"""
    print("\n" + "="*80)
    print("SCHEMA CONFIGURATION TEST")
    print("="*80)
    
    schema = os.getenv("SCHEMA", "")
    schema_prefix = f"{schema}." if schema else ""
    
    print(f"\n1. SCHEMA environment variable: {repr(schema)}")
    print(f"2. Schema prefix: {repr(schema_prefix)}")
    print(f"3. Sequence reference: {schema_prefix}DWMAPRSEQ.nextval")
    
    if not schema:
        print("\n⚠️  WARNING: SCHEMA environment variable is NOT set")
        print("   If your sequences are in a different schema, you need to set this.")
    else:
        print(f"\n✓ SCHEMA is set to: {schema}")
    
    return schema, schema_prefix


def test_sequence_access(conn, schema_prefix):
    """Test if sequences are accessible"""
    print("\n" + "="*80)
    print("SEQUENCE ACCESSIBILITY TEST")
    print("="*80)
    
    sequences = [
        f"{schema_prefix}DWMAPRSQLSEQ",
        f"{schema_prefix}DWMAPRSEQ",
        f"{schema_prefix}DWMAPRDTLSEQ",
        f"{schema_prefix}DWMAPERRSEQ"
    ]
    
    cursor = conn.cursor()
    
    for seq in sequences:
        try:
            print(f"\nTesting: {seq}")
            cursor.execute(f"SELECT {seq}.nextval FROM dual")
            nextval = cursor.fetchone()[0]
            print(f"  ✓ Accessible - current value: {nextval}")
            
            # Rollback to not consume sequence numbers
            conn.rollback()
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ FAILED - {error_msg}")
            
            if "ORA-00942" in error_msg:
                print(f"    → Sequence does not exist or no permission")
                print(f"    → Check: SELECT * FROM all_sequences WHERE sequence_name = '{seq.split('.')[-1]}'")
            elif "ORA-02289" in error_msg:
                print(f"    → Sequence does not exist")
            
    cursor.close()


def test_table_access(conn):
    """Test if required tables are accessible"""
    print("\n" + "="*80)
    print("TABLE ACCESSIBILITY TEST")
    print("="*80)
    
    tables = ['DWMAPRSQL', 'DWMAPR', 'DWMAPRDTL', 'DWMAPERR']
    
    cursor = conn.cursor()
    
    for table in tables:
        try:
            print(f"\nTesting: {table}")
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ Accessible - {count} rows")
        except Exception as e:
            print(f"  ✗ FAILED - {str(e)}")
    
    cursor.close()


def check_sequence_ownership(conn, schema):
    """Check which schema owns the sequences"""
    print("\n" + "="*80)
    print("SEQUENCE OWNERSHIP CHECK")
    print("="*80)
    
    cursor = conn.cursor()
    
    try:
        # Check current user
        cursor.execute("SELECT USER FROM dual")
        current_user = cursor.fetchone()[0]
        print(f"\nCurrent connected user: {current_user}")
        
        # Check for sequences in all accessible schemas
        print("\nSearching for DWT sequences in all accessible schemas:")
        cursor.execute("""
            SELECT owner, sequence_name 
            FROM all_sequences 
            WHERE sequence_name LIKE 'DW%SEQ'
            ORDER BY owner, sequence_name
        """)
        
        sequences = cursor.fetchall()
        if sequences:
            print(f"\nFound {len(sequences)} sequences:")
            for owner, seq_name in sequences:
                print(f"  {owner}.{seq_name}")
                if owner != current_user:
                    print(f"    → In different schema! You need:")
                    print(f"       - GRANT SELECT ON {owner}.{seq_name} TO {current_user};")
                    print(f"       - OR CREATE SYNONYM {seq_name} FOR {owner}.{seq_name};")
        else:
            print("  ✗ No DWT sequences found in any accessible schema!")
            print("    You may need to create them. See CREATE_SEQUENCES.sql")
        
    except Exception as e:
        print(f"  ✗ Error checking sequences: {str(e)}")
    
    cursor.close()


def main():
    """Run all diagnostic tests"""
    print("\n" + "="*80)
    print("PKGDWMAPR SEQUENCE DIAGNOSTIC TOOL")
    print("="*80)
    
    # Test 1: Schema configuration
    schema, schema_prefix = test_schema_config()
    
    # Test 2: Database connection
    print("\n" + "="*80)
    print("DATABASE CONNECTION TEST")
    print("="*80)
    
    try:
        conn = create_db_connection()
        print("\n✓ Database connection successful")
    except Exception as e:
        print(f"\n✗ Database connection failed: {str(e)}")
        return
    
    # Test 3: Check sequence ownership
    check_sequence_ownership(conn, schema)
    
    # Test 4: Table access
    test_table_access(conn)
    
    # Test 5: Sequence access
    test_sequence_access(conn, schema_prefix)
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    print("\nIf you see ORA-00942 errors above:")
    print("1. Verify the SCHEMA environment variable is correct")
    print("2. Check if sequences exist in the database")
    print("3. Verify you have SELECT permission on the sequences")
    print("4. Consider creating synonyms if sequences are in another schema")
    print("\nSee ORA_00942_SCHEMA_PREFIX_FIX.md for detailed troubleshooting.")
    print("="*80 + "\n")
    
    conn.close()


if __name__ == "__main__":
    main()

