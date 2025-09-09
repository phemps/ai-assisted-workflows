#!/usr/bin/env python3
"""
Test installation script - non-interactive version for validation.
This script checks for the presence of critical packages directly.
"""

import sys
import importlib

def test_installation():
    """Test that critical packages can be imported."""
    print("🧪 Testing AI Assisted Workflows dependency installation...")

    critical_packages = [
        "bandit",      # Security analysis
        "psutil",      # System utilities
        "flake8",      # Code quality
        "requests",    # HTTP requests
    ]
    
    missing_packages = []

    print("\n🔍 Verifying critical packages...")
    for package_name in critical_packages:
        try:
            importlib.import_module(package_name)
            print(f"✅ {package_name} - OK")
        except ImportError:
            print(f"❌ {package_name} - MISSING")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n❌ Verification failed. Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("\n✅ All critical packages are installed.")
    return True

if __name__ == "__main__":
    success = test_installation()
    sys.exit(0 if success else 1)