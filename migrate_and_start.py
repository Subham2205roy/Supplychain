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
        print(f"Error: {err}")
        
        # Check for "already exists" error
        if "already exists" in err.lower() or "already exists" in out.lower():
            print("Detected 'table already exists' error. Attempting to stamp the database...")
            # We assume the most recent head if it fails at the start
            # But let's try to stamp the base first
            run_command("python -m alembic stamp cd598c0cad46")
            print("Retrying upgrade...")
            ret, out, err = run_command("python -m alembic upgrade head")
            print(out)
            if ret != 0:
                print("Migration still failing, but attempting to start the app anyway...")
        else:
            print("Non-specific migration failure. Starting app anyway...")

    # 2. Start Application
    print("--- Starting Uvicorn ---")
    # Hugging Face Spaces port is usually 7860
    port = os.environ.get("PORT", "7860")
    os.system(f"uvicorn backend.app:app --host 0.0.0.0 --port {port}")

if __name__ == "__main__":
    main()
