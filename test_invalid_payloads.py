#!/usr/bin/env python
"""Test endpoint with various invalid payloads"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "Valid request",
        "payload": {
            "DBTYP": "VALIDTEST",
            "DBDESC": "Valid test database"
        },
        "should_fail": False
    },
    {
        "name": "Missing DBDESC",
        "payload": {
            "DBTYP": "NODESCC"
        },
        "should_fail": True
    },
    {
        "name": "Missing DBTYP",
        "payload": {
            "DBDESC": "Description only"
        },
        "should_fail": True
    },
    {
        "name": "Empty DBTYP",
        "payload": {
            "DBTYP": "",
            "DBDESC": "Desc"
        },
        "should_fail": True
    },
    {
        "name": "Empty DBDESC",
        "payload": {
            "DBTYP": "EMPTYDES",
            "DBDESC": ""
        },
        "should_fail": True
    },
    {
        "name": "NULL in payload",
        "payload": {
            "DBTYP": None,
            "DBDESC": "Desc"
        },
        "should_fail": True
    }
]

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"Test: {test['name']}")
    print(f"Expected: {'SHOULD FAIL' if test['should_fail'] else 'SHOULD SUCCEED'}")
    print(f"Payload: {json.dumps(test['payload'], indent=2)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/mapping/supported_database_add",
            json=test['payload'],
            headers={
                "Content-Type": "application/json",
                "X-User": "testuser"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if test['should_fail']:
            if response.status_code >= 400:
                print(f"✓ Got expected failure status {response.status_code}")
            else:
                print(f"✗ Expected failure but got {response.status_code}")
        else:
            if response.status_code == 200:
                print(f"✓ Got expected success")
            else:
                print(f"✗ Expected success but got {response.status_code}")
                
    except Exception as e:
        print(f"✗ Exception: {e}")

print("\n" + "="*60)
