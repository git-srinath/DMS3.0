#!/usr/bin/env python
"""
Test the complete flow to identify where the 400 error happens
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an endpoint and return response"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        'Content-Type': 'application/json',
        'X-User': 'testuser'
    }
    
    print(f"\n  Method: {method}")
    print(f"  URL: {url}")
    if params:
        print(f"  Params: {params}")
    if data:
        print(f"  Data: {json.dumps(data)}")
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        print(f"  Status: {response.status_code}")
        try:
            resp_json = response.json()
            print(f"  Response: {json.dumps(resp_json, indent=2)[:200]}")
            return response.status_code, resp_json
        except:
            print(f"  Response: {response.text[:200]}")
            return response.status_code, response.text
    except Exception as e:
        print(f"  ERROR: {e}")
        return None, str(e)

print("\n" + "="*60)
print("TESTING ADD DATABASE + CLONE FLOW")
print("="*60)

# Use unique database name
test_db = f"TESTCRE{int(time.time()) % 10000}"
test_desc = "Test Creation Flow"

print(f"\nTest database: {test_db}")
print(f"Test description: {test_desc}")

# Step 1: Test endpoint /mapping/supported_database_add
print("\n" + "-"*60)
print("Step 1: Add supported database")
print("-"*60)

status1, resp1 = test_endpoint(
    "POST",
    "/mapping/supported_database_add",
    data={"DBTYP": test_db, "DBDESC": test_desc}
)

if status1 != 200:
    print(f"\n✗ FAILED at step 1: {status1}")
else:
    print(f"\n✓ Step 1 successful")

    # Step 2: Test endpoint /mapping/clone_datatypes_from_generic
    print("\n" + "-"*60)
    print("Step 2: Clone datatypes from generic")
    print("-"*60)
    
    status2, resp2 = test_endpoint(
        "POST",
        "/mapping/clone_datatypes_from_generic",
        data={"TARGET_DBTYPE": test_db}
    )
    
    if status2 != 200:
        print(f"\n✗ FAILED at step 2: {status2}")
    else:
        print(f"\n✓ Step 2 successful")

print("\n" + "="*60)

# Additional test: Try with missing fields
print("\n" + "="*60)
print("TESTING VALIDATION - MISSING FIELDS")
print("="*60)

print("\nTest 1: Missing DBDESC")
status, resp = test_endpoint(
    "POST",
    "/mapping/supported_database_add",
    data={"DBTYP": "NODESC"}
)
print(f"Result: {status} - {'Expected 422' if status == 422 else f'ERROR: Got {status}'}")

print("\nTest 2: Empty string fields")
status, resp = test_endpoint(
    "POST",
    "/mapping/supported_database_add",
    data={"DBTYP": "", "DBDESC": ""}
)
print(f"Result: {status} - {'Expected 400' if status == 400 else f'ERROR: Got {status}'}")

print("\n" + "="*60)
