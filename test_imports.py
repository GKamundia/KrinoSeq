#!/usr/bin/env python3
"""
Test script to verify all required imports work correctly.
"""

def test_imports():
    """Test all critical imports for the genome filtering tool."""
    print("Testing imports...")
    
    try:
        # Core web framework
        import fastapi
        import uvicorn
        print("✓ FastAPI and Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI/Uvicorn import failed: {e}")
        return False
    
    try:
        # Scientific computing
        import numpy as np
        import pandas as pd
        import scipy
        print("✓ NumPy, Pandas, SciPy imported successfully")
    except ImportError as e:
        print(f"✗ Scientific computing imports failed: {e}")
        return False
    
    try:
        # Bioinformatics
        import Bio
        from Bio import SeqIO
        print("✓ BioPython imported successfully")
    except ImportError as e:
        print(f"✗ BioPython import failed: {e}")
        return False
    
    try:
        # Visualization
        import matplotlib
        print("✓ Matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ Matplotlib import failed: {e}")
        return False
    
    try:
        # Machine learning (optional)
        import sklearn
        print("✓ scikit-learn imported successfully")
    except ImportError as e:
        print(f"⚠ scikit-learn import failed (optional): {e}")
    
    try:
        # Test our own modules
        from backend.api.main import app
        print("✓ Main application imported successfully")
    except ImportError as e:
        print(f"✗ Main application import failed: {e}")
        return False
    
    print("\n✅ All critical imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
