#!/usr/bin/env python3
"""
Environment variable validation
Ensure required configuration is present
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EnvValidationResult:
    """Result of environment validation."""
    valid: bool
    missing: List[str]
    optional_missing: List[str]
    warnings: List[str]

class EnvironmentValidator:
    """Validate environment configuration."""
    
    REQUIRED_VARS = [
        "GROQ_API_KEY",  # Required for story generation
    ]
    
    OPTIONAL_VARS = {
        "NVIDIA_API_KEY": "Enhanced LLM reasoning",
        "GEMINI_API_KEY": "Better story direction",
        "NVIDIA_IMAGE_API_KEY": "FLUX.1-dev image generation",
        "MONGODB_URL": "Database persistence",
    }
    
    @classmethod
    def validate(cls) -> EnvValidationResult:
        """
        Validate environment variables.
        
        Returns:
            EnvValidationResult with validation status
        """
        missing = []
        optional_missing = []
        warnings = []
        
        # Check required vars
        for var in cls.REQUIRED_VARS:
            if not os.getenv(var):
                missing.append(var)
        
        # Check optional vars
        for var, description in cls.OPTIONAL_VARS.items():
            if not os.getenv(var):
                optional_missing.append(f"{var} ({description})")
        
        # Generate warnings
        if missing:
            warnings.append(f"❌ Missing REQUIRED: {', '.join(missing)}")
        
        if optional_missing:
            warnings.append(f"⚠️  Missing OPTIONAL: {', '.join(optional_missing)}")
        
        # Check for common mistakes
        for var in cls.REQUIRED_VARS + list(cls.OPTIONAL_VARS.keys()):
            value = os.getenv(var, "")
            if value and ("your_" in value.lower() or "example" in value.lower()):
                warnings.append(f"⚠️  {var} looks like a placeholder - update .env file")
        
        valid = len(missing) == 0
        
        return EnvValidationResult(
            valid=valid,
            missing=missing,
            optional_missing=optional_missing,
            warnings=warnings
        )
    
    @classmethod
    def print_report(cls):
        """Print validation report to console."""
        result = cls.validate()
        
        print("\n" + "="*60)
        print("🔍 ENVIRONMENT VALIDATION REPORT")
        print("="*60)
        
        if result.valid:
            print("✅ All required environment variables are set!")
        else:
            print("❌ Environment validation FAILED!")
            print(f"\nMissing required variables:")
            for var in result.missing:
                print(f"  - {var}")
        
        if result.optional_missing:
            print(f"\n⚠️  Optional features disabled (missing vars):")
            for item in result.optional_missing:
                print(f"  - {item}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  {warning}")
        
        print("\n💡 Copy .env.example to .env and add your API keys")
        print("="*60 + "\n")
        
        return result
