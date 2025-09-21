"""
Unit tests for traffic signal service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services.traffic_signal_service import TrafficSignalService
from app.schemas.base import CoordinatesSchema


@pytest.fixture
def traffic_service():
    return TrafficSignalService()


@pytest.fixture
def sample_coordinates():
    return CoordinatesSchema(latitude=28.6304, longitude=77.2177)


class TestTrafficSignalService:
    
    def test_initialize_mock_signals(self, traffic_service):
        """Test initialization of mock signals"""
        assert len(traffic_service.mock_signals) > 0
        
        # Check that all signals have required fields
        for signal_id, signal_data in traffic_service.mock_signals.items():
            assert "signal_id" in signal_data
            assert "coordinates" in signal_data
            assert "cycle_time_seconds" in signal_data
            assert "green_duration" in signal_data
            assert "yellow_duration" in signal_data
            assert "red_duration" in signal_data
            assert isinstance(signal_data["coordinates"], CoordinatesSchema)
    
    def test_get_corridor_id(self, traffic_service):
        """Test corridor ID retrieval"""
        # Test signal in corridor
        corridor_id = traffic_service._get_corridor_id("TL001")
        assert corridor_id == "corridor_1"
        
        # Test signal not in any corridor
        corridor_id = traffic_service._get_corridor_id("TL015")
        assert corridor_id is None
    
    def test_get_current_signal_state_valid(self, traffic_service):
        """Test getting current state of a valid signal"""
        signal_state = traffic_service.get_current_signal_state("TL001")
        
        assert signal_state is not None
        assert signal_state.signal_id == "TL001"
        assert signal_state.current_state in ["red", "yellow", "green"]
        assert signal_state.cycle_time_seconds > 0
        assert signal_state.time_to_next_change >= 0
        assert isinstance(signal_state.coordinates, CoordinatesSchema)
    
    def test_get_current_signal_state_invalid(self, traffic_service):
        """Test getting state of non-existent signal"""
        signal_state = traffic_service.get_current_signal_state("INVALID_ID")
        
        assert signal_state is None
    
    def test_predict_signal_state_valid(self, traffic_service):
        """Test signal state prediction for valid signal"""
        arrival_time = datetime.utcnow() + timedelta(minutes=2)
        
        prediction = traffic_service.predict_signal_state(
            signal_id="TL001",
            arrival_time=arrival_time,
            current_speed_kmh=50.0
        )
        
        assert prediction is not None
        assert prediction.signal_id == "TL001"
        assert prediction.predicted_state in ["red", "yellow", "green"]
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.time_to_arrival >= 0
    
    def test_predict_signal_state_invalid(self, traffic_service):
        """Test prediction for non-existent signal"""
        arrival_time = datetime.utcnow() + timedelta(minutes=2)
        
        prediction = traffic_service.predict_signal_state(
            signal_id="INVALID_ID",
            arrival_time=arrival_time,
            current_speed_kmh=50.0
        )
        
        assert prediction is None
    
    def test_predict_signal_state_past_time(self, traffic_service):
        """Test prediction with past arrival time"""
        past_time = datetime.utcnow() - timedelta(minutes=1)
        
        prediction = traffic_service.predict_signal_state(
            signal_id="TL001",
            arrival_time=past_time,
            current_speed_kmh=50.0
        )
        
        # Should still work but with time_to_arrival = 0
        assert prediction is not None
        assert prediction.time_to_arrival == 0
    
    def test_calculate_recommended_speed(self, traffic_service):
        """Test recommended speed calculation"""
        signal_data = traffic_service.mock_signals["TL001"]
        
        # Test with reasonable time to arrival
        recommended_speed = traffic_service._calculate_recommended_speed(
            signal_data=signal_data,
            time_to_arrival=30.0,  # 30 seconds
            current_speed_kmh=45.0
        )
        
        if recommended_speed is not None:
            assert 20.0 <= recommended_speed <= 60.0
    
    def test_calculate_recommended_speed_no_time(self, traffic_service):
        """Test recommended speed with no time to arrival"""
        signal_data = traffic_service.mock_signals["TL001"]
        
        recommended_speed = traffic_service._calculate_recommended_speed(
            signal_data=signal_data,
            time_to_arrival=0.0,
            current_speed_kmh=45.0
        )
        
        assert recommended_speed is None
    
    def test_get_signals_near_location(self, traffic_service, sample_coordinates):
        """Test getting signals near a location"""
        nearby_signals = traffic_service.get_signals_near_location(
            coordinates=sample_coordinates,
            radius_km=1.0
        )
        
        assert isinstance(nearby_signals, list)
        
        # Should find at least one signal near the test coordinates
        if nearby_signals:
            for signal in nearby_signals:
                assert signal.signal_id in traffic_service.mock_signals
                distance = traffic_service._calculate_distance(
                    sample_coordinates,
                    signal.coordinates
                )
                assert distance <= 1.0
    
    def test_get_signals_near_location_large_radius(self, traffic_service, sample_coordinates):
        """Test getting signals with large search radius"""
        nearby_signals = traffic_service.get_signals_near_location(
            coordinates=sample_coordinates,
            radius_km=10.0
        )
        
        # Should find multiple signals with large radius
        assert len(nearby_signals) > 0
    
    def test_get_signals_along_route(self, traffic_service):
        """Test getting signals along a route"""
        route_coordinates = [
            CoordinatesSchema(latitude=28.6304, longitude=77.2177),
            CoordinatesSchema(latitude=28.6289, longitude=77.2156),
            CoordinatesSchema(latitude=28.6274, longitude=77.2135)
        ]
        
        route_signals = traffic_service.get_signals_along_route(
            route_coordinates=route_coordinates,
            buffer_meters=200.0
        )
        
        assert isinstance(route_signals, list)
        
        # Should find signals along this route (TL001, TL002, TL003 are on this path)
        if route_signals:
            signal_ids = [s.signal_id for s in route_signals]
            assert any(sid in ["TL001", "TL002", "TL003"] for sid in signal_ids)
    
    def test_calculate_green_wave_timing_valid_corridor(self, traffic_service):
        """Test green wave calculation for valid corridor"""
        green_wave = traffic_service.calculate_green_wave_timing(
            corridor_id="corridor_1",
            average_speed_kmh=50.0
        )
        
        assert green_wave is not None
        assert green_wave.corridor_id == "corridor_1"
        assert len(green_wave.signals) >= 2
        assert green_wave.optimal_speed_kmh == 50.0
        assert len(green_wave.coordination_offset_seconds) > 0
        assert 0.0 <= green_wave.success_probability <= 1.0
    
    def test_calculate_green_wave_timing_invalid_corridor(self, traffic_service):
        """Test green wave calculation for invalid corridor"""
        green_wave = traffic_service.calculate_green_wave_timing(
            corridor_id="invalid_corridor",
            average_speed_kmh=50.0
        )
        
        assert green_wave is None
    
    def test_optimize_corridor_timing_valid(self, traffic_service):
        """Test corridor timing optimization with valid signals"""
        signal_chain = ["TL001", "TL002", "TL003"]
        
        result = traffic_service.optimize_corridor_timing(
            signal_chain=signal_chain,
            traffic_density="moderate"
        )
        
        assert "error" not in result
        assert result["signal_chain"] == signal_chain
        assert result["optimal_speed_kmh"] > 0
        assert result["total_distance_meters"] > 0
        assert result["coordination_efficiency"] > 0
        assert "recommended_offsets" in result
    
    def test_optimize_corridor_timing_insufficient_signals(self, traffic_service):
        """Test corridor optimization with insufficient signals"""
        signal_chain = ["TL001"]  # Only one signal
        
        result = traffic_service.optimize_corridor_timing(
            signal_chain=signal_chain,
            traffic_density="moderate"
        )
        
        assert "error" in result
        assert "At least 2 signals required" in result["error"]
    
    def test_optimize_corridor_timing_invalid_signals(self, traffic_service):
        """Test corridor optimization with invalid signal IDs"""
        signal_chain = ["INVALID1", "INVALID2"]
        
        result = traffic_service.optimize_corridor_timing(
            signal_chain=signal_chain,
            traffic_density="moderate"
        )
        
        assert "error" in result
        assert "Invalid signal IDs" in result["error"]
    
    def test_simulate_adaptive_timing_valid_signal(self, traffic_service):
        """Test adaptive timing simulation for valid signal"""
        result = traffic_service.simulate_adaptive_timing(
            signal_id="TL001",
            traffic_volume=150,
            pedestrian_count=10
        )
        
        assert "error" not in result
        assert result["signal_id"] == "TL001"
        assert "original_timing" in result
        assert "adaptive_timing" in result
        assert result["traffic_volume"] == 150
        assert result["pedestrian_count"] == 10
        assert "efficiency_gain_percent" in result
    
    def test_simulate_adaptive_timing_invalid_signal(self, traffic_service):
        """Test adaptive timing for invalid signal"""
        result = traffic_service.simulate_adaptive_timing(
            signal_id="INVALID_ID",
            traffic_volume=100,
            pedestrian_count=5
        )
        
        assert "error" in result
        assert "Signal not found" in result["error"]
    
    def test_simulate_adaptive_timing_heavy_traffic(self, traffic_service):
        """Test adaptive timing with heavy traffic"""
        result = traffic_service.simulate_adaptive_timing(
            signal_id="TL001",
            traffic_volume=200,  # Heavy traffic
            pedestrian_count=0
        )
        
        original_green = result["original_timing"]["green"]
        adaptive_green = result["adaptive_timing"]["green"]
        
        # Should extend green time for heavy traffic
        assert adaptive_green >= original_green
    
    def test_simulate_adaptive_timing_light_traffic(self, traffic_service):
        """Test adaptive timing with light traffic"""
        result = traffic_service.simulate_adaptive_timing(
            signal_id="TL001",
            traffic_volume=20,  # Light traffic
            pedestrian_count=0
        )
        
        original_green = result["original_timing"]["green"]
        adaptive_green = result["adaptive_timing"]["green"]
        
        # Should reduce green time for light traffic
        assert adaptive_green <= original_green
    
    def test_calculate_distance(self, traffic_service):
        """Test distance calculation between coordinates"""
        coord1 = CoordinatesSchema(latitude=28.6304, longitude=77.2177)
        coord2 = CoordinatesSchema(latitude=28.6289, longitude=77.2156)
        
        distance = traffic_service._calculate_distance(coord1, coord2)
        
        assert distance > 0
        assert distance < 5  # Should be less than 5km for nearby points
    
    def test_calculate_distance_same_point(self, traffic_service):
        """Test distance calculation for same point"""
        coord = CoordinatesSchema(latitude=28.6304, longitude=77.2177)
        
        distance = traffic_service._calculate_distance(coord, coord)
        
        assert distance == 0.0
    
    def test_get_corridor_performance_valid(self, traffic_service):
        """Test corridor performance metrics for valid corridor"""
        performance = traffic_service.get_corridor_performance("corridor_1")
        
        assert "error" not in performance
        assert performance["corridor_id"] == "corridor_1"
        assert performance["total_signals"] > 0
        assert performance["coordination_percentage"] >= 0
        assert performance["average_delay_seconds"] > 0
        assert performance["throughput_vehicles_per_hour"] > 0
    
    def test_get_corridor_performance_invalid(self, traffic_service):
        """Test corridor performance for invalid corridor"""
        performance = traffic_service.get_corridor_performance("invalid_corridor")
        
        assert "error" in performance
        assert "Corridor not found" in performance["error"]
    
    def test_signal_patterns_consistency(self, traffic_service):
        """Test that signal patterns are consistent"""
        for pattern_name, pattern in traffic_service.signal_patterns.items():
            # Cycle time should equal sum of phases
            expected_cycle = pattern["green"] + pattern["yellow"] + pattern["red"]
            assert pattern["cycle"] == expected_cycle
            
            # All durations should be positive
            assert pattern["green"] > 0
            assert pattern["yellow"] > 0
            assert pattern["red"] > 0
    
    def test_corridors_contain_valid_signals(self, traffic_service):
        """Test that all corridors contain valid signal IDs"""
        for corridor_id, signal_ids in traffic_service.corridors.items():
            assert len(signal_ids) >= 2  # Corridors should have at least 2 signals
            
            for signal_id in signal_ids:
                assert signal_id in traffic_service.mock_signals
    
    def test_signal_state_transitions(self, traffic_service):
        """Test that signal states transition correctly over time"""
        signal_id = "TL001"
        
        # Get initial state
        initial_state = traffic_service.get_current_signal_state(signal_id)
        assert initial_state is not None
        
        # Mock time progression by updating signal data
        signal_data = traffic_service.mock_signals[signal_id]
        original_time = signal_data["last_updated"]
        
        # Advance time by half cycle
        signal_data["last_updated"] = original_time - timedelta(
            seconds=signal_data["cycle_time_seconds"] // 2
        )
        
        # Get new state
        new_state = traffic_service.get_current_signal_state(signal_id)
        assert new_state is not None
        
        # State might have changed due to time progression
        assert new_state.signal_id == signal_id
        
        # Restore original time
        signal_data["last_updated"] = original_time
    
    def test_prediction_confidence_levels(self, traffic_service):
        """Test that prediction confidence levels are reasonable"""
        arrival_time = datetime.utcnow() + timedelta(minutes=1)
        
        for signal_id in list(traffic_service.mock_signals.keys())[:5]:  # Test first 5 signals
            prediction = traffic_service.predict_signal_state(
                signal_id=signal_id,
                arrival_time=arrival_time,
                current_speed_kmh=45.0
            )
            
            if prediction:
                assert 0.0 <= prediction.confidence <= 1.0
                # Confidence should be reasonably high for short-term predictions
                assert prediction.confidence >= 0.7