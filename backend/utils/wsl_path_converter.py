"""
Utilities for converting file paths between Windows and WSL formats.
Used primarily for running QUAST and other Linux-based tools via WSL.
"""

import os
import subprocess
from typing import Tuple, Optional


def convert_windows_to_wsl_path(windows_path: str) -> str:
    """
    Convert a Windows path to a WSL-compatible path.
    
    Args:
        windows_path: Windows-style path (e.g., C:\\Users\\name\\file.txt)
        
    Returns:
        WSL-compatible path (e.g., /mnt/c/Users/name/file.txt)
    """
    # Normalize path separators first
    windows_path = os.path.normpath(windows_path)
    
    # Check if path has a drive letter
    if len(windows_path) >= 2 and windows_path[1] == ':':
        # Extract drive letter and convert to lowercase
        drive = windows_path[0].lower()
        # Remove drive letter and colon, replace backslashes
        path = windows_path[2:].replace('\\', '/')
        return f"/mnt/{drive}{path}"
    else:
        # Handle relative paths or UNC paths
        return windows_path.replace('\\', '/')


def convert_wsl_to_windows_path(wsl_path: str) -> str:
    """
    Convert a WSL path to a Windows-compatible path.
    
    Args:
        wsl_path: WSL-style path (e.g., /mnt/c/Users/name/file.txt)
        
    Returns:
        Windows-compatible path (e.g., C:\\Users\\name\\file.txt)
    """
    # Handle /mnt/x/ paths (standard WSL drive mapping)
    if wsl_path.startswith('/mnt/') and len(wsl_path) > 5:
        # Extract drive letter
        drive = wsl_path[5:6].upper()
        # Extract the rest of the path and convert separators
        path = wsl_path[6:].replace('/', '\\')
        return f"{drive}:{path}"
    else:
        # For non-standard paths, just replace separators
        # This won't be a valid Windows path in most cases
        return wsl_path.replace('/', '\\')


def check_path_exists(path: str, in_wsl: bool = False) -> bool:
    """
    Check if a path exists in either Windows or WSL environment.
    
    Args:
        path: Path to check
        in_wsl: Whether to check in WSL (True) or Windows (False)
        
    Returns:
        True if path exists, False otherwise
    """
    if in_wsl:
        # Convert to WSL path if needed
        if ':' in path:  # Windows path detected
            path = convert_windows_to_wsl_path(path)
        
        # Check if path exists in WSL
        try:
            result = subprocess.run(
                ["wsl", "test", "-e", path, "&&", "echo", "exists"],
                capture_output=True,
                text=True,
                check=False
            )
            return "exists" in result.stdout
        except subprocess.SubprocessError:
            return False
    else:
        # Check if path exists in Windows
        return os.path.exists(path)


def validate_paths(windows_path: str) -> Tuple[bool, bool, Optional[str], Optional[str]]:
    """
    Validate that a path exists in both Windows and WSL environments.
    
    Args:
        windows_path: Windows path to validate
        
    Returns:
        Tuple of (windows_exists, wsl_exists, windows_path, wsl_path)
    """
    # Normalize Windows path
    windows_path = os.path.normpath(windows_path)
    
    # Convert to WSL path
    wsl_path = convert_windows_to_wsl_path(windows_path)
    
    # Check existence in both environments
    windows_exists = check_path_exists(windows_path, in_wsl=False)
    wsl_exists = check_path_exists(wsl_path, in_wsl=True)
    
    return windows_exists, wsl_exists, windows_path, wsl_path


def get_temp_dir(in_wsl: bool = False) -> str:
    """
    Get path to a temporary directory in either Windows or WSL.
    
    Args:
        in_wsl: Whether to return WSL path (True) or Windows path (False)
        
    Returns:
        Path to temporary directory
    """
    if in_wsl:
        # Get WSL temp directory
        try:
            result = subprocess.run(
                ["wsl", "mktemp", "-d"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.SubprocessError:
            # Fallback to a standard location
            return "/tmp/genome_filtering_tool"
    else:
        # Use Windows temp directory
        import tempfile
        return tempfile.gettempdir()