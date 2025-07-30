"""
Cross-platform command execution utilities.
Provides a unified interface for running commands on different operating systems,
using WSL on Windows and native execution on macOS/Linux.
"""

import os
import subprocess
import logging
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from pathlib import Path

from .platform_detector import requires_wsl, is_windows, is_unix_like
from .wsl_executor import run_wsl_command, WSLExecutionError
from .wsl_path_converter import convert_windows_to_wsl_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrossPlatformExecutionError(Exception):
    """Exception raised when a cross-platform command fails."""
    
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str, platform: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.platform = platform
        message = f"Command failed on {platform} with return code {returncode}.\nCommand: {command}\n"
        if stderr:
            message += f"Error: {stderr}\n"
        super().__init__(message)


def run_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None
) -> Tuple[str, str, int]:
    """
    Run a command on the appropriate platform (WSL on Windows, native on Unix-like systems).
    
    Args:
        command: The command to execute
        working_dir: Working directory for the command
        timeout: Command timeout in seconds
        check: Whether to raise an exception if the command fails
        env: Environment variables to set for the command
        
    Returns:
        Tuple of (stdout, stderr, return_code)
        
    Raises:
        CrossPlatformExecutionError: If the command fails and check=True
    """
    if requires_wsl():
        # Use WSL on Windows
        try:
            return run_wsl_command(
                command=command,
                working_dir=working_dir,
                timeout=timeout,
                check=check,
                env=env
            )
        except WSLExecutionError as e:
            if check:
                raise CrossPlatformExecutionError(
                    command=e.command,
                    returncode=e.returncode,
                    stdout=e.stdout,
                    stderr=e.stderr,
                    platform="Windows (WSL)"
                )
            return e.stdout, e.stderr, e.returncode
    else:
        # Use native execution on Unix-like systems
        return run_native_command(
            command=command,
            working_dir=working_dir,
            timeout=timeout,
            check=check,
            env=env
        )


def run_native_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None
) -> Tuple[str, str, int]:
    """
    Run a command natively on Unix-like systems (macOS/Linux).
    
    Args:
        command: The command to execute
        working_dir: Working directory for the command
        timeout: Command timeout in seconds
        check: Whether to raise an exception if the command fails
        env: Environment variables to set for the command
        
    Returns:
        Tuple of (stdout, stderr, return_code)
        
    Raises:
        CrossPlatformExecutionError: If the command fails and check=True
    """
    import time
    
    # Start timing for performance logging
    start_time = time.time()
    
    # Prepare environment
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    logger.debug(f"Executing native command: {command}")
    if working_dir:
        logger.debug(f"Working directory: {working_dir}")
    
    try:
        # Run the command using shell=True for proper command parsing
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,  # We'll handle errors manually
            cwd=working_dir,
            env=process_env
        )
        
        # Log execution time for performance monitoring
        execution_time = time.time() - start_time
        logger.debug(f"Native command completed in {execution_time:.2f} seconds")
        
        # Handle errors if needed
        if check and process.returncode != 0:
            platform_name = "macOS" if is_unix_like() else "Linux"
            raise CrossPlatformExecutionError(
                command=command,
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                platform=platform_name
            )
        
        return process.stdout, process.stderr, process.returncode
    
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {command}")
        return "", f"Command timed out after {timeout} seconds", -1
    
    except Exception as e:
        logger.error(f"Error executing native command: {str(e)}")
        return "", str(e), -2


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists on the current platform.
    
    Args:
        command: The command name to check
        
    Returns:
        True if command exists, False otherwise
    """
    if requires_wsl():
        # Check in WSL environment
        from .wsl_executor import check_command_exists as wsl_check_command_exists
        return wsl_check_command_exists(command)
    else:
        # Check in native environment
        try:
            stdout, stderr, returncode = run_native_command(
                f"command -v {command} >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
                check=False
            )
            return 'exists' in stdout
        except Exception:
            return False


def get_command_path(command: str) -> Optional[str]:
    """
    Get the full path to a command on the current platform.
    
    Args:
        command: The command name to locate
        
    Returns:
        Full path to the command if found, None otherwise
    """
    try:
        if requires_wsl():
            # Get path in WSL environment
            stdout, stderr, returncode = run_command(
                f"which {command}",
                check=False
            )
            if returncode == 0 and stdout.strip():
                return stdout.strip()
        else:
            # Get path in native environment
            stdout, stderr, returncode = run_native_command(
                f"which {command}",
                check=False
            )
            if returncode == 0 and stdout.strip():
                return stdout.strip()
    except Exception:
        pass
    
    return None


def normalize_path(path: str, for_command: bool = False) -> str:
    """
    Normalize a path for the current platform.
    
    Args:
        path: The path to normalize
        for_command: Whether the path will be used in a command execution context
        
    Returns:
        Normalized path appropriate for the current platform
    """
    if requires_wsl() and for_command:
        # Convert Windows path to WSL path for command execution
        return convert_windows_to_wsl_path(path)
    else:
        # Use the path as-is for native execution or non-command contexts
        return os.path.normpath(path)


def get_temp_dir() -> str:
    """
    Get a temporary directory path appropriate for the current platform.
    
    Returns:
        Path to temporary directory
    """
    if requires_wsl():
        # Get WSL temp directory
        try:
            stdout, stderr, returncode = run_command(
                "mktemp -d",
                check=True
            )
            return stdout.strip()
        except Exception:
            # Fallback to a standard location
            return "/tmp/genome_filtering_tool"
    else:
        # Use native temp directory
        import tempfile
        return tempfile.gettempdir()


def get_executable_extension() -> str:
    """
    Get the executable file extension for the current platform.
    
    Returns:
        File extension for executables (e.g., '.exe' on Windows, '' on Unix)
    """
    return '.exe' if is_windows() else ''


def run_with_progress(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
    progress_regex: str = r'(\d+)%'
) -> Tuple[str, str, int]:
    """
    Run a command with progress monitoring on the current platform.
    
    Args:
        command: The command to execute
        working_dir: Working directory for the command
        timeout: Command timeout in seconds
        progress_callback: Callback function that accepts progress percentage
        progress_regex: Regex pattern to extract progress information
        
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    if requires_wsl():
        # Use WSL progress monitoring
        from .wsl_executor import run_with_progress as wsl_run_with_progress
        return wsl_run_with_progress(
            command=command,
            working_dir=working_dir,
            timeout=timeout,
            progress_callback=progress_callback,
            progress_regex=progress_regex
        )
    else:
        # Implement native progress monitoring
        import re
        import threading
        
        progress_pattern = re.compile(progress_regex)
        
        # Prepare environment
        process_env = os.environ.copy()
        
        # Start the process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            cwd=working_dir,
            env=process_env
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