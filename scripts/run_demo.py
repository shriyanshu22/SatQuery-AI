from __future__ import annotations

import os
import subprocess
import sys

"""
Script to run the SatQuery AI backend in demo mode.

This script sets the necessary environment variables to enable demo mode,
which uses mock or cached models instead of requiring a GPU. It then starts
the FastAPI server using Uvicorn.
"""

def main() -> None:
    """
    Sets environment variables and starts the application in demo mode.
    """
    print("Starting SatQuery AI in DEMO MODE...")
    print("This mode uses mock/cached models. No GPU required.")
    
    # Set environment variables for demo mode
    os.environ["SATQUERY_DEMO_MODE"] = "true"
    os.environ["SATQUERY_MODEL_BACKEND"] = "mock"
    os.environ["SATQUERY_DEBUG"] = "true"
    
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Demo Endpoint: http://localhost:8000/api/v1/demo\n")
    
    try:
        # We assume uvicorn is installed and backend/api/main.py exists.
        # This will fail if the structure isn't entirely set up, but serves as the entrypoint.
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "backend.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            check=True
        )
    except KeyboardInterrupt:
        print("\nDemo server stopped.")
    except Exception as e:
        print(f"\nFailed to start demo server: {e}")
        print("Please ensure you have installed dependencies and the backend is correctly structured.")

if __name__ == "__main__":
    main()
