"""
Quick diagnostic script to verify schema configuration is loaded
Run this to check if environment variables are being read correctly
"""

import os
import sys
import dotenv

# Load .env file
dotenv.load_dotenv()

print("=" * 80)
print("SCHEMA CONFIGURATION DIAGNOSTIC")
print("=" * 80)

# Check current working directory
print(f"\nCurrent Directory: {os.getcwd()}")

# Check if .env file exists
env_file_path = os.path.join(os.getcwd(), '.env')
print(f".env file exists: {os.path.exists(env_file_path)}")

if os.path.exists(env_file_path):
    print(f".env file location: {env_file_path}")
    # Show relevant lines from .env (without passwords)
    print("\nRelevant .env contents:")
    with open(env_file_path, 'r') as f:
        for line in f:
            if 'SCHEMA' in line and not 'PASSWORD' in line and not line.strip().startswith('#'):
                print(f"  {line.strip()}")

print("\n" + "=" * 80)
print("ENVIRONMENT VARIABLES")
print("=" * 80)

# Check all schema-related environment variables
print(f"\nDWT_SCHEMA: '{os.getenv('DWT_SCHEMA', 'NOT SET')}'")
print(f"CDR_SCHEMA: '{os.getenv('CDR_SCHEMA', 'NOT SET')}'")
print(f"SCHEMA (legacy): '{os.getenv('SCHEMA', 'NOT SET')}'")

# Calculate prefixes
DWT_SCHEMA = os.getenv("DWT_SCHEMA", "")
CDR_SCHEMA = os.getenv("CDR_SCHEMA", "")

# Backward compatibility
if not DWT_SCHEMA and os.getenv("SCHEMA"):
    DWT_SCHEMA = os.getenv("SCHEMA")
    print(f"\n⚠️ Using legacy SCHEMA variable as DWT_SCHEMA")

DWT_SCHEMA_PREFIX = f"{DWT_SCHEMA}." if DWT_SCHEMA else ""
CDR_SCHEMA_PREFIX = f"{CDR_SCHEMA}." if CDR_SCHEMA else ""

print("\n" + "=" * 80)
print("CALCULATED PREFIXES")
print("=" * 80)

print(f"\nDWT_SCHEMA_PREFIX: '{DWT_SCHEMA_PREFIX}'")
print(f"CDR_SCHEMA_PREFIX: '{CDR_SCHEMA_PREFIX}'")

# Show what SQL will look like
print("\n" + "=" * 80)
print("EXAMPLE SQL GENERATION")
print("=" * 80)

print(f"\nMetadata table reference:")
print(f"  FROM {{DWT_SCHEMA_PREFIX}}dwmapr")
print(f"  Becomes: FROM {DWT_SCHEMA_PREFIX}dwmapr")

print(f"\nSequence reference:")
print(f"  {{DWT_SCHEMA_PREFIX}}DWMAPRSEQ.nextval")
print(f"  Becomes: {DWT_SCHEMA_PREFIX}DWMAPRSEQ.nextval")

if not DWT_SCHEMA:
    print("\n" + "=" * 80)
    print("⚠️  WARNING: DWT_SCHEMA IS NOT SET!")
    print("=" * 80)
    print("\nThis means:")
    print("  - No schema prefix will be applied")
    print("  - Tables must be in your connected user's schema")
    print("  - OR you need to set DWT_SCHEMA in .env file")
    print("\nTo fix:")
    print("  1. Add to .env: DWT_SCHEMA=DWT")
    print("  2. Restart the application")
else:
    print("\n" + "=" * 80)
    print("✓ Configuration looks good!")
    print("=" * 80)

# Now test database connection if possible
print("\n" + "=" * 80)
print("DATABASE CONNECTION TEST")
print("=" * 80)

try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from database.dbconnect import create_db_connection
    
    print("\nAttempting database connection...")
    conn = create_db_connection()
    print("✓ Database connection successful")
    
    # Test accessing DWT schema table
    cursor = conn.cursor()
    
    print(f"\nTesting access to: {DWT_SCHEMA_PREFIX}dwmapr")
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {DWT_SCHEMA_PREFIX}dwmapr")
        count = cursor.fetchone()[0]
        print(f"✓ Table accessible! Row count: {count}")
    except Exception as e:
        print(f"✗ Error accessing table: {str(e)}")
        
        # Suggest fixes
        print("\nPossible issues:")
        if "ORA-00942" in str(e):
            print("  1. Table doesn't exist in specified schema")
            print("  2. No permission to access the table")
            print("  3. Schema name is incorrect")
            print("\nVerify in Oracle:")
            print(f"  SELECT * FROM all_tables WHERE table_name = 'DWMAPR';")
            if DWT_SCHEMA:
                print(f"  GRANT SELECT ON {DWT_SCHEMA}.dwmapr TO <your_user>;")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Database connection failed: {str(e)}")

print("\n" + "=" * 80)
print("END OF DIAGNOSTIC")
print("=" * 80)

