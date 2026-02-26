#!/usr/bin/env python3
"""
Verification script for multi-agent orchestrator pattern structure.

This script verifies:
1. File structure and required files exist
2. No pattern-specific utils directory exists
3. Correct import paths in agent files
4. Dockerfile configurations are correct
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def verify_file_exists(file_path: str, base_dir: Path) -> bool:
    """
    Verify that a file exists.
    
    Args:
        file_path: Relative path to the file
        base_dir: Base directory for the pattern
        
    Returns:
        True if file exists, False otherwise
    """
    full_path = base_dir / file_path
    if full_path.exists():
        print_success(f"Found: {file_path}")
        return True
    else:
        print_error(f"Missing: {file_path}")
        return False


def verify_directory_not_exists(dir_path: str, base_dir: Path) -> bool:
    """
    Verify that a directory does NOT exist.
    
    Args:
        dir_path: Relative path to the directory
        base_dir: Base directory for the pattern
        
    Returns:
        True if directory does not exist, False if it exists
    """
    full_path = base_dir / dir_path
    if not full_path.exists():
        print_success(f"Correctly absent: {dir_path}")
        return True
    else:
        print_error(f"Should not exist: {dir_path}")
        return False


def verify_file_contains(file_path: str, base_dir: Path, search_strings: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that a file contains specific strings.
    
    Args:
        file_path: Relative path to the file
        base_dir: Base directory for the pattern
        search_strings: List of strings to search for
        
    Returns:
        Tuple of (all_found, missing_strings)
    """
    full_path = base_dir / file_path
    if not full_path.exists():
        print_error(f"Cannot check content - file missing: {file_path}")
        return False, search_strings
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    for search_str in search_strings:
        if search_str not in content:
            missing.append(search_str)
    
    return len(missing) == 0, missing


def main() -> int:
    """
    Main verification function.
    
    Returns:
        Exit code: 0 if all checks pass, 1 if any check fails
    """
    # Determine base directories
    script_dir = Path(__file__).parent
    patterns_dir = script_dir.parent
    
    print_header("Multi-Agent Orchestrator Pattern Structure Verification")
    print(f"Pattern directory: {script_dir}")
    print(f"Patterns root: {patterns_dir}")
    
    all_checks_passed = True
    
    # ========================================================================
    # 1. FILE STRUCTURE VERIFICATION
    # ========================================================================
    print_header("1. File Structure Verification")
    
    required_files = [
        "requirements.txt",
        "agents.json",
        "tools/__init__.py",
        "tools/code_interpreter.py",
        "tools/invoke_specialist.py",
        "agents/orchestrator/orchestrator_agent.py",
        "agents/orchestrator/Dockerfile",
        "agents/colorado/colorado_agent.py",
        "agents/colorado/Dockerfile",
        "agents/umich/umich_agent.py",
        "agents/umich/Dockerfile",
        "agents/coder/coder_agent.py",
        "agents/coder/Dockerfile",
    ]
    
    for file_path in required_files:
        if not verify_file_exists(file_path, script_dir):
            all_checks_passed = False
    
    # ========================================================================
    # 2. NO PATTERN-SPECIFIC UTILS
    # ========================================================================
    print_header("2. Pattern-Specific Utils Verification")
    
    if not verify_directory_not_exists("utils", script_dir):
        all_checks_passed = False
        print_warning("Pattern should use shared utils from patterns/utils/")
    
    # Verify shared utils exist
    shared_utils_files = [
        "utils/auth.py",
        "utils/ssm.py",
    ]
    
    print("\nVerifying shared utils exist:")
    for file_path in shared_utils_files:
        if not verify_file_exists(file_path, patterns_dir):
            all_checks_passed = False
    
    # ========================================================================
    # 3. IMPORT PATH VERIFICATION
    # ========================================================================
    print_header("3. Import Path Verification")
    
    agent_files = [
        "agents/orchestrator/orchestrator_agent.py",
        "agents/colorado/colorado_agent.py",
        "agents/umich/umich_agent.py",
        "agents/coder/coder_agent.py",
    ]
    
    for agent_file in agent_files:
        print(f"\nChecking {agent_file}:")
        
        # Check for sys.path.append
        contains_syspath, missing = verify_file_contains(
            agent_file,
            script_dir,
            ['sys.path.append("/app/patterns")']
        )
        
        if contains_syspath:
            print_success("Contains sys.path.append('/app/patterns')")
        else:
            print_error("Missing sys.path.append('/app/patterns')")
            all_checks_passed = False
        
        # Check for correct imports
        contains_imports, missing = verify_file_contains(
            agent_file,
            script_dir,
            ['from utils.auth import', 'from utils.ssm import']
        )
        
        if contains_imports:
            print_success("Uses correct shared utils imports (utils.auth, utils.ssm)")
        else:
            print_error(f"Missing or incorrect imports. Should use 'from utils.auth import' and 'from utils.ssm import'")
            print_error(f"Missing: {missing}")
            all_checks_passed = False
    
    # ========================================================================
    # 4. DOCKERFILE VERIFICATION
    # ========================================================================
    print_header("4. Dockerfile Verification")
    
    dockerfiles = [
        "agents/orchestrator/Dockerfile",
        "agents/colorado/Dockerfile",
        "agents/umich/Dockerfile",
        "agents/coder/Dockerfile",
    ]
    
    for dockerfile in dockerfiles:
        print(f"\nChecking {dockerfile}:")
        
        # Check for shared requirements.txt copy
        contains_req, missing = verify_file_contains(
            dockerfile,
            script_dir,
            ['COPY patterns/strands-multi-agent-orchestrator/requirements.txt']
        )
        
        if contains_req:
            print_success("Copies from shared requirements.txt at pattern root")
        else:
            print_error("Missing or incorrect requirements.txt COPY command")
            all_checks_passed = False
        
        # Check for shared utils copy
        contains_utils, missing = verify_file_contains(
            dockerfile,
            script_dir,
            ['COPY patterns/utils/ patterns/utils/']
        )
        
        if contains_utils:
            print_success("Copies shared patterns/utils/ directory")
        else:
            print_error("Missing or incorrect utils COPY command")
            all_checks_passed = False
        
        # Check for pattern-specific tools copy
        contains_tools, missing = verify_file_contains(
            dockerfile,
            script_dir,
            ['COPY patterns/strands-multi-agent-orchestrator/tools/ patterns/strands-multi-agent-orchestrator/tools/']
        )
        
        if contains_tools:
            print_success("Copies pattern-specific tools/ directory")
        else:
            print_error("Missing or incorrect tools COPY command")
            all_checks_passed = False
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("Verification Summary")
    
    if all_checks_passed:
        print_success("All verification checks passed! ✓")
        print(f"\n{Colors.GREEN}{Colors.BOLD}Structure is correct and follows the multi-agent orchestrator pattern.{Colors.RESET}\n")
        return 0
    else:
        print_error("Some verification checks failed! ✗")
        print(f"\n{Colors.RED}{Colors.BOLD}Please review the errors above and fix the issues.{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
