"""
Configuration file for QUAST paths and settings with cross-platform support
"""

import os
from pathlib import Path
from typing import Optional

from .platform_detector import requires_wsl, get_platform, PlatformType
from .cross_platform_executor import get_command_path, check_command_exists

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default QUAST installation paths for different platforms
DEFAULT_QUAST_PATHS = {
    PlatformType.WINDOWS: PROJECT_ROOT / "tools" / "quast" / "quast.py",
    PlatformType.MACOS: "quast.py",  # Assume it's in PATH on macOS
    PlatformType.LINUX: "quast.py",  # Assume it's in PATH on Linux
}


def get_quast_executable() -> str:
    """
    Get the QUAST executable path for the current platform.
    
    Returns:
        Path to QUAST executable
    """
    platform = get_platform()
    
    # Try to find QUAST in the system PATH first
    if check_command_exists("quast.py"):
        quast_path = get_command_path("quast.py")
        if quast_path:
            return quast_path
    
    # Fallback to platform-specific defaults
    default_path = DEFAULT_QUAST_PATHS.get(platform, "quast.py")
    
    if isinstance(default_path, Path):
        return str(default_path)
    else:
        return default_path


def get_quast_command() -> str:
    """
    Get the QUAST command for the current platform.
    On some systems, it might be 'quast' instead of 'quast.py'.
    
    Returns:
        QUAST command string
    """
    # Try different common QUAST command variations
    commands_to_try = ["quast.py", "quast"]
    
    for cmd in commands_to_try:
        if check_command_exists(cmd):
            return cmd
    
    # Fallback to quast.py
    return "quast.py"


def get_wsl_quast_path() -> str:
    """
    Get WSL path to QUAST executable (for backward compatibility).
    On non-Windows platforms, returns the native path.
    
    Returns:
        Path to QUAST executable appropriate for the current platform
    """
    if requires_wsl():
        from .wsl_path_converter import convert_windows_to_wsl_path
        return convert_windows_to_wsl_path(get_quast_executable())
    else:
        return get_quast_executable()


def validate_quast_installation() -> dict:
    """
    Validate QUAST installation on the current platform.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "platform": get_platform().value,
        "requires_wsl": requires_wsl(),
        "quast_command": None,
        "quast_path": None,
        "is_available": False,
        "version": None,
        "error": None
    }
    
    try:
        # Check if QUAST command exists
        quast_cmd = get_quast_command()
        results["quast_command"] = quast_cmd
        
        if check_command_exists(quast_cmd):
            results["is_available"] = True
            results["quast_path"] = get_command_path(quast_cmd)
            
            # Try to get version information
            try:
                from .cross_platform_executor import run_command
                stdout, stderr, returncode = run_command(
                    f"{quast_cmd} --version",
                    timeout=30,
                    check=False
                )
                if returncode == 0 and stdout.strip():
                    results["version"] = stdout.strip()
            except Exception as e:
                results["error"] = f"Could not get QUAST version: {str(e)}"
        else:
            results["error"] = f"QUAST command '{quast_cmd}' not found in PATH"
            
    except Exception as e:
        results["error"] = f"Error validating QUAST installation: {str(e)}"
    
    return results


def get_installation_instructions() -> str:
    """
    Get platform-specific QUAST installation instructions.
    
    Returns:
        String with installation instructions
    """
    platform = get_platform()
    
    if platform == PlatformType.WINDOWS:
        return """
QUAST Installation on Windows:
1. Install WSL2 with Ubuntu: wsl --install
2. Open WSL terminal and install QUAST:
   pip install quast
   OR
   conda install -c bioconda quast
3. Verify installation: quast.py --version
"""
    elif platform == PlatformType.MACOS:
        return """
QUAST Installation on macOS:
1. Using pip: pip install quast
2. Using conda: conda install -c bioconda quast
3. Using Homebrew: brew install quast
4. Verify installation: quast.py --version

If you encounter issues, you might need to install dependencies:
brew install python3 matplotlib
"""
    elif platform == PlatformType.LINUX:
        return """
QUAST Installation on Linux:
1. Using pip: pip install quast
2. Using conda: conda install -c bioconda quast
3. Using apt (Ubuntu/Debian): sudo apt install quast
4. Verify installation: quast.py --version

You might need to install Python and pip first:
sudo apt update
sudo apt install python3 python3-pip
"""
    else:
        return "Please install QUAST manually and ensure it's available in your PATH."