"""
Entry point for running the FastAPI application.
"""

import os
import uvicorn

def run_api(port: int = 8000, reload: bool = True):
    """Run the FastAPI application"""
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    run_api()