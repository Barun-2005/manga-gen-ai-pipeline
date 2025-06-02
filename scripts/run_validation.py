#!/usr/bin/env python3
"""
Validation Entry Point
Runs Phase 13 real validation pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.validation.validation_runner import Phase13RealRunner

def main():
    """Main validation entry point."""
    runner = Phase13RealRunner()
    success = runner.run_complete_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
