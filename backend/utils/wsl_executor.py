"""
WSL command execution utilities.
Provides functions to run commands in Windows Subsystem for Linux with proper
error handling, timeout management, and output capture.
"""

import os
import subprocess
import shlex
import time
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path

from .wsl_path_converter import convert_windows_to_wsl_path, convert_wsl_to_windows_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WSLExecutionError(Exception):
    """Exception raised when a WSL command fails."""
    
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = f"WSL command failed with return code {returncode}.\nCommand: {command}\n"
        if stderr:
            message += f"Error: {stderr}\n"
        super().__init__(message)


def run_wsl_command(
    command: str, 
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None
) -> Tuple[str, str, int]:
    """
    Run a command in WSL with proper error handling and timeout management.
    
    Args:
        command: The command to execute
        working_dir: Working directory (Windows path, will be converted to WSL path)
        timeout: Command timeout in seconds
        check: Whether to raise an exception if the command fails
        env: Environment variables to set for the command
        
    Returns:
        Tuple of (stdout, stderr, return_code)
        
    Raises:
        WSLExecutionError: If the command fails and check=True
        TimeoutExpired: If the command times out
    """
    # Start timing for performance logging
    start_time = time.time()
    
    # Build the WSL command
    wsl_cmd = ["wsl"]
    
    # Add environment variables if provided
    if env:
        for key, value in env.items():
            wsl_cmd.extend(["export", f"{key}={value}", "&&"])
    
    # Add working directory if provided
    if working_dir:
        wsl_dir = convert_windows_to_wsl_path(working_dir)
        wsl_cmd.extend(["cd", wsl_dir, "&&"])
    
    # Add the command
    # We use 'bash -c' to ensure consistent behavior and handle shell features
    wsl_cmd.extend(["bash", "-c", f"'{command}'"])
    
    logger.debug(f"Executing WSL command: {' '.join(wsl_cmd)}")
    
    try:
        # Run the command and capture output
        process = subprocess.run(
            wsl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False  # We'll handle errors manually
        )
        
        # Log execution time for performance monitoring
        execution_time = time.time() - start_time
        logger.debug(f"WSL command completed in {execution_time:.2f} seconds")
        
        # Handle errors if needed
        if check and process.returncode != 0:
            raise WSLExecutionError(
                command=command,
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr
            )
        
        return process.stdout, process.stderr, process.returncode
    
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {command}")
        return "", f"Command timed out after {timeout} seconds", -1
    
    except Exception as e:
        logger.error(f"Error executing WSL command: {str(e)}")
        return "", str(e), -2


def check_wsl_installed() -> bool:
    """
    Check if WSL is installed and available.
    
    Returns:
        True if WSL is available, False otherwise
    """
    try:
        process = subprocess.run(
            ["wsl", "--status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        # WSL returns 0 if it's installed and working
        return process.returncode == 0
    except Exception:
        return False


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the WSL environment.
    
    Args:
        command: The command name to check
        
    Returns:
        True if command exists, False otherwise
    """
    stdout, stderr, returncode = run_wsl_command(
        f"command -v {command} >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
        check=False
    )
    return 'exists' in stdout


def get_wsl_version() -> str:
    """
    Get the WSL version information.
    
    Returns:
        Version information as a string
    """
    stdout, stderr, returncode = run_wsl_command("wsl --version", check=False)
    if returncode == 0:
        return stdout
    return "Unknown (unable to retrieve version information)"


def get_quast_version() -> Optional[str]:
    """
    Get the installed QUAST version in WSL.
    
    Returns:
        Version string if QUAST is installed, None otherwise
    """
    stdout, stderr, returncode = run_wsl_command(
        "quast.py --version 2>&1 | grep -o 'QUAST v[0-9.]*'",
        check=False
    )
    
    if returncode == 0 and stdout.strip():
        return stdout.strip()
    return None


def monitor_resource_usage(pid: int, interval: float = 0.5) -> Dict[str, float]:
    """
    Monitor memory and CPU usage of a process.
    
    Args:
        pid: Process ID to monitor
        interval: Monitoring interval in seconds
        
    Returns:
        Dictionary with peak memory and CPU usage
    """
    stdout, stderr, returncode = run_wsl_command(
        f"ps -p {pid} -o %cpu,%mem",
        check=False
    )
    
    if returncode != 0:
        return {"peak_cpu": 0.0, "peak_memory": 0.0}
    
    lines = stdout.strip().split('\n')
    if len(lines) < 2:
        return {"peak_cpu": 0.0, "peak_memory": 0.0}
    
    try:
        cpu, mem = lines[1].split()
        return {"peak_cpu": float(cpu), "peak_memory": float(mem)}
    except (ValueError, IndexError):
        return {"peak_cpu": 0.0, "peak_memory": 0.0}


def run_with_progress(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    progress_callback: Optional[callable] = None,
    progress_regex: str = r'(\d+)%'
) -> Tuple[str, str, int]:
    """
    Run a command in WSL and monitor progress.
    
    Args:
        command: The command to execute
        working_dir: Working directory (Windows path)
        timeout: Command timeout in seconds
        progress_callback: Callback function that accepts progress percentage
        progress_regex: Regex pattern to extract progress information
        
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    import re
    import threading
    
    # Create command that outputs progress information
    progress_pattern = re.compile(progress_regex)
    
    # Start the process
    wsl_dir = convert_windows_to_wsl_path(working_dir) if working_dir else None
    
    # This function needs a custom implementation that streams output
    # and monitors for progress information in real-time
    full_command = f"cd {wsl_dir} && {command}" if wsl_dir else command
    
    wsl_cmd = ["wsl", "bash", "-c", f"'{full_command}'"]
    
    process = subprocess.Popen(
        wsl_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )
    
    stdout_chunks = []
    stderr_chunks = []
    
    # Function to read from a pipe and update progress
    def read_pipe(pipe, chunks, is_stderr=False):
        for line in iter(pipe.readline, ''):
            chunks.append(line)
            if progress_callback and not is_stderr:
                match = progress_pattern.search(line)
                if match:
                    try:
                        progress = int(match.group(1))
                        progress_callback(progress)
                    except (ValueError, IndexError):
                        pass
    
    # Create threads to read stdout and stderr
    stdout_thread = threading.Thread(target=read_pipe, args=(process.stdout, stdout_chunks))
    stderr_thread = threading.Thread(target=read_pipe, args=(process.stderr, stderr_chunks, True))
    
    # Set as daemon threads so they'll exit when the main program exits
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    
    # Start the threads
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for the process to complete or timeout
    try:
        return_code = process.wait(timeout=timeout)
        stdout_thread.join()
        stderr_thread.join()
        return ''.join(stdout_chunks), ''.join(stderr_chunks), return_code
    except subprocess.TimeoutExpired:
        process.kill()
        return ''.join(stdout_chunks), ''.join(stderr_chunks) + "\nCommand timed out", -1