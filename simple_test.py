#!/usr/bin/env python3
"""
Simple test to verify CityLife Nexus backend structure
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        "backend/app/main.py",
        "backend/app/core/config.py",
        "backend/app/api/v1/api.py",
        "backend/app/models/base.py",
        "backend/app/schemas/base.py",
        "backend/app/services/maps_service.py",
        "backend/app/services/aqi_service.py",
        "backend/app/services/traffic_signal_service.py",
        "backend/app/services/route_optimizer.py",
        "frontend/src/components/NavigationView.js",
        "frontend/src/components/MapComponent.js",
        "docker-compose.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    return missing_files

def check_imports():
    """Check if key imports work"""
    try:
        # Test backend imports
        from backend.app.core.config import settings
        from backend.app.schemas.base import CoordinatesSchema
        print("✅ Backend imports successful")
        return True
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
        return False

def check_config():
    """Check configuration settings"""
    try:
        from backend.app.core.config import settings
        
        # Check key settings
        assert settings.PROJECT_NAME == "CityLife Nexus"
        assert settings.API_V1_STR == "/api/v1"
        assert len(settings.ALLOWED_HOSTS) > 0
        
        print("✅ Configuration check passed")
        return True
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def main():
    print("🌱 CityLife Nexus - Structure Verification")
    print("=" * 50)
    
    # Check file structure
    print("📁 Checking file structure...")
    missing_files = check_file_structure()
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
    
    # Check imports
    print("📦 Checking imports...")
    if not check_imports():
        return False
    
    # Check configuration
    print("⚙️  Checking configuration...")
    if not check_config():
        return False
    
    print("\n🎉 All structure checks passed!")
    print("   CityLife Nexus project structure is correct")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
