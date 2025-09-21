#!/usr/bin/env python3
"""
Simple test script to verify SafeAir Navigator backend functionality
"""
import sys
import os
import subprocess
import time
import requests
import json

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting SafeAir Navigator backend...")
    
    # Change to backend directory
    os.chdir("backend")
    
    # Set environment variables
    os.environ["DATABASE_URL"] = "postgresql://safeair:safeair@localhost:5432/safeair_navigator"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    
    try:
        # Start the server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        # Wait a bit for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def test_api_endpoints():
    """Test key API endpoints"""
    base_url = "http://localhost:8000"
    
    tests = [
        {
            "name": "Health Check",
            "method": "GET",
            "url": f"{base_url}/health",
            "expected_status": 200
        },
        {
            "name": "API Root",
            "method": "GET", 
            "url": f"{base_url}/",
            "expected_status": 200
        },
        {
            "name": "API Documentation",
            "method": "GET",
            "url": f"{base_url}/docs",
            "expected_status": 200
        },
        {
            "name": "Create Session",
            "method": "POST",
            "url": f"{base_url}/api/v1/sessions/create",
            "expected_status": 200
        },
        {
            "name": "List Traffic Signals",
            "method": "GET",
            "url": f"{base_url}/api/v1/signals/all-signals",
            "expected_status": 200
        },
        {
            "name": "Get Signal State",
            "method": "GET",
            "url": f"{base_url}/api/v1/signals/current/TL001",
            "expected_status": 200
        }
    ]
    
    print("\n🧪 Testing API endpoints...")
    
    for test in tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            elif test["method"] == "POST":
                response = requests.post(test["url"], timeout=10)
            
            if response.status_code == test["expected_status"]:
                print(f"✅ {test['name']}: {response.status_code}")
                if test["name"] == "Create Session":
                    data = response.json()
                    print(f"   Session ID: {data.get('session_id', 'N/A')}")
            else:
                print(f"⚠️  {test['name']}: Expected {test['expected_status']}, got {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test['name']}: Connection failed - {e}")
        except Exception as e:
            print(f"❌ {test['name']}: Error - {e}")

def test_advanced_features():
    """Test advanced SafeAir Navigator features"""
    base_url = "http://localhost:8000"
    
    print("\n🔬 Testing advanced features...")
    
    # Test route optimization
    try:
        route_data = {
            "origin": {"latitude": 28.6139, "longitude": 77.2090},
            "destination": {"latitude": 28.6200, "longitude": 77.2150}
        }
        
        response = requests.post(
            f"{base_url}/api/v1/routes/route-comparison",
            json=route_data,
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Route Comparison: Working")
            data = response.json()
            print(f"   Fast route: {data.get('fast_route', {}).get('estimated_time_minutes', 'N/A')} min")
            print(f"   Clean route: {data.get('clean_route', {}).get('estimated_time_minutes', 'N/A')} min")
        else:
            print(f"⚠️  Route Comparison: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Route Comparison: {e}")
    
    # Test AQI data
    try:
        aqi_data = {"latitude": 28.6139, "longitude": 77.2090}
        
        response = requests.post(
            f"{base_url}/api/v1/aqi/measurements",
            json=aqi_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ AQI Measurements: Working")
            data = response.json()
            print(f"   Found {len(data)} AQI readings")
        else:
            print(f"⚠️  AQI Measurements: {response.status_code}")
            
    except Exception as e:
        print(f"❌ AQI Measurements: {e}")
    
    # Test green wave calculation
    try:
        response = requests.post(
            f"{base_url}/api/v1/signals/green-wave/calculate-offset?distance_meters=500&average_speed_kmh=50",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Green Wave Calculation: Working")
            data = response.json()
            print(f"   Recommended offset: {data.get('recommended_offset_seconds', 'N/A')} seconds")
        else:
            print(f"⚠️  Green Wave Calculation: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Green Wave Calculation: {e}")

def main():
    """Main test function"""
    print("🌱 SafeAir Navigator Backend Test")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return False
    
    try:
        # Test basic endpoints
        test_api_endpoints()
        
        # Test advanced features
        test_advanced_features()
        
        print("\n🎉 Backend testing completed!")
        print(f"📊 API Documentation: http://localhost:8000/docs")
        print(f"🔍 Interactive API: http://localhost:8000/redoc")
        
        # Keep server running
        print("\n⏸️  Press Ctrl+C to stop the server...")
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        backend_process.terminate()
        backend_process.wait()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        backend_process.terminate()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)