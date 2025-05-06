"""
Configuration file for QUAST paths and settings
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Path to QUAST installation
QUAST_DIR = PROJECT_ROOT / "tools" / "quast"
QUAST_EXECUTABLE = QUAST_DIR / "quast.py"

# Convert to strings for easier use
QUAST_DIR_STR = str(QUAST_DIR)
QUAST_EXECUTABLE_STR = str(QUAST_EXECUTABLE)

# Get WSL path to QUAST executable
def get_wsl_quast_path():
    from .wsl_path_converter import convert_windows_to_wsl_path
    return convert_windows_to_wsl_path(QUAST_EXECUTABLE_STR)