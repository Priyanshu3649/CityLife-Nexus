"""
Data interpolation service for filling gaps in AQI, signal, and traffic data
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from app.schemas.base import CoordinatesSchema
import math

logger = logging.getLogger(__name__)


class InterpolationService:
    """Service for interpolating missing data points using various algorithms"""
    
    def __init__(self):
        pass
    
    def idw_interpolation(
        self,
        target_point: CoordinatesSchema,
        known_points: List[Tuple[CoordinatesSchema, float]],
        power: float = 2.0
    ) -> float:
        """
        Inverse Distance Weighting interpolation for estimating values at unknown points
        
        Args:
            target_point: Point where value needs to be estimated
            known_points: List of (coordinates, value) tuples
            power: Power parameter for IDW (default 2.0)
            
        Returns:
            Interpolated value at target point
        """
        if not known_points:
            return 0.0
            
        # If target point matches a known point exactly, return that value
        for coords, value in known_points:
            if (abs(coords.latitude - target_point.latitude) < 1e-6 and 
                abs(coords.longitude - target_point.longitude) < 1e-6):
                return value
        
        # Calculate IDW
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for coords, value in known_points:
            distance = self._calculate_distance(target_point, coords)
            
            # Avoid division by zero
            if distance < 1e-10:
                return value
                
            weight = 1.0 / (distance ** power)
            weighted_sum += value * weight
            weight_sum += weight
        
        if weight_sum == 0:
            # Fallback to average if all weights are zero
            return sum(value for _, value in known_points) / len(known_points)
        
        return weighted_sum / weight_sum
    
    def linear_interpolation(
        self,
        x: float,
        x1: float,
        x2: float,
        y1: float,
        y2: float
    ) -> float:
        """
        Linear interpolation between two points
        
        Args:
            x: Target x value
            x1, x2: Known x values
            y1, y2: Known y values
            
        Returns:
            Interpolated y value
        """
        if x2 == x1:
            return y1
            
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    
    def temporal_interpolation(
        self,
        target_time: datetime,
        time1: datetime,
        time2: datetime,
        value1: float,
        value2: float
    ) -> float:
        """
        Temporal interpolation between two time points
        
        Args:
            target_time: Target time for interpolation
            time1, time2: Known time points
            value1, value2: Values at known time points
            
        Returns:
            Interpolated value at target time
        """
        if time2 == time1:
            return value1
            
        # Calculate time ratios
        total_duration = (time2 - time1).total_seconds()
        target_duration = (target_time - time1).total_seconds()
        
        if total_duration == 0:
            return value1
            
        ratio = target_duration / total_duration
        ratio = max(0.0, min(1.0, ratio))  # Clamp between 0 and 1
        
        return value1 + (value2 - value1) * ratio
    
    def bilinear_interpolation(
        self,
        target_point: CoordinatesSchema,
        grid_points: List[Tuple[CoordinatesSchema, float]]
    ) -> float:
        """
        Bilinear interpolation for 2D grid data
        
        Args:
            target_point: Point where value needs to be estimated
            grid_points: List of 4 (coordinates, value) tuples forming a grid
            
        Returns:
            Interpolated value at target point
        """
        if len(grid_points) < 4:
            # Fall back to IDW if not enough points
            return self.idw_interpolation(target_point, grid_points)
        
        # Sort points to form a grid
        sorted_points = sorted(grid_points, key=lambda p: (p[0].latitude, p[0].longitude))
        
        # Extract the four corner points
        p1, p2, p3, p4 = sorted_points[:4]  # (lat1,lon1), (lat1,lon2), (lat2,lon1), (lat2,lon2)
        
        # Perform bilinear interpolation
        # First interpolate in latitude direction
        val1 = self.linear_interpolation(
            target_point.latitude,
            p1[0].latitude,
            p3[0].latitude,
            p1[1],
            p3[1]
        )
        
        val2 = self.linear_interpolation(
            target_point.latitude,
            p2[0].latitude,
            p4[0].latitude,
            p2[1],
            p4[1]
        )
        
        # Then interpolate in longitude direction
        result = self.linear_interpolation(
            target_point.longitude,
            p1[0].longitude,
            p2[0].longitude,
            val1,
            val2
        )
        
        return result
    
    def interpolate_aqi_along_route(
        self,
        route_waypoints: List[CoordinatesSchema],
        aqi_readings: List[Tuple[CoordinatesSchema, float]]
    ) -> List[float]:
        """
        Interpolate AQI values along a route
        
        Args:
            route_waypoints: List of coordinates along the route
            aqi_readings: List of (coordinates, aqi_value) tuples
            
        Returns:
            List of interpolated AQI values for each waypoint
        """
        if not route_waypoints:
            return []
            
        if not aqi_readings:
            # Return default AQI if no readings available
            return [100.0] * len(route_waypoints)
        
        interpolated_aqi = []
        
        for waypoint in route_waypoints:
            aqi = self.idw_interpolation(waypoint, aqi_readings, power=2.0)
            interpolated_aqi.append(max(0.0, aqi))  # AQI should be non-negative
        
        return interpolated_aqi
    
    def interpolate_signal_timing(
        self,
        target_signal: CoordinatesSchema,
        known_signals: List[Tuple[CoordinatesSchema, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Interpolate signal timing data for a target signal
        
        Args:
            target_signal: Coordinates of signal to estimate
            known_signals: List of (coordinates, signal_data) tuples
            
        Returns:
            Interpolated signal timing data
        """
        if not known_signals:
            # Return default signal timing
            return {
                "cycle_duration": 90,
                "green_duration": 30,
                "yellow_duration": 3,
                "red_duration": 57,
                "offset": 0
            }
        
        # Interpolate each timing parameter
        cycle_durations = [(coords, data.get("cycle_duration", 90)) for coords, data in known_signals]
        green_durations = [(coords, data.get("green_duration", 30)) for coords, data in known_signals]
        yellow_durations = [(coords, data.get("yellow_duration", 3)) for coords, data in known_signals]
        
        cycle_duration = self.idw_interpolation(target_signal, cycle_durations)
        green_duration = self.idw_interpolation(target_signal, green_durations)
        yellow_duration = self.idw_interpolation(target_signal, yellow_durations)
        red_duration = max(0, cycle_duration - green_duration - yellow_duration)
        
        # Interpolate offset
        offsets = [(coords, data.get("offset", 0)) for coords, data in known_signals]
        offset = self.idw_interpolation(target_signal, offsets)
        
        return {
            "cycle_duration": max(30, cycle_duration),  # Minimum 30 seconds
            "green_duration": max(10, min(cycle_duration - 10, green_duration)),
            "yellow_duration": max(3, min(10, yellow_duration)),
            "red_duration": max(10, red_duration),
            "offset": offset
        }
    
    def smooth_time_series(
        self,
        data_points: List[Tuple[datetime, float]],
        window_size: int = 5
    ) -> List[Tuple[datetime, float]]:
        """
        Apply moving average smoothing to time series data
        
        Args:
            data_points: List of (timestamp, value) tuples
            window_size: Size of moving average window
            
        Returns:
            Smoothed data points
        """
        if len(data_points) <= window_size:
            return data_points
            
        smoothed = []
        
        for i in range(len(data_points)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(data_points), i + window_size // 2 + 1)
            
            window_values = [data_points[j][1] for j in range(start_idx, end_idx)]
            smoothed_value = sum(window_values) / len(window_values)
            
            smoothed.append((data_points[i][0], smoothed_value))
        
        return smoothed
    
    def fill_missing_data(
        self,
        data_points: List[Optional[float]],
        method: str = "linear"
    ) -> List[float]:
        """
        Fill missing data points in a series
        
        Args:
            data_points: List of values with None for missing data
            method: Interpolation method ("linear", "previous", "next")
            
        Returns:
            List with missing data filled
        """
        if not data_points:
            return []
        
        filled_data = data_points.copy()
        
        if method == "linear":
            # Linear interpolation for missing values
            i = 0
            while i < len(filled_data):
                if filled_data[i] is None:
                    # Find next non-None value
                    j = i + 1
                    while j < len(filled_data) and filled_data[j] is None:
                        j += 1
                    
                    # If we found a value, interpolate
                    if j < len(filled_data) and i > 0:
                        start_val = filled_data[i-1]
                        end_val = filled_data[j]
                        interval = j - i + 1
                        
                        for k in range(i, j):
                            ratio = (k - i + 1) / interval
                            filled_data[k] = start_val + (end_val - start_val) * ratio
                    elif i == 0 and j < len(filled_data):
                        # Fill leading None values with first known value
                        for k in range(j):
                            filled_data[k] = filled_data[j]
                    elif i > 0:
                        # Fill trailing None values with last known value
                        for k in range(i, len(filled_data)):
                            filled_data[k] = filled_data[i-1]
                
                i += 1
        
        elif method == "previous":
            # Fill with previous known value
            last_known = None
            for i in range(len(filled_data)):
                if filled_data[i] is not None:
                    last_known = filled_data[i]
                elif last_known is not None:
                    filled_data[i] = last_known
        
        elif method == "next":
            # Fill with next known value
            next_known = None
            for i in range(len(filled_data) - 1, -1, -1):
                if filled_data[i] is not None:
                    next_known = filled_data[i]
                elif next_known is not None:
                    filled_data[i] = next_known
        
        # Convert any remaining None values to 0
        for i in range(len(filled_data)):
            if filled_data[i] is None:
                filled_data[i] = 0.0
        
        return filled_data
    
    def _calculate_distance(
        self,
        coord1: CoordinatesSchema,
        coord2: CoordinatesSchema
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r


# Global instance
interpolation_service = InterpolationService()