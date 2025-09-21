"""
Unit tests for route optimizer service
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
import uuid

from app.services.route_optimizer import RouteOptimizer
from app.schemas.base import CoordinatesSchema
from app.schemas.route import RouteOption, RouteSegment
from app.schemas.user import UserPreferences, HealthProfile
from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate


@pytest.fixture
def route_optimizer():
    return RouteOptimizer()


@pytest.fixture
def sample_coordinates():
    return {
        "origin": CoordinatesSchema(latitude=28.6139, longitude=77.2090),
        "destination": CoordinatesSchema(latitude=28.6200, longitude=77.2150)
    }


@pytest.fixture
def sample_route():
    return RouteOption(
        id=uuid.uuid4(),
        start_coords=CoordinatesSchema(latitude=28.6139, longitude=77.2090),
        end_coords=CoordinatesSchema(latitude=28.6200, longitude=77.2150),
        waypoints=[
            CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            CoordinatesSchema(latitude=28.6170, longitude=77.2120),
            CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        ],
        distance_km=5.2,
        estimated_time_minutes=18,
        average_aqi=None,
        route_score=None,
        route_type="optimal"
    )


@pytest.fixture
def sample_user_preferences():
    return UserPreferences(
        prioritize_time=0.6,
        prioritize_air_quality=0.3,
        prioritize_safety=0.1,
        voice_alerts_enabled=True,
        gamification_enabled=True
    )


@pytest.fixture
def sample_health_profile():
    return HealthProfile(
        age_group="adult",
        respiratory_conditions=["asthma"],
        pollution_sensitivity=1.5,
        activity_level="moderate"
    )


@pytest.fixture
def sample_route_aqi_data():
    return RouteAQIData(
        route_coordinates=[
            CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        ],
        aqi_readings=[],
        average_aqi=85,
        max_aqi=120,
        pollution_hotspots=[]
    )


class TestRouteOptimizer:
    
    def test_initialization(self, route_optimizer):
        """Test route optimizer initialization"""
        assert route_optimizer.default_weights is not None
        assert route_optimizer.route_types is not None
        assert "fastest" in route_optimizer.route_types
        assert "cleanest" in route_optimizer.route_types
        assert "balanced" in route_optimizer.route_types
    
    def test_get_scoring_weights_default(self, route_optimizer):
        """Test getting default scoring weights"""
        weights = route_optimizer._get_scoring_weights(None, "balanced")
        
        assert isinstance(weights, dict)
        assert "time" in weights
        assert "air_quality" in weights
        assert "safety" in weights
        
        # Weights should sum to approximately 1.0
        total_weight = sum(weights.values())
        assert 0.9 <= total_weight <= 1.1
    
    def test_get_scoring_weights_with_preferences(self, route_optimizer, sample_user_preferences):
        """Test scoring weights with user preferences"""
        weights = route_optimizer._get_scoring_weights(sample_user_preferences, "balanced")
        
        assert weights["time"] == 0.6
        assert weights["air_quality"] == 0.3
        assert weights["safety"] == 0.1
    
    def test_get_scoring_weights_route_type(self, route_optimizer):
        """Test scoring weights for different route types"""
        fastest_weights = route_optimizer._get_scoring_weights(None, "fastest")
        cleanest_weights = route_optimizer._get_scoring_weights(None, "cleanest")
        
        assert fastest_weights["time"] > cleanest_weights["time"]
        assert cleanest_weights["air_quality"] > fastest_weights["air_quality"]
    
    def test_calculate_time_score(self, route_optimizer):
        """Test time efficiency score calculation"""
        # Test excellent time (10 minutes)
        score_excellent = route_optimizer._calculate_time_score(10)
        assert score_excellent == 100.0
        
        # Test moderate time (30 minutes)
        score_moderate = route_optimizer._calculate_time_score(30)
        assert 40 <= score_moderate <= 80
        
        # Test poor time (60+ minutes)
        score_poor = route_optimizer._calculate_time_score(70)
        assert score_poor == 20.0
    
    def test_calculate_aqi_score(self, route_optimizer):
        """Test AQI score calculation"""
        # Test good air quality
        score_good = route_optimizer._calculate_aqi_score(30)
        assert score_good == 100.0
        
        # Test moderate air quality
        score_moderate = route_optimizer._calculate_aqi_score(75)
        assert 50 <= score_moderate <= 90
        
        # Test unhealthy air quality
        score_unhealthy = route_optimizer._calculate_aqi_score(180)
        assert score_unhealthy <= 20
        
        # Test hazardous air quality
        score_hazardous = route_optimizer._calculate_aqi_score(350)
        assert score_hazardous <= 5
    
    def test_calculate_safety_score(self, route_optimizer, sample_route, sample_route_aqi_data):
        """Test safety score calculation"""
        # Test route with no hotspots
        safe_aqi_data = RouteAQIData(
            route_coordinates=sample_route_aqi_data.route_coordinates,
            aqi_readings=[],
            average_aqi=60,
            max_aqi=80,
            pollution_hotspots=[]
        )
        
        safety_score = route_optimizer._calculate_safety_score(sample_route, safe_aqi_data)
        assert 50 <= safety_score <= 100
        
        # Test route with pollution hotspots
        unsafe_aqi_data = RouteAQIData(
            route_coordinates=sample_route_aqi_data.route_coordinates,
            aqi_readings=[],
            average_aqi=150,
            max_aqi=200,
            pollution_hotspots=[CoordinatesSchema(latitude=28.6170, longitude=77.2120)]
        )
        
        unsafe_score = route_optimizer._calculate_safety_score(sample_route, unsafe_aqi_data)
        assert unsafe_score < safety_score
    
    def test_calculate_fuel_efficiency_score(self, route_optimizer, sample_route):
        """Test fuel efficiency score calculation"""
        # Test with good green wave score
        fuel_score_good = route_optimizer._calculate_fuel_efficiency_score(sample_route, 80.0)
        
        # Test with poor green wave score
        fuel_score_poor = route_optimizer._calculate_fuel_efficiency_score(sample_route, 30.0)
        
        assert fuel_score_good > fuel_score_poor
        assert 0 <= fuel_score_good <= 100
        assert 0 <= fuel_score_poor <= 100
    
    def test_calculate_comfort_score(self, route_optimizer, sample_route, sample_route_aqi_data):
        """Test comfort score calculation"""
        comfort_score = route_optimizer._calculate_comfort_score(sample_route, sample_route_aqi_data)
        
        assert 0 <= comfort_score <= 100
        assert isinstance(comfort_score, float)
    
    def test_calculate_green_wave_score_no_signals(self, route_optimizer):
        """Test green wave score with no signals"""
        score = route_optimizer._calculate_green_wave_score([], 5.0, 20)
        
        assert score == 70.0  # Neutral score for no signals
    
    def test_calculate_green_wave_score_with_signals(self, route_optimizer):
        """Test green wave score with coordinated signals"""
        from app.schemas.route import TrafficSignalState
        
        # Mock coordinated signals
        mock_signals = [
            TrafficSignalState(
                signal_id="TL001",
                coordinates=CoordinatesSchema(latitude=28.6139, longitude=77.2090),
                current_state="green",
                cycle_time_seconds=120,
                time_to_next_change=30,
                is_coordinated=True
            ),
            TrafficSignalState(
                signal_id="TL002",
                coordinates=CoordinatesSchema(latitude=28.6170, longitude=77.2120),
                current_state="red",
                cycle_time_seconds=120,
                time_to_next_change=45,
                is_coordinated=True
            )
        ]
        
        score = route_optimizer._calculate_green_wave_score(mock_signals, 5.0, 20)
        
        assert score > 70.0  # Should be better than neutral
        assert score <= 100.0
    
    def test_calculate_distance(self, route_optimizer):
        """Test distance calculation"""
        coord1 = CoordinatesSchema(latitude=28.6139, longitude=77.2090)
        coord2 = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        distance = route_optimizer._calculate_distance(coord1, coord2)
        
        assert distance > 0
        assert distance < 10  # Should be reasonable for nearby points
    
    def test_calculate_route_score_basic(self, route_optimizer, sample_route, sample_route_aqi_data):
        """Test basic route score calculation"""
        score = route_optimizer._calculate_route_score(
            route=sample_route,
            route_aqi_data=sample_route_aqi_data,
            health_impact=None,
            green_wave_score=70.0,
            user_preferences=None,
            route_type="balanced"
        )
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_route_score_with_health_impact(self, route_optimizer, sample_route, sample_route_aqi_data):
        """Test route score with health impact penalty"""
        health_impact = HealthImpactEstimate(
            estimated_exposure_pm25=45.0,
            health_risk_score=80.0,  # High risk
            recommended_precautions=["Wear mask"],
            comparison_to_baseline=25.0
        )
        
        score_with_health = route_optimizer._calculate_route_score(
            route=sample_route,
            route_aqi_data=sample_route_aqi_data,
            health_impact=health_impact,
            green_wave_score=70.0,
            user_preferences=None,
            route_type="balanced"
        )
        
        score_without_health = route_optimizer._calculate_route_score(
            route=sample_route,
            route_aqi_data=sample_route_aqi_data,
            health_impact=None,
            green_wave_score=70.0,
            user_preferences=None,
            route_type="balanced"
        )
        
        # Score with health impact should be lower due to penalty
        assert score_with_health < score_without_health
    
    def test_determine_recommendation_time_priority(self, route_optimizer, sample_route):
        """Test recommendation with time priority"""
        fast_route = sample_route
        clean_route = RouteOption(
            id=uuid.uuid4(),
            start_coords=sample_route.start_coords,
            end_coords=sample_route.end_coords,
            waypoints=sample_route.waypoints,
            distance_km=6.0,
            estimated_time_minutes=25,
            average_aqi=60,
            route_score=75.0,
            route_type="clean"
        )
        
        time_preferences = UserPreferences(
            prioritize_time=0.8,
            prioritize_air_quality=0.1,
            prioritize_safety=0.1
        )
        
        recommendation = route_optimizer._determine_recommendation(
            fast_route, clean_route, None, time_preferences
        )
        
        assert recommendation == "fast"
    
    def test_determine_recommendation_aqi_priority(self, route_optimizer, sample_route):
        """Test recommendation with AQI priority"""
        fast_route = sample_route
        clean_route = RouteOption(
            id=uuid.uuid4(),
            start_coords=sample_route.start_coords,
            end_coords=sample_route.end_coords,
            waypoints=sample_route.waypoints,
            distance_km=6.0,
            estimated_time_minutes=25,
            average_aqi=60,
            route_score=75.0,
            route_type="clean"
        )
        
        aqi_preferences = UserPreferences(
            prioritize_time=0.1,
            prioritize_air_quality=0.8,
            prioritize_safety=0.1
        )
        
        recommendation = route_optimizer._determine_recommendation(
            fast_route, clean_route, None, aqi_preferences
        )
        
        assert recommendation == "clean"
    
    def test_create_enhanced_segments(self, route_optimizer, sample_route_aqi_data):
        """Test creation of enhanced route segments"""
        base_segments = [
            RouteSegment(
                start_point=CoordinatesSchema(latitude=28.6139, longitude=77.2090),
                end_point=CoordinatesSchema(latitude=28.6170, longitude=77.2120),
                distance_meters=2500,
                aqi_level=0,
                traffic_signals=[],
                estimated_travel_time=300
            )
        ]
        
        enhanced_segments = route_optimizer._create_enhanced_segments(
            base_segments=base_segments,
            route_aqi_data=sample_route_aqi_data,
            route_signals=[]
        )
        
        assert len(enhanced_segments) == 1
        assert enhanced_segments[0].aqi_level == sample_route_aqi_data.average_aqi
    
    @pytest.mark.asyncio
    async def test_calculate_route_efficiency_metrics(self, route_optimizer, sample_route):
        """Test route efficiency metrics calculation"""
        metrics = await route_optimizer.calculate_route_efficiency_metrics(sample_route)
        
        assert "route_id" in metrics
        assert "distance_km" in metrics
        assert "estimated_time_minutes" in metrics
        assert "average_speed_kmh" in metrics
        assert "estimated_fuel_liters" in metrics
        assert "estimated_co2_kg" in metrics
        
        assert metrics["distance_km"] == sample_route.distance_km
        assert metrics["estimated_time_minutes"] == sample_route.estimated_time_minutes
        assert metrics["average_speed_kmh"] > 0
    
    @pytest.mark.asyncio
    async def test_calculate_route_efficiency_metrics_with_baseline(self, route_optimizer, sample_route):
        """Test efficiency metrics with baseline comparison"""
        baseline_route = RouteOption(
            id=uuid.uuid4(),
            start_coords=sample_route.start_coords,
            end_coords=sample_route.end_coords,
            waypoints=sample_route.waypoints,
            distance_km=6.0,
            estimated_time_minutes=25,
            average_aqi=120,
            route_score=60.0,
            route_type="baseline"
        )
        
        metrics = await route_optimizer.calculate_route_efficiency_metrics(
            route=sample_route,
            baseline_route=baseline_route
        )
        
        assert "time_efficiency" in metrics
        assert "distance_efficiency" in metrics
        assert "aqi_improvement" in metrics
        
        # Sample route should be more efficient (shorter time/distance)
        assert metrics["time_efficiency"] > 1.0
        assert metrics["distance_efficiency"] > 1.0
    
    @pytest.mark.asyncio
    async def test_optimize_route_integration(self, route_optimizer, sample_coordinates, sample_user_preferences):
        """Test route optimization integration (mocked)"""
        with patch('app.services.maps_service.maps_service.get_multiple_route_options') as mock_maps:
            with patch('app.services.aqi_service.aqi_service.get_route_aqi_data') as mock_aqi:
                with patch('app.services.traffic_signal_service.traffic_signal_service.get_signals_along_route') as mock_signals:
                    
                    # Mock responses
                    mock_maps.return_value = [sample_route]
                    mock_aqi.return_value = sample_route_aqi_data
                    mock_signals.return_value = []
                    
                    routes = await route_optimizer.optimize_route(
                        origin=sample_coordinates["origin"],
                        destination=sample_coordinates["destination"],
                        user_preferences=sample_user_preferences,
                        route_type="balanced"
                    )
                    
                    assert len(routes) > 0
                    assert routes[0].route_score is not None
                    assert routes[0].average_aqi is not None
    
    @pytest.mark.asyncio
    async def test_optimize_route_no_base_routes(self, route_optimizer, sample_coordinates):
        """Test optimization when no base routes are found"""
        with patch('app.services.maps_service.maps_service.get_multiple_route_options') as mock_maps:
            mock_maps.return_value = []
            
            routes = await route_optimizer.optimize_route(
                origin=sample_coordinates["origin"],
                destination=sample_coordinates["destination"],
                route_type="balanced"
            )
            
            assert routes == []
    
    @pytest.mark.asyncio
    async def test_compare_routes_integration(self, route_optimizer, sample_coordinates):
        """Test route comparison integration (mocked)"""
        with patch.object(route_optimizer, 'optimize_route') as mock_optimize:
            fast_route = RouteOption(
                id=uuid.uuid4(),
                start_coords=sample_coordinates["origin"],
                end_coords=sample_coordinates["destination"],
                waypoints=[sample_coordinates["origin"], sample_coordinates["destination"]],
                distance_km=4.5,
                estimated_time_minutes=15,
                average_aqi=100,
                route_score=85.0,
                route_type="fastest"
            )
            
            clean_route = RouteOption(
                id=uuid.uuid4(),
                start_coords=sample_coordinates["origin"],
                end_coords=sample_coordinates["destination"],
                waypoints=[sample_coordinates["origin"], sample_coordinates["destination"]],
                distance_km=5.2,
                estimated_time_minutes=22,
                average_aqi=70,
                route_score=80.0,
                route_type="cleanest"
            )
            
            # Mock different responses for different route types
            def mock_optimize_side_effect(*args, **kwargs):
                route_type = kwargs.get('route_type', 'balanced')
                if route_type == "fastest":
                    return [fast_route]
                elif route_type == "cleanest":
                    return [clean_route]
                else:
                    return [fast_route]  # balanced fallback
            
            mock_optimize.side_effect = mock_optimize_side_effect
            
            comparison = await route_optimizer.compare_routes(
                origin=sample_coordinates["origin"],
                destination=sample_coordinates["destination"]
            )
            
            assert comparison is not None
            assert comparison.fast_route == fast_route
            assert comparison.clean_route == clean_route
            assert comparison.recommendation in ["fast", "clean", "balanced"]