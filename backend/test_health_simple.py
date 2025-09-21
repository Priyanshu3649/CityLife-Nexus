"""
Simple test for health impact service
"""
from datetime import datetime
from app.services.health_impact_service import health_impact_service
from app.schemas.user import HealthProfile
from app.schemas.air_quality import RouteAQIData, AQIReading
from app.schemas.base import CoordinatesSchema

# Create test data with correct schema
coordinates = CoordinatesSchema(latitude=28.6139, longitude=77.2090)

good_aqi_reading = AQIReading(
    coordinates=coordinates,
    aqi_value=45,
    pm25=12.0,
    pm10=18.0,
    no2=15.0,
    o3=80.0,
    source="test",
    reading_time=datetime.now()
)

unhealthy_aqi_reading = AQIReading(
    coordinates=coordinates,
    aqi_value=165,
    pm25=65.0,
    pm10=95.0,
    no2=55.0,
    o3=180.0,
    source="test",
    reading_time=datetime.now()
)

# Test route data
good_route_data = RouteAQIData(
    route_coordinates=[coordinates],
    aqi_readings=[good_aqi_reading],
    average_aqi=45,
    max_aqi=50,
    pollution_hotspots=[]
)

unhealthy_route_data = RouteAQIData(
    route_coordinates=[coordinates],
    aqi_readings=[unhealthy_aqi_reading],
    average_aqi=165,
    max_aqi=180,
    pollution_hotspots=[coordinates]
)

# Test health profiles
healthy_adult = HealthProfile(
    age_group="adult",
    respiratory_conditions=[],
    pollution_sensitivity=1.0,
    activity_level="moderate"
)

sensitive_child = HealthProfile(
    age_group="child",
    respiratory_conditions=["asthma"],
    pollution_sensitivity=2.0,
    activity_level="high"
)

def test_basic_functionality():
    """Test basic health impact calculations"""
    print("Testing Health Impact Service...")
    
    # Test 1: Good air quality for healthy adult
    print("\n1. Testing good air quality for healthy adult:")
    impact1 = health_impact_service.calculate_comprehensive_health_impact(
        good_route_data, healthy_adult, 30, "car"
    )
    print(f"   Health Risk Score: {impact1.health_risk_score}")
    print(f"   PM2.5 Exposure: {impact1.estimated_exposure_pm25}")
    print(f"   Precautions: {len(impact1.recommended_precautions)}")
    print(f"   Baseline Comparison: {impact1.comparison_to_baseline}%")
    
    # Test 2: Unhealthy air for sensitive child
    print("\n2. Testing unhealthy air quality for sensitive child:")
    impact2 = health_impact_service.calculate_comprehensive_health_impact(
        unhealthy_route_data, sensitive_child, 30, "bicycle"
    )
    print(f"   Health Risk Score: {impact2.health_risk_score}")
    print(f"   PM2.5 Exposure: {impact2.estimated_exposure_pm25}")
    print(f"   Precautions: {len(impact2.recommended_precautions)}")
    print(f"   Baseline Comparison: {impact2.comparison_to_baseline}%")
    
    # Test 3: Route comparison
    print("\n3. Testing route health comparison:")
    comparison = health_impact_service.calculate_route_health_comparison(
        good_route_data, unhealthy_route_data, healthy_adult, (25, 35)
    )
    print(f"   Recommended Route: {comparison['recommendation']}")
    print(f"   Health Benefit Score: {comparison['health_benefit_score']}")
    print(f"   Summary: {comparison['summary']}")
    
    # Test 4: AQI recommendations
    print("\n4. Testing AQI health recommendations:")
    recommendations = health_impact_service.get_health_recommendations_for_aqi(
        120, sensitive_child
    )
    print(f"   Category: {recommendations['category']}")
    print(f"   Color: {recommendations['color']}")
    print(f"   Mask Recommended: {recommendations['mask_recommended']}")
    print(f"   Personal Recommendations: {len(recommendations['personal_recommendations'])}")
    
    # Test 5: Personal risk factors
    print("\n5. Testing personal risk factor calculations:")
    risk_factors = health_impact_service._calculate_personal_risk_factors(sensitive_child)
    print(f"   Age Factor: {risk_factors['age_factor']}")
    print(f"   Condition Factor: {risk_factors['condition_factor']}")
    print(f"   Sensitivity Factor: {risk_factors['sensitivity_factor']}")
    
    print("\n✅ All basic tests completed successfully!")
    
    # Verify expected behaviors
    assert impact2.health_risk_score > impact1.health_risk_score, "Unhealthy air should have higher risk"
    assert impact2.estimated_exposure_pm25 > impact1.estimated_exposure_pm25, "Unhealthy air should have higher exposure"
    assert comparison['recommendation'] == 'route1', "Clean route should be recommended"
    assert recommendations['mask_recommended'], "Mask should be recommended for AQI 120"
    
    print("✅ All assertions passed!")

if __name__ == "__main__":
    test_basic_functionality()