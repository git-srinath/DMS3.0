"""
Script to queue a test job for immediate execution.
This will insert a request into DMS_PRCREQ which the scheduler will pick up and execute.
"""
import sys
import os

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.database.dbconnect import create_metadata_connection
    from backend.modules.jobs.pkgdwprc_python import JobSchedulerService, ImmediateJobRequest
except ImportError:  # When running from backend directory
    from database.dbconnect import create_metadata_connection
    from modules.jobs.pkgdwprc_python import JobSchedulerService, ImmediateJobRequest

def queue_test_job(mapref: str):
    """Queue a job for immediate execution"""
    connection = None
    try:
        print(f"Connecting to metadata database...")
        connection = create_metadata_connection()
        print(f"Connection established successfully")
        
        print(f"Creating JobSchedulerService...")
        service = JobSchedulerService(connection)
        
        print(f"Queueing immediate job for {mapref}...")
        request = ImmediateJobRequest(
            mapref=mapref,
            params={}
        )
        request_id = service.queue_immediate_job(request)
        
        print(f"✓ Successfully queued job {mapref}")
        print(f"  Request ID: {request_id}")
        print(f"  The scheduler will pick up this request and execute it shortly.")
        print(f"  You can monitor the execution in the application logs and DMS_PRCLOG table.")
        return request_id
    except Exception as e:
        print(f"✗ Error queueing job: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if connection:
            connection.close()
            print("Connection closed")

if __name__ == "__main__":
    mapref = "DIM_ACNT_LN2"
    print("=" * 80)
    print(f"Queueing test job: {mapref}")
    print("=" * 80)
    queue_test_job(mapref)
    print("=" * 80)

