#!/usr/bin/env python
"""
Comprehensive test of the database wizard flow
Tests: add database + clone datatypes
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_datatype_suggestions(target_dbtype):
    """Test getting datatype suggestions"""
    print(f"\n{'='*60}")
    print(f"Step 1: Get datatype suggestions for {target_dbtype}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mapping/datatype_suggestions",
            params={
                'target_dbtype': target_dbtype,
                'based_on_usage': True
            },
            json={},
            headers={'Content-Type': 'application/json', 'X-User': 'testuser'}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Got {data.get('suggestion_count', 0)} suggestions")
            return True
        else:
            print(f"✗ Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_add_database(dbtype, dbdesc):
    """Test adding a new database type"""
    print(f"\n{'='*60}")
    print(f"Step 2: Add new database {dbtype}")
    print('='*60)
    
    payload = {
        "DBTYP": dbtype,
        "DBDESC": dbdesc
    }
    
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mapping/supported_database_add",
            json=payload,
            headers={'Content-Type': 'application/json', 'X-User': 'testuser'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}")
        
        if response.status_code == 200:
            print(f"✓ Database added successfully")
            return True
        else:
            print(f"✗ Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_clone_datatypes(target_dbtype):
    """Test cloning datatypes"""
    print(f"\n{'='*60}")
    print(f"Step 3: Clone datatypes for {target_dbtype}")
    print('='*60)
    
    payload = {
        "TARGET_DBTYPE": target_dbtype
    }
    
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mapping/clone_datatypes_from_generic",
            json=payload,
            headers={'Content-Type': 'application/json', 'X-User': 'testuser'}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Cloned {data.get('created_count', 0)} datatypes")
            return True
        else:
            print(f"✗ Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

# Main test
if __name__ == "__main__":
    print("\n" + "*"*60)
    print("DATABASE WIZARD FLOW TEST")
    print("*"*60)
    
    # Test with a unique database name
    test_db = f"WIZTEST{int(time.time()) % 10000}"
    test_desc = "Database Wizard Test"
    
    print(f"\nTest plan:")
    print(f"  1. Get suggestions for ORACLE (existing db)")
    print(f"  2. Add new database: {test_db} ")
    print(f"  3. Clone datatypes for: {test_db}")
    
    # Step 1: Get suggestions for Oracle
    success1 = test_datatype_suggestions("ORACLE")
    
    # Step 2: Add new database
    success2 = test_add_database(test_db, test_desc)
    
    # Step 3: Clone datatypes if step 2 succeeded
    success3 = False
    if success2:
        success3 = test_clone_datatypes(test_db)
    
    # Summary
    print(f"\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"1. Get suggestions for ORACLE:      {'✓ PASS' if success1 else '✗ FAIL'}")
    print(f"2. Add database {test_db:15} {'✓ PASS' if success2 else '✗ FAIL'}")
    print(f"3. Clone datatypes:                 {'✓ PASS' if success3 else '✗ FAIL'}")
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all([success1, success2, success3]) else '✗ SOME TESTS FAILED'}")
    print("="*60)
