"""
Test health impact API endpoints
"""
import requests
import json
from datetime import datetime

# Test data
test_data = {
    "route_aqi_data": {
        "route_coordinates": [
            {"latitude": 28.6139, "longitude": 77.2090}
        ],
        "aqi_readings": [
            {
                "coordinates": {"latitude": 28.6139, "longitude": 77.2090},
                "aqi_value": 120,
                "pm25": 35.0,
                "pm10": 50.0,
                "no2": 25.0,
                "o3": 140.0,
                "source": "test",
                "reading_time": datetime.now().isoformat()
            }
        ],
        "average_aqi": 120,
        "max_aqi": 130,
        "pollution_hotspots": []
    },
    "health_profile": {
        "age_group": "adult",
        "respiratory_conditions": ["asthma"],
        "pollution_sensitivity": 1.5,
        "activity_level": "moderate"
    },
    "travel_time_minutes": 25,
    "vehicle_type": "car"
}

def test_health_impact_api():
    """Test the health impact API endpoints"""
    base_url = "http://127.0.0.1:8002/api/v1/health-impact"
    
    print("Testing Health Impact API endpoints...")
    
    try:
        # Test 1: Calculate health impact
        print("\n1. Testing health impact calculation:")
        response = requests.post(f"{base_url}/calculate", json=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Health Risk Score: {result['health_risk_score']}")
            print(f"   PM2.5 Exposure: {result['estimated_exposure_pm25']}")
            print(f"   Precautions: {len(result['recommended_precautions'])}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 2: AQI recommendations
        print("\n2. Testing AQI recommendations:")
        aqi_data = {"aqi": 150, "health_profile": test_data["health_profile"]}
        response = requests.post(f"{base_url}/aqi-recommendations", json=aqi_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Category: {result['category']}")
            print(f"   Mask Recommended: {result['mask_recommended']}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 3: Quick risk score
        print("\n3. Testing quick risk score:")
        response = requests.get(f"{base_url}/quick-risk-score?aqi=120&has_respiratory_condition=true&age_group=adult")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Risk Score: {result['health_risk_score']}")
            print(f"   Risk Level: {result['risk_level']}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 4: Health categories
        print("\n4. Testing health categories:")
        response = requests.get(f"{base_url}/health-categories")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Categories: {len(result['categories'])}")
        else:
            print(f"   Error: {response.text}")
        
        # Test 5: Risk factors
        print("\n5. Testing risk factors:")
        response = requests.get(f"{base_url}/risk-factors")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Age Risk Factors: {len(result['age_risk_factors'])}")
            print(f"   Respiratory Conditions: {len(result['respiratory_conditions'])}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n✅ API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the backend is running on port 8002.")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_health_impact_api()