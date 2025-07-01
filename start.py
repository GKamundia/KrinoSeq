#!/usr/bin/env python
"""
Simple start script for Railway deployment.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set environment variable for production
os.environ.setdefault("ENVIRONMENT", "production")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    # Import after setting up the path
    try:
        from backend.api.main import app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Trying alternative import method...")
        uvicorn.run(
            "backend.api.main:app",
            host="0.0.0.0",
            port=port,
            reload=False
        )
