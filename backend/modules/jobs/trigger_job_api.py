"""
Script to trigger a job via the API endpoint.
This uses the HTTP API instead of direct database access.
"""
import requests
import json

def trigger_job_via_api(mapref: str, base_url: str = "http://localhost:8000"):
    """Trigger a job via the API endpoint"""
    url = f"{base_url}/job/schedule-job-immediately"
    payload = {
        "mapref": mapref,
        "loadType": "regular",
        "truncateLoad": "N"
    }
    
    try:
        print(f"Calling API: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Success! Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.ConnectionError:
        print(f"✗ Error: Could not connect to {base_url}")
        print("  Make sure the server is running on port 8000")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        try:
            error_detail = response.json()
            print(f"  Details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"  Response: {response.text}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    mapref = "DIM_ACNT_LN2"
    print("=" * 80)
    print(f"Triggering job via API: {mapref}")
    print("=" * 80)
    trigger_job_via_api(mapref)
    print("=" * 80)
    print("\nThe job has been queued. The scheduler will pick it up and execute it.")
    print("You can monitor the execution in:")
    print("  - Application logs")
    print("  - DMS_PRCLOG table")
    print("  - DMS_JOBSCH table (LST_RUN_DT and NXT_RUN_DT should be updated after completion)")

