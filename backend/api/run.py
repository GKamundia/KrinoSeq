"""
Entry point for running the FastAPI application.
"""

import os
import uvicorn

def run_api(port: int = None, reload: bool = True):
    """Run the FastAPI application"""
    # Use PORT environment variable if available (for deployment)
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    run_api()