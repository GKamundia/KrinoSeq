#!/usr/bin/env python
"""
Main entry point for the genome filtering application.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.api.run import run_api

if __name__ == "__main__":
    # For deployment, don't use reload
    reload = os.environ.get("ENVIRONMENT", "development") == "development"
    run_api(reload=reload)
