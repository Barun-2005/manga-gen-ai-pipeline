#!/usr/bin/env python3
"""Execute the configuration test."""

import subprocess
import sys
from pathlib import Path

def run_test():
    """Run the configuration test."""
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, "test_config.py"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
    except Exception as e:
        print(f"Error running test: {e}")

if __name__ == "__main__":
    run_test()