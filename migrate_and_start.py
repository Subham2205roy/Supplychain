import subprocess
import sys
import os
import time

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def main():
    print("--- Starting Migration & Startup Sequence ---")
    
    # 1. Attempt Migration
    ret, out, err = run_command("python -m alembic upgrade head")
    print(out)
    
    if ret != 0:
        print(f"Migration failed with exit code {ret}")
        print(f"Executing forced DB sync via Base.metadata.create_all...")
        
        # Fallback to direct SQLAlchemy creation
        ret_force, out_force, err_force = run_command("python force_db_sync.py")
        print(out_force)
        
        if ret_force == 0:
            print("Forced creation successful. Stamping migration head...")
            run_command("python -m alembic stamp head")
        else:
            print(f"Forced creation failed: {err_force}")
    else:
        print("Migration successful.")

    # 2. Start Application
    print("--- Starting Uvicorn ---")
    # Force port 8000 as requested
    port = "8000"
    print(f"Starting server on http://127.0.0.1:{port}...")
    os.system(f"uvicorn backend.app:app --host 127.0.0.1 --port {port}")

if __name__ == "__main__":
    main()
