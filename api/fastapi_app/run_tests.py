#!/usr/bin/env python3
"""
Test runner script for MergeMind API tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    cmd.append("tests/")
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Filter by test type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "health":
        cmd.append("tests/test_health.py")
    elif test_type == "mrs":
        cmd.append("tests/test_mrs.py")
    elif test_type == "mr":
        cmd.append("tests/test_mr.py")
    elif test_type == "services":
        cmd.append("tests/test_services.py")
    elif test_type == "integration":
        cmd.append("tests/test_integration.py")
    
    # Add other options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run MergeMind API tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "health", "mrs", "mr", "services"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    
    args = parser.parse_args()
    
    # Set environment variables for testing
    os.environ.update({
        "GCP_PROJECT_ID": "test-project",
        "BQ_DATASET_RAW": "test_raw",
        "BQ_DATASET_MODELED": "test_modeled",
        "VERTEX_LOCATION": "us-central1",
        "GITLAB_BASE_URL": "https://test.gitlab.com",
        "GITLAB_TOKEN": "test-token",
        "SLACK_SIGNING_SECRET": "test-secret",
        "SLACK_BOT_TOKEN": "test-bot-token",
        "API_BASE_URL": "http://localhost:8080",
        "LOG_LEVEL": "DEBUG"
    })
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
