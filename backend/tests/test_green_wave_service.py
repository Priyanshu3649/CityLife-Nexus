"""
Unit tests for green wave service
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.green_wave_service import GreenWaveService
from app.schemas.base import CoordinatesSchema
from app.schemas.route import TrafficSignalState


@pytest.fixture
def green_wave_service():
    return GreenWaveService()


@pytest.fixture
def mock_signal_states():
    """Mock traffic signal states for testing"""
    return [
        TrafficSignalState(
            signal_id="TL001",
            coordinates=CoordinatesSchema(latitude=28.6304, longitude=77.2177),
            current_state="green",
            cycle_time_seconds=120,
            time_to_next_change=30,
            is_coordinated=True
        ),
        TrafficSignalState(
            signal_id="TL002",
            coordinates=CoordinatesSchema(latitude=28.6289, longitude=77.2156),
            current_state="red",
            cycle_time_seconds=120,
            time_to_next_change=45,
            is_coordinated=True
        ),
        TrafficSignalState(
            signal_id="TL003",
            coordinates=CoordinatesSchema(latitude=28.6274, longitude=77.2135),
            current_state="green",
            cycle_time_seconds=120,
            time_to_next_change=60,
            is_coordinated=False
        )
    ]


class TestGreenWaveService:
    
    def test_initialization(self, green_wave_service):
        """Test green wave service initialization"""
        assert green_wave_service.optimal_speed_range == (40, 60)
        assert green_wave_service.max_coordination_distance == 5.0
        assert green_wave_service.min_signals_for_wave == 2
        assert "urban" in green_wave_service.flow_models
        assert "arterial" in green_wave_service.flow_models
        assert "highway" in green_wave_service.flow_models
    
    def test_calculate_green_wave_offset_basic(self, green_wave_service):
        """Test basic green wave offset calculation"""
        offset = green_wave_service.calculate_green_wave_offset(
            distance_meters=500,
            average_speed_kmh=50,
            signal_cycle_time=120
        )
        
        # 500m at 50 km/h = 36 seconds travel time
        expected_offset = 36  # Should be around 36 seconds
        assert abs(offset - expected_offset) <= 2  # Allow small variance
    
    def test_calculate_green_wave_offset_different_speeds(self, green_wave_service):
        """Test offset calculation with different speeds"""
        distance = 600  # meters
        cycle_time = 120
        
        # Slower speed should result in larger offset
        offset_slow = green_wave_service.calculate_green_wave_offset(
            distance, 30, cycle_time
        )
        
        # Faster speed should result in smaller offset
        offset_fast = green_wave_service.calculate_green_wave_offset(
            distance, 60, cycle_time
        )
        
        assert offset_slow > offset_fast
    
    def test_calculate_green_wave_offset_cycle_wrap(self, green_wave_service):
        """Test offset calculation with cycle time wrapping"""
        # Long distance that exceeds one cycle
        offset = green_wave_service.calculate_green_wave_offset(
            distance_meters=2000,  # 2km
            average_speed_kmh=40,   # Will take 180 seconds
            signal_cycle_time=120   # Should wrap around
        )
        
        # 180 seconds % 120 = 60 seconds
        assert offset == 60
    
    def test_optimize_corridor_timing_insufficient_signals(self, green_wave_service):
        """Test corridor optimization with insufficient signals"""
        result = green_wave_service.optimize_corridor_timing(
            signal_chain=["TL001"],  # Only one signal
            target_speed_kmh=50.0
        )
        
        assert "error" in result
        assert "Minimum 2 signals required" in result["error"]
    
    def test_optimize_corridor_timing_valid(self, green_wave_service, mock_signal_states):
        """Test corridor optimization with valid signals"""
        with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
            # Return mock signal states in sequence
            mock_get.side_effect = mock_signal_states
            
            result = green_wave_service.optimize_corridor_timing(
                signal_chain=["TL001", "TL002", "TL003"],
                target_speed_kmh=50.0,
                traffic_density="moderate"
            )
            
            assert "error" not in result
            assert result["total_signals"] == 3
            assert result["optimized_speed_kmh"] > 0
            assert "recommended_offsets" in result
            assert len(result["recommended_offsets"]) == 2  # n-1 offsets for n signals
            assert "coordination_efficiency" in result
            assert "performance_gains" in result
    
    def test_optimize_corridor_timing_no_valid_signals(self, green_wave_service):
        """Test corridor optimization with no valid signals"""
        with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
            mock_get.return_value = None  # No valid signals
            
            result = green_wave_service.optimize_corridor_timing(
                signal_chain=["INVALID1", "INVALID2"],
                target_speed_kmh=50.0
            )
            
            assert "error" in result
            assert "Insufficient valid signals" in result["error"]
    
    def test_simulate_green_wave_progression_invalid_corridor(self, green_wave_service):
        """Test simulation with invalid corridor"""
        result = green_wave_service.simulate_green_wave_progression(
            corridor_id="invalid_corridor",
            vehicle_speed_kmh=50.0,
            start_time=datetime.utcnow()
        )
        
        assert "error" in result
        assert "Corridor not found" in result["error"]
    
    def test_simulate_green_wave_progression_valid(self, green_wave_service, mock_signal_states):
        """Test valid green wave simulation"""
        with patch('app.services.traffic_signal_service.traffic_signal_service.corridors') as mock_corridors:
            with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
                with patch('app.services.traffic_signal_service.traffic_signal_service.predict_signal_state') as mock_predict:
                    
                    # Mock corridor data
                    mock_corridors.__contains__ = lambda self, key: key == "corridor_1"
                    mock_corridors.__getitem__ = lambda self, key: ["TL001", "TL002", "TL003"]
                    
                    # Mock signal states
                    mock_get.side_effect = mock_signal_states
                    
                    # Mock predictions
                    from app.schemas.route import SignalPrediction
                    mock_predict.return_value = SignalPrediction(
                        signal_id="TL001",
                        predicted_state="green",
                        confidence=0.9,
                        time_to_arrival=30,
                        recommended_speed=50.0
                    )
                    
                    result = green_wave_service.simulate_green_wave_progression(
                        corridor_id="corridor_1",
                        vehicle_speed_kmh=50.0,
                        start_time=datetime.utcnow()
                    )
                    
                    assert "error" not in result
                    assert result["corridor_id"] == "corridor_1"
                    assert result["simulation_speed_kmh"] == 50.0
                    assert "signal_encounters" in result
                    assert "performance_summary" in result
                    assert len(result["signal_encounters"]) == 3
    
    def test_calculate_bandwidth_efficiency_insufficient_signals(self, green_wave_service):
        """Test bandwidth calculation with insufficient signals"""
        with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
            mock_get.return_value = None
            
            result = green_wave_service.calculate_bandwidth_efficiency(
                signal_chain=["TL001"],
                speed_range=(40, 60)
            )
            
            assert "error" in result
            assert "Insufficient signals" in result["error"]
    
    def test_calculate_bandwidth_efficiency_valid(self, green_wave_service, mock_signal_states):
        """Test valid bandwidth efficiency calculation"""
        with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
            mock_get.side_effect = mock_signal_states[:2]  # Use first 2 signals
            
            result = green_wave_service.calculate_bandwidth_efficiency(
                signal_chain=["TL001", "TL002"],
                speed_range=(40, 60)
            )
            
            assert "error" not in result
            assert "signal_chain" in result
            assert "total_distance_meters" in result
            assert "speed_analysis" in result
            assert "optimal_speed" in result
            assert "coordination_potential" in result
            assert "recommendations" in result
            
            # Check speed analysis structure
            speed_analysis = result["speed_analysis"]
            assert len(speed_analysis) > 0
            for analysis in speed_analysis:
                assert "speed_kmh" in analysis
                assert "bandwidth_seconds" in analysis
                assert "efficiency_percent" in analysis
    
    def test_optimize_speed_for_conditions(self, green_wave_service):
        """Test speed optimization for different traffic conditions"""
        distances = [400, 500, 600]  # meters
        
        # Light traffic should allow higher speed
        light_speed = green_wave_service._optimize_speed_for_conditions(
            target_speed=50.0,
            traffic_density="light",
            distances=distances
        )
        
        # Heavy traffic should reduce speed
        heavy_speed = green_wave_service._optimize_speed_for_conditions(
            target_speed=50.0,
            traffic_density="heavy",
            distances=distances
        )
        
        # Moderate traffic should be close to target
        moderate_speed = green_wave_service._optimize_speed_for_conditions(
            target_speed=50.0,
            traffic_density="moderate",
            distances=distances
        )
        
        assert light_speed > moderate_speed > heavy_speed
        assert 25 <= light_speed <= 70  # Within bounds
        assert 25 <= heavy_speed <= 70  # Within bounds
    
    def test_optimize_speed_for_conditions_short_blocks(self, green_wave_service):
        """Test speed optimization with short blocks"""
        short_distances = [200, 250, 180]  # Short blocks
        
        speed = green_wave_service._optimize_speed_for_conditions(
            target_speed=50.0,
            traffic_density="moderate",
            distances=short_distances
        )
        
        # Should be reduced for short blocks
        assert speed < 50.0
    
    def test_optimize_speed_for_conditions_long_blocks(self, green_wave_service):
        """Test speed optimization with long blocks"""
        long_distances = [900, 1000, 850]  # Long blocks
        
        speed = green_wave_service._optimize_speed_for_conditions(
            target_speed=50.0,
            traffic_density="moderate",
            distances=long_distances
        )
        
        # Should be slightly increased for long blocks
        assert speed > 50.0
    
    def test_calculate_coordination_efficiency(self, green_wave_service, mock_signal_states):
        """Test coordination efficiency calculation"""
        signals_data = [
            {"state": signal} for signal in mock_signal_states
        ]
        distances = [500, 600]  # meters
        
        efficiency = green_wave_service._calculate_coordination_efficiency(
            signals_data=signals_data,
            distances=distances,
            speed_kmh=50.0
        )
        
        assert 0.0 <= efficiency <= 1.0
        assert isinstance(efficiency, float)
    
    def test_estimate_performance_gains(self, green_wave_service):
        """Test performance gains estimation"""
        gains = green_wave_service._estimate_performance_gains(
            signal_count=5,
            total_distance=2500.0,  # meters
            efficiency=0.8
        )
        
        assert "time_savings_percent" in gains
        assert "fuel_savings_percent" in gains
        assert "co2_reduction_percent" in gains
        assert "stops_reduced" in gains
        assert "estimated_time_saved_minutes" in gains
        assert "efficiency_score" in gains
        
        # Check reasonable ranges
        assert 0 <= gains["time_savings_percent"] <= 30
        assert 0 <= gains["fuel_savings_percent"] <= 20
        assert 0 <= gains["stops_reduced"] <= 5
    
    def test_calculate_bandwidth_for_speed(self, green_wave_service, mock_signal_states):
        """Test bandwidth calculation for specific speed"""
        distances = [500, 600]  # meters
        
        bandwidth = green_wave_service._calculate_bandwidth_for_speed(
            signals_data=mock_signal_states,
            distances=distances,
            speed_kmh=50.0
        )
        
        assert bandwidth >= 0
        assert isinstance(bandwidth, float)
    
    def test_assess_coordination_potential(self, green_wave_service, mock_signal_states):
        """Test coordination potential assessment"""
        assessment = green_wave_service._assess_coordination_potential(mock_signal_states)
        
        assert "cycle_consistency" in assessment
        assert "current_coordination_level" in assessment
        assert "potential_rating" in assessment
        assert "recommended_actions" in assessment
        
        # Check value ranges
        assert 0.0 <= assessment["cycle_consistency"] <= 1.0
        assert 0.0 <= assessment["current_coordination_level"] <= 1.0
        assert isinstance(assessment["recommended_actions"], list)
    
    def test_get_coordination_recommendations(self, green_wave_service):
        """Test coordination recommendations generation"""
        # Low consistency, low coordination
        recommendations_low = green_wave_service._get_coordination_recommendations(
            cycle_consistency=0.5,
            coordination_level=0.3
        )
        
        # High consistency, high coordination
        recommendations_high = green_wave_service._get_coordination_recommendations(
            cycle_consistency=0.9,
            coordination_level=0.8
        )
        
        assert isinstance(recommendations_low, list)
        assert isinstance(recommendations_high, list)
        assert len(recommendations_low) > 0
        assert len(recommendations_high) > 0
        
        # Low coordination should have more recommendations
        assert len(recommendations_low) >= len(recommendations_high)
    
    def test_generate_bandwidth_recommendations(self, green_wave_service, mock_signal_states):
        """Test bandwidth recommendations generation"""
        optimal_analysis = {
            "speed_kmh": 45,
            "efficiency_percent": 65
        }
        
        recommendations = green_wave_service._generate_bandwidth_recommendations(
            optimal_analysis=optimal_analysis,
            signals_data=mock_signal_states
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should include target speed recommendation
        speed_mentioned = any("45" in rec for rec in recommendations)
        assert speed_mentioned
    
    def test_calculate_distance(self, green_wave_service):
        """Test distance calculation between coordinates"""
        coord1 = CoordinatesSchema(latitude=28.6304, longitude=77.2177)
        coord2 = CoordinatesSchema(latitude=28.6289, longitude=77.2156)
        
        distance = green_wave_service._calculate_distance(coord1, coord2)
        
        assert distance > 0
        assert distance < 5  # Should be reasonable for nearby points in Delhi
        assert isinstance(distance, float)
    
    def test_calculate_distance_same_point(self, green_wave_service):
        """Test distance calculation for same coordinates"""
        coord = CoordinatesSchema(latitude=28.6304, longitude=77.2177)
        
        distance = green_wave_service._calculate_distance(coord, coord)
        
        assert distance == 0.0
    
    def test_error_handling_in_offset_calculation(self, green_wave_service):
        """Test error handling in offset calculation"""
        # Test with zero speed (should not crash)
        offset = green_wave_service.calculate_green_wave_offset(
            distance_meters=500,
            average_speed_kmh=0,  # Invalid speed
            signal_cycle_time=120
        )
        
        # Should return 0 on error
        assert offset == 0
    
    def test_corridor_optimization_with_mixed_coordination(self, green_wave_service):
        """Test corridor optimization with mixed coordination levels"""
        mixed_signals = [
            TrafficSignalState(
                signal_id="TL001",
                coordinates=CoordinatesSchema(latitude=28.6304, longitude=77.2177),
                current_state="green",
                cycle_time_seconds=120,
                time_to_next_change=30,
                is_coordinated=True  # Coordinated
            ),
            TrafficSignalState(
                signal_id="TL002",
                coordinates=CoordinatesSchema(latitude=28.6289, longitude=77.2156),
                current_state="red",
                cycle_time_seconds=90,   # Different cycle time
                time_to_next_change=45,
                is_coordinated=False  # Not coordinated
            )
        ]
        
        with patch('app.services.traffic_signal_service.traffic_signal_service.get_current_signal_state') as mock_get:
            mock_get.side_effect = mixed_signals
            
            result = green_wave_service.optimize_corridor_timing(
                signal_chain=["TL001", "TL002"],
                target_speed_kmh=50.0
            )
            
            assert "error" not in result
            # Should still work but with lower efficiency
            assert result["coordination_efficiency"] < 1.0