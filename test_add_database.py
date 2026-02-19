#!/usr/bin/env python
"""Test script to debug supported_database_add endpoint"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

print("="*60)
print("Testing supported_database_add endpoint")
print("="*60)

# Test the endpoint
payload = {
    "DBTYP": "TESTDB001",
    "DBDESC": "Test Database for Debugging"
}

print(f"\nSending request to: {API_BASE_URL}/mapping/supported_database_add")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{API_BASE_URL}/mapping/supported_database_add",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-User": "testuser"
        }
    )
    
    print(f"\n✓ Request completed")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print(f"\n✗ ERROR: Got status code {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Could not parse response as JSON")
    
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
