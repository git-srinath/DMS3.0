#!/usr/bin/env python
"""Test script to debug 400 error when adding duplicate database"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

print("="*60)
print("Testing supported_database_add with duplicate database")
print("="*60)

# First, try to add a new database
print("\n1. Adding a NEW database...")
payload_new = {
    "DBTYP": f"NEWDB{__import__('time').time_ns() % 10000}",
    "DBDESC": "Test New Database"
}

print(f"Payload: {json.dumps(payload_new, indent=2)}")

try:
    response = requests.post(
        f"{API_BASE_URL}/mapping/supported_database_add",
        json=payload_new,
        headers={
            "Content-Type": "application/json",
            "X-User": "testuser"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    dbtype_added = None
    if response.status_code == 200:
        dbtype_added = response.json().get('DBTYP')
        print(f"✓ Successfully added {dbtype_added}")
except Exception as e:
    print(f"✗ Error: {e}")
    dbtype_added = None

# Now try to add the SAME database again
if dbtype_added:
    print(f"\n2. Attempting to add the SAME database again (should get 400)...")
    payload_dup = {
        "DBTYP": dbtype_added,
        "DBDESC": "Duplicate Description"
    }
    
    print(f"Payload: {json.dumps(payload_dup, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mapping/supported_database_add",
            json=payload_dup,
            headers={
                "Content-Type": "application/json",
                "X-User": "testuser"
            }
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print(f"✓ Got expected 400 error for duplicate database")
        else:
            print(f"✗ Expected 400 but got {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*60)
