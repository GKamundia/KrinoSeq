#!/usr/bin/env python3
"""
Test script to demonstrate cross-platform functionality of KrinoSeq.
This script shows that the application correctly detects the platform and
provides appropriate setup recommendations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.utils.platform_detector import (
    get_platform, 
    get_platform_info, 
    requires_wsl, 
    get_recommended_setup
)
from backend.utils.quast_config import (
    validate_quast_installation,
    get_installation_instructions,
    get_quast_command
)
from backend.utils.cross_platform_executor import (
    run_command,
    check_command_exists
)

def main():
    print("=" * 60)
    print("KrinoSeq Cross-Platform Compatibility Test")
    print("=" * 60)
    
    # Platform detection
    platform_info = get_platform_info()
    print(f"\nPlatform Detection:")
    print(f"  Operating System: {platform_info['system']}")
    print(f"  Platform Type: {platform_info['platform_type']}")
    print(f"  Machine: {platform_info['machine']}")
    print(f"  Requires WSL: {platform_info['requires_wsl']}")
    print(f"  Is Unix-like: {platform_info['is_unix_like']}")
    
    # Answer the main question
    print(f"\n" + "=" * 60)
    if platform_info['platform_type'] == 'macos':
        print("ANSWER: Do you need WSL on your MacBook Pro M2?")
        print("NO - WSL is not needed on macOS!")
        print("macOS is Unix-based and can run bioinformatics tools natively.")
    elif platform_info['platform_type'] == 'windows':
        print("ANSWER: Do you need WSL on Windows?")
        print("YES - WSL is recommended for running Linux-based tools.")
    else:
        print(f"ANSWER: Do you need WSL on {platform_info['platform_type']}?")
        print("NO - WSL is only needed on Windows systems.")
    print("=" * 60)
    
    # QUAST validation
    print(f"\nQUAST Installation Status:")
    quast_validation = validate_quast_installation()
    print(f"  QUAST Available: {quast_validation['is_available']}")
    print(f"  QUAST Command: {quast_validation.get('quast_command', 'Not found')}")
    if quast_validation['quast_path']:
        print(f"  QUAST Path: {quast_validation['quast_path']}")
    if quast_validation['version']:
        print(f"  QUAST Version: {quast_validation['version']}")
    if quast_validation['error']:
        print(f"  Error: {quast_validation['error']}")
    
    # Setup recommendations
    print(f"\nSetup Recommendations:")
    recommendations = get_recommended_setup()
    print(recommendations)
    
    if not quast_validation['is_available']:
        print(f"\nInstallation Instructions:")
        instructions = get_installation_instructions()
        print(instructions)
    
    # Test cross-platform command execution
    print(f"\nCross-Platform Command Execution Test:")
    try:
        stdout, stderr, returncode = run_command('echo "Hello from cross-platform executor"', check=False)
        print(f"  ✓ Command executed successfully")
        print(f"  Output: {stdout.strip()}")
    except Exception as e:
        print(f"  ✗ Command execution failed: {e}")
    
    # Test basic command availability
    print(f"\nBasic Command Availability:")
    commands_to_test = ['python3', 'pip', 'git']
    for cmd in commands_to_test:
        available = check_command_exists(cmd)
        status = "✓" if available else "✗"
        print(f"  {status} {cmd}: {'Available' if available else 'Not found'}")
    
    print(f"\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()