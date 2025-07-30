"""
Platform detection utilities for cross-platform compatibility.
Determines the operating system and provides platform-specific configurations.
"""

import platform
import sys
from typing import Tuple, Optional
from enum import Enum


class PlatformType(Enum):
    """Supported platform types."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


def get_platform() -> PlatformType:
    """
    Detect the current operating system platform.
    
    Returns:
        PlatformType enum value representing the current platform
    """
    system = platform.system().lower()
    
    if system == "windows":
        return PlatformType.WINDOWS
    elif system == "darwin":  # macOS
        return PlatformType.MACOS
    elif system == "linux":
        return PlatformType.LINUX
    else:
        return PlatformType.UNKNOWN


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == PlatformType.WINDOWS


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform() == PlatformType.MACOS


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == PlatformType.LINUX


def is_unix_like() -> bool:
    """Check if running on a Unix-like system (macOS or Linux)."""
    return get_platform() in [PlatformType.MACOS, PlatformType.LINUX]


def requires_wsl() -> bool:
    """
    Determine if WSL is required for this platform.
    WSL is only needed on Windows for running Linux tools.
    
    Returns:
        True if WSL is required, False otherwise
    """
    return is_windows()


def get_platform_info() -> dict:
    """
    Get detailed platform information.
    
    Returns:
        Dictionary containing platform details
    """
    return {
        "platform_type": get_platform().value,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "requires_wsl": requires_wsl(),
        "is_unix_like": is_unix_like()
    }


def get_recommended_setup() -> str:
    """
    Get platform-specific setup recommendations.
    
    Returns:
        String with setup recommendations for the current platform
    """
    platform_type = get_platform()
    
    if platform_type == PlatformType.WINDOWS:
        return """
Windows Setup:
- Install WSL2 with Ubuntu or another Linux distribution
- Install QUAST in the WSL environment: pip install quast
- Ensure WSL is accessible from Windows command line
"""
    elif platform_type == PlatformType.MACOS:
        return """
macOS Setup:
- Install QUAST natively using pip: pip install quast
- Or install via conda: conda install -c bioconda quast
- Or install via Homebrew: brew install quast
- Ensure quast.py is available in your PATH
"""
    elif platform_type == PlatformType.LINUX:
        return """
Linux Setup:
- Install QUAST using pip: pip install quast
- Or install via conda: conda install -c bioconda quast
- Or install via apt (Ubuntu/Debian): sudo apt install quast
- Ensure quast.py is available in your PATH
"""
    else:
        return "Platform not recognized. Please install QUAST manually and ensure it's available in your PATH."