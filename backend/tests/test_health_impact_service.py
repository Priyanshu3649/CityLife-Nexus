"""
Tests for Health Impact Assessment Service
Testing personalized health impact calculations and risk assessments
"""
import pytest
from datetime import datetime, timedelta
from typing import List

from app.services.health_impact_service import HealthImpactService
from app.schemas.user import HealthProfile
from app.schemas.air_quality import AQIReading, RouteAQIData, HealthImpactEstimate


class TestHealthImpactService:
    """Test suite for health impact calculations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = HealthImpactService()
        
        # Sample AQI readings
        self.good_aqi_reading = AQIReading(
            latitude=28.6139,
            longitude=77.2090,
            aqi_value=45,
            pm25=12.0,
            pm10=18.0,
            no2=15.0,
            o3=80.0,
            source="test",
            reading_time=datetime.now()
        )
        
        self.moderate_aqi_reading = AQIReading(
            latitude=28.6139,
            longitude=77.2090,
            aqi_value=85,
            pm25=25.0,
            pm10=40.0,
            no2=30.0,
            o3=120.0,
            source="test",
            reading_time=datetime.now()
        )
        
        self.unhealthy_aqi_reading = AQIReading(
            latitude=28.6139,
            longitude=77.2090,
            aqi_value=165,
            pm25=65.0,
            pm10=95.0,
            no2=55.0,
            o3=180.0,
            source="test",
            reading_time=datetime.now()
        )
        
        # Sample health profiles
        self.healthy_adult = HealthProfile(
            age_group="adult",
            respiratory_conditions=[],
            pollution_sensitivity=1.0,
            activity_level="moderate"
        )
        
        self.sensitive_child = HealthProfile(
            age_group="child",
            respiratory_conditions=["asthma"],
            pollution_sensitivity=2.0,
            activity_level="high"
        )
        
        self.senior_with_copd = HealthProfile(
            age_group="senior",
            respiratory_conditions=["copd"],
            pollution_sensitivity=2.5,
            activity_level="low"
        )
    
    def test_aqi_to_pm25_conversion(self):
        """Test AQI to PM2.5 concentration conversion"""
        # Test various AQI levels
        assert self.service._aqi_to_pm25_concentration(0) == 0.0
        assert self.service._aqi_to_pm25_concentration(50) == 12.0
        assert abs(self.service._aqi_to_pm25_concentration(100) - 35.4) < 0.1
        assert self.service._aqi_to_pm25_concentration(150) > 50
        assert self.service._aqi_to_pm25_concentration(300) > 200
    
    def test_personal_risk_factors_healthy_adult(self):
        """Test personal risk calculation for healthy adult"""
        risk_factors = self.service._calculate_personal_risk_factors(self.healthy_adult)
        
        assert risk_factors["age_factor"] == 1.0
        assert risk_factors["condition_factor"] == 1.0
        assert risk_factors["sensitivity_factor"] == 1.0
    
    def test_personal_risk_factors_sensitive_child(self):
        """Test personal risk calculation for sensitive child with asthma"""
        risk_factors = self.service._calculate_personal_risk_factors(self.sensitive_child)
        
        assert risk_factors["age_factor"] == 1.5  # Child multiplier
        assert risk_factors["condition_factor"] == 2.0  # Asthma multiplier
        assert risk_factors["sensitivity_factor"] == 2.0  # High sensitivity
    
    def test_personal_risk_factors_senior_with_copd(self):
        """Test personal risk calculation for senior with COPD"""
        risk_factors = self.service._calculate_personal_risk_factors(self.senior_with_copd)
        
        assert risk_factors["age_factor"] == 1.3  # Senior multiplier
        assert risk_factors["condition_factor"] == 2.5  # COPD multiplier
        assert risk_factors["sensitivity_factor"] == 2.5  # High sensitivity
    
    def test_base_exposure_calculation_car(self):
        """Test base exposure calculation for car travel"""
        route_data = RouteAQIData(
            average_aqi=100,
            max_aqi=120,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        exposure = self.service._calculate_base_exposure(route_data, 30, "car")
        
        assert "pm25" in exposure
        assert "pm10" in exposure
        assert "no2" in exposure
        assert "o3" in exposure
        assert all(val > 0 for val in exposure.values())
        
        # Car should have protection factor of 0.7
        expected_pm25 = self.service._aqi_to_pm25_concentration(100) * 0.7 * 0.5
        assert abs(exposure["pm25"] - expected_pm25) < 1.0
    
    def test_base_exposure_calculation_bicycle(self):
        """Test base exposure calculation for bicycle travel"""
        route_data = RouteAQIData(
            average_aqi=100,
            max_aqi=120,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        car_exposure = self.service._calculate_base_exposure(route_data, 30, "car")
        bike_exposure = self.service._calculate_base_exposure(route_data, 30, "bicycle")
        
        # Bicycle should have higher exposure than car
        assert bike_exposure["pm25"] > car_exposure["pm25"]
    
    def test_comprehensive_health_impact_good_air(self):
        """Test comprehensive health impact for good air quality"""
        route_data = RouteAQIData(
            average_aqi=45,
            max_aqi=50,
            aqi_readings=[self.good_aqi_reading]
        )
        
        impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "car"
        )
        
        assert isinstance(impact, HealthImpactEstimate)
        assert impact.health_risk_score < 30  # Low risk for good air
        assert impact.estimated_exposure_pm25 > 0
        assert len(impact.recommended_precautions) >= 1
        assert impact.comparison_to_baseline < 50  # Not much above baseline
    
    def test_comprehensive_health_impact_unhealthy_air(self):
        """Test comprehensive health impact for unhealthy air quality"""
        route_data = RouteAQIData(
            average_aqi=165,
            max_aqi=180,
            aqi_readings=[self.unhealthy_aqi_reading]
        )
        
        impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "car"
        )
        
        assert impact.health_risk_score > 40  # Higher risk for unhealthy air
        assert impact.estimated_exposure_pm25 > 20
        assert len(impact.recommended_precautions) > 2
        assert impact.comparison_to_baseline > 100  # Significantly above baseline
    
    def test_health_impact_sensitive_vs_healthy(self):
        """Test health impact difference between sensitive and healthy individuals"""
        route_data = RouteAQIData(
            average_aqi=120,
            max_aqi=140,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        healthy_impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "car"
        )
        
        sensitive_impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.sensitive_child, 30, "car"
        )
        
        # Sensitive individual should have higher risk
        assert sensitive_impact.health_risk_score > healthy_impact.health_risk_score
        assert len(sensitive_impact.recommended_precautions) >= len(healthy_impact.recommended_precautions)
    
    def test_time_weighted_exposure(self):
        """Test time-weighted exposure calculations"""
        base_exposure = {"pm25": 20.0, "pm10": 30.0, "no2": 15.0, "o3": 100.0}
        
        # Test different travel times
        short_exposure = self.service._calculate_time_weighted_exposure(
            base_exposure, 15, self.healthy_adult
        )
        long_exposure = self.service._calculate_time_weighted_exposure(
            base_exposure, 60, self.healthy_adult
        )
        
        # Longer travel should result in higher exposure
        assert long_exposure["pm25"] > short_exposure["pm25"]
        
        # Test different activity levels
        low_activity_exposure = self.service._calculate_time_weighted_exposure(
            base_exposure, 30, HealthProfile(
                age_group="adult", respiratory_conditions=[], 
                pollution_sensitivity=1.0, activity_level="low"
            )
        )
        high_activity_exposure = self.service._calculate_time_weighted_exposure(
            base_exposure, 30, HealthProfile(
                age_group="adult", respiratory_conditions=[], 
                pollution_sensitivity=1.0, activity_level="high"
            )
        )
        
        # Higher activity should result in higher exposure
        assert high_activity_exposure["pm25"] > low_activity_exposure["pm25"]
    
    def test_health_precautions_generation(self):
        """Test generation of health precautions"""
        route_data = RouteAQIData(
            average_aqi=180,
            max_aqi=200,
            aqi_readings=[self.unhealthy_aqi_reading]
        )
        
        # Test precautions for different health profiles
        healthy_precautions = self.service._generate_health_precautions(
            60.0, route_data, self.healthy_adult
        )
        
        sensitive_precautions = self.service._generate_health_precautions(
            80.0, route_data, self.sensitive_child
        )
        
        assert len(healthy_precautions) > 0
        assert len(sensitive_precautions) >= len(healthy_precautions)
        
        # Check for specific precautions
        precautions_text = " ".join(sensitive_precautions).lower()
        assert "mask" in precautions_text or "inhaler" in precautions_text
    
    def test_route_health_comparison(self):
        """Test health comparison between two routes"""
        clean_route = RouteAQIData(
            average_aqi=50,
            max_aqi=60,
            aqi_readings=[self.good_aqi_reading]
        )
        
        polluted_route = RouteAQIData(
            average_aqi=150,
            max_aqi=170,
            aqi_readings=[self.unhealthy_aqi_reading]
        )
        
        comparison = self.service.calculate_route_health_comparison(
            clean_route, polluted_route, self.healthy_adult, (25, 30)
        )
        
        assert "route1_impact" in comparison
        assert "route2_impact" in comparison
        assert comparison["recommendation"] == "route1"  # Clean route should be recommended
        assert comparison["health_benefit_score"] > 0
        assert comparison["exposure_difference_pm25"] > 0
        assert "summary" in comparison
    
    def test_health_recommendations_for_aqi(self):
        """Test health recommendations for different AQI levels"""
        # Test good air quality
        good_rec = self.service.get_health_recommendations_for_aqi(45, self.healthy_adult)
        assert good_rec["category"] == "Good"
        assert good_rec["color"] == "green"
        assert not good_rec["mask_recommended"]
        assert good_rec["outdoor_exercise_safe"]
        
        # Test unhealthy air quality
        unhealthy_rec = self.service.get_health_recommendations_for_aqi(165, self.sensitive_child)
        assert unhealthy_rec["category"] == "Unhealthy"
        assert unhealthy_rec["color"] == "red"
        assert unhealthy_rec["mask_recommended"]
        assert not unhealthy_rec["outdoor_exercise_safe"]
        assert len(unhealthy_rec["personal_recommendations"]) > 0
    
    def test_pollutant_impacts_calculation(self):
        """Test calculation of pollutant-specific health impacts"""
        route_data = RouteAQIData(
            average_aqi=120,
            max_aqi=140,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        impacts = self.service._calculate_pollutant_impacts(route_data, self.healthy_adult)
        
        # Should have impacts for pollutants with data
        assert "pm25" in impacts
        assert "pm10" in impacts
        assert "no2" in impacts
        assert "o3" in impacts
        
        # Each pollutant should have respiratory and cardiovascular impacts
        for pollutant, impact_data in impacts.items():
            if impact_data:  # If there's data for this pollutant
                assert "respiratory" in impact_data
                assert "cardiovascular" in impact_data
                assert "excess_ratio" in impact_data
    
    def test_baseline_comparison_calculation(self):
        """Test baseline comparison calculations"""
        # Test exposure above baseline
        high_exposure = {"pm25": 50.0, "pm10": 75.0}
        high_comparison = self.service._calculate_baseline_comparison(high_exposure, 30)
        assert high_comparison > 0  # Should be above baseline
        
        # Test exposure at baseline
        low_exposure = {"pm25": 7.5, "pm10": 15.0}  # Close to clean air baseline
        low_comparison = self.service._calculate_baseline_comparison(low_exposure, 30)
        assert abs(low_comparison) < 50  # Should be close to baseline
    
    def test_error_handling(self):
        """Test error handling in health impact calculations"""
        # Test with invalid data
        invalid_route_data = RouteAQIData(
            average_aqi=-1,  # Invalid AQI
            max_aqi=-1,
            aqi_readings=[]
        )
        
        # Should return default impact without crashing
        impact = self.service.calculate_comprehensive_health_impact(
            invalid_route_data, None, 30, "car"
        )
        
        assert isinstance(impact, HealthImpactEstimate)
        assert impact.health_risk_score >= 0
        assert len(impact.recommended_precautions) > 0
    
    def test_vehicle_type_impact(self):
        """Test impact of different vehicle types on exposure"""
        route_data = RouteAQIData(
            average_aqi=100,
            max_aqi=120,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        # Test different vehicle types
        car_impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "car"
        )
        
        bike_impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "bicycle"
        )
        
        electric_impact = self.service.calculate_comprehensive_health_impact(
            route_data, self.healthy_adult, 30, "electric"
        )
        
        # Bicycle should have highest exposure, electric car lowest
        assert bike_impact.estimated_exposure_pm25 > car_impact.estimated_exposure_pm25
        assert electric_impact.estimated_exposure_pm25 < car_impact.estimated_exposure_pm25
        
        # Risk scores should follow the same pattern
        assert bike_impact.health_risk_score >= car_impact.health_risk_score
        assert electric_impact.health_risk_score <= car_impact.health_risk_score
    
    def test_respiratory_condition_specific_advice(self):
        """Test condition-specific health advice"""
        route_data = RouteAQIData(
            average_aqi=120,
            max_aqi=140,
            aqi_readings=[self.moderate_aqi_reading]
        )
        
        # Test different respiratory conditions
        asthma_profile = HealthProfile(
            age_group="adult",
            respiratory_conditions=["asthma"],
            pollution_sensitivity=1.5,
            activity_level="moderate"
        )
        
        copd_profile = HealthProfile(
            age_group="senior",
            respiratory_conditions=["copd"],
            pollution_sensitivity=2.0,
            activity_level="low"
        )
        
        asthma_impact = self.service.calculate_comprehensive_health_impact(
            route_data, asthma_profile, 30, "car"
        )
        
        copd_impact = self.service.calculate_comprehensive_health_impact(
            route_data, copd_profile, 30, "car"
        )
        
        # COPD should generally have higher risk than asthma
        assert copd_impact.health_risk_score >= asthma_impact.health_risk_score
        
        # Both should have condition-specific precautions
        asthma_text = " ".join(asthma_impact.recommended_precautions).lower()
        copd_text = " ".join(copd_impact.recommended_precautions).lower()
        
        assert "inhaler" in asthma_text or "medication" in asthma_text
        assert "medication" in copd_text or "doctor" in copd_text


@pytest.fixture
def health_service():
    """Fixture providing health impact service instance"""
    return HealthImpactService()


@pytest.fixture
def sample_health_profiles():
    """Fixture providing sample health profiles for testing"""
    return {
        "healthy_adult": HealthProfile(
            age_group="adult",
            respiratory_conditions=[],
            pollution_sensitivity=1.0,
            activity_level="moderate"
        ),
        "sensitive_child": HealthProfile(
            age_group="child",
            respiratory_conditions=["asthma"],
            pollution_sensitivity=2.0,
            activity_level="high"
        ),
        "senior_copd": HealthProfile(
            age_group="senior",
            respiratory_conditions=["copd"],
            pollution_sensitivity=2.5,
            activity_level="low"
        )
    }


@pytest.fixture
def sample_aqi_data():
    """Fixture providing sample AQI data for testing"""
    return {
        "good": RouteAQIData(
            average_aqi=45,
            max_aqi=50,
            aqi_readings=[AQIReading(
                latitude=28.6139, longitude=77.2090, aqi_value=45,
                pm25=12.0, pm10=18.0, no2=15.0, o3=80.0,
                source="test", reading_time=datetime.now()
            )]
        ),
        "unhealthy": RouteAQIData(
            average_aqi=165,
            max_aqi=180,
            aqi_readings=[AQIReading(
                latitude=28.6139, longitude=77.2090, aqi_value=165,
                pm25=65.0, pm10=95.0, no2=55.0, o3=180.0,
                source="test", reading_time=datetime.now()
            )]
        )
    }


class TestHealthImpactIntegration:
    """Integration tests for health impact service with other components"""
    
    def test_integration_with_route_data(self, health_service, sample_health_profiles, sample_aqi_data):
        """Test integration with route and AQI data"""
        # Test with different combinations
        for profile_name, profile in sample_health_profiles.items():
            for aqi_name, aqi_data in sample_aqi_data.items():
                impact = health_service.calculate_comprehensive_health_impact(
                    aqi_data, profile, 30, "car"
                )
                
                # Verify all required fields are present
                assert hasattr(impact, 'estimated_exposure_pm25')
                assert hasattr(impact, 'health_risk_score')
                assert hasattr(impact, 'recommended_precautions')
                assert hasattr(impact, 'comparison_to_baseline')
                
                # Verify reasonable values
                assert 0 <= impact.health_risk_score <= 100
                assert impact.estimated_exposure_pm25 >= 0
                assert len(impact.recommended_precautions) > 0
    
    def test_performance_with_large_datasets(self, health_service):
        """Test performance with larger datasets"""
        import time
        
        # Create large dataset
        readings = []
        for i in range(100):
            readings.append(AQIReading(
                latitude=28.6139 + i * 0.001,
                longitude=77.2090 + i * 0.001,
                aqi_value=50 + i,
                pm25=12.0 + i * 0.5,
                pm10=18.0 + i * 0.7,
                no2=15.0 + i * 0.3,
                o3=80.0 + i * 1.0,
                source="test",
                reading_time=datetime.now() - timedelta(minutes=i)
            ))
        
        large_route_data = RouteAQIData(
            average_aqi=100,
            max_aqi=150,
            aqi_readings=readings
        )
        
        profile = HealthProfile(
            age_group="adult",
            respiratory_conditions=["asthma"],
            pollution_sensitivity=1.5,
            activity_level="moderate"
        )
        
        # Measure performance
        start_time = time.time()
        impact = health_service.calculate_comprehensive_health_impact(
            large_route_data, profile, 45, "car"
        )
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        assert isinstance(impact, HealthImpactEstimate)