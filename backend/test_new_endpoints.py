#!/usr/bin/env python3
"""
Test script to verify that all new API endpoints are properly registered
"""
import sys
import os

def test_api_endpoints():
    """Test that all API endpoints can be imported and registered"""
    try:
        # Test importing the main API router
        from app.api.v1.api import api_router
        print("✓ Main API router imported successfully")
        
        # Test importing all new endpoint modules
        from app.api.v1.endpoints import traffic_predictor, parking, eco_score
        from app.api.v1.endpoints import community, interpolation, green_wave, incidents
        print("✓ All new endpoint modules imported successfully")
        
        # Check that routers exist
        assert hasattr(traffic_predictor, 'router'), "Traffic predictor router missing"
        assert hasattr(parking, 'router'), "Parking router missing"
        assert hasattr(eco_score, 'router'), "Eco score router missing"
        assert hasattr(community, 'router'), "Community router missing"
        assert hasattr(interpolation, 'router'), "Interpolation router missing"
        assert hasattr(green_wave, 'router'), "Green wave router missing"
        assert hasattr(incidents, 'router'), "Incidents router missing"
        print("✓ All new routers exist")
        
        # Test that services can be imported
        from app.services.traffic_predictor_service import traffic_predictor_service
        from app.services.parking_service import parking_service
        from app.services.eco_score_service import eco_score_service
        from app.services.community_service import community_service
        from app.services.interpolation_service import interpolation_service
        from app.services.green_wave_service import green_wave_service
        print("✓ All new services imported successfully")
        
        # Test that services have the expected methods
        # Traffic predictor service
        assert hasattr(traffic_predictor_service, 'predict_traffic_density'), "Traffic predictor missing predict_traffic_density method"
        assert hasattr(traffic_predictor_service, 'get_traffic_prediction_summary'), "Traffic predictor missing get_traffic_prediction_summary method"
        print("✓ Traffic predictor service methods verified")
        
        # Parking service
        assert hasattr(parking_service, 'find_parking_near_destination'), "Parking service missing find_parking_near_destination method"
        assert hasattr(parking_service, 'predict_parking_availability'), "Parking service missing predict_parking_availability method"
        print("✓ Parking service methods verified")
        
        # Eco score service
        assert hasattr(eco_score_service, 'calculate_eco_score'), "Eco score service missing calculate_eco_score method"
        assert hasattr(eco_score_service, 'get_trip_comparison'), "Eco score service missing get_trip_comparison method"
        print("✓ Eco score service methods verified")
        
        # Community service
        assert hasattr(community_service, 'submit_report'), "Community service missing submit_report method"
        assert hasattr(community_service, 'get_reports_in_area'), "Community service missing get_reports_in_area method"
        print("✓ Community service methods verified")
        
        # Interpolation service
        assert hasattr(interpolation_service, 'idw_interpolation'), "Interpolation service missing idw_interpolation method"
        assert hasattr(interpolation_service, 'linear_interpolation'), "Interpolation service missing linear_interpolation method"
        print("✓ Interpolation service methods verified")
        
        # Green wave service
        assert hasattr(green_wave_service, 'calculate_green_wave_offset'), "Green wave service missing calculate_green_wave_offset method"
        assert hasattr(green_wave_service, 'optimize_corridor_timing'), "Green wave service missing optimize_corridor_timing method"
        print("✓ Green wave service methods verified")
        
        print("\n🎉 All tests passed! New API endpoints are properly integrated.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)