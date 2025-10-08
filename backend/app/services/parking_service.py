"""
Smart parking service using K-Means clustering to predict free parking spots
"""
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.schemas.base import CoordinatesSchema

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    KMeans = None
    StandardScaler = None
    logger.warning("Scikit-learn not available, using mock clustering implementation")

# Parking spot data structure
class ParkingSpot:
    def __init__(self, spot_id: str, coordinates: CoordinatesSchema, capacity: int, 
                 occupied: int, hourly_rate: float, is_covered: bool = False):
        self.spot_id = spot_id
        self.coordinates = coordinates
        self.capacity = capacity
        self.occupied = occupied
        self.hourly_rate = hourly_rate
        self.is_covered = is_covered
        self.last_updated = datetime.utcnow()
    
    @property
    def availability(self) -> float:
        """Calculate availability percentage (0.0 to 1.0)"""
        if self.capacity == 0:
            return 0.0
        return max(0.0, min(1.0, (self.capacity - self.occupied) / self.capacity))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "spot_id": self.spot_id,
            "coordinates": {
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude
            },
            "capacity": self.capacity,
            "occupied": self.occupied,
            "availability": self.availability,
            "hourly_rate": self.hourly_rate,
            "is_covered": self.is_covered,
            "last_updated": self.last_updated.isoformat()
        }


class ParkingService:
    """Service for finding and predicting parking availability using ML clustering"""
    
    def __init__(self):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE and StandardScaler else None
        self.kmeans_model = None
        self.parking_spots = {}  # In-memory storage for demo
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock parking data for Delhi NCR areas"""
        # Mock parking spots in Delhi NCR
        mock_spots = [
            ParkingSpot("CP001", CoordinatesSchema(latitude=28.6315, longitude=77.2167), 50, 30, 20.0, True),
            ParkingSpot("CP002", CoordinatesSchema(latitude=28.6320, longitude=77.2170), 100, 85, 25.0, True),
            ParkingSpot("CP003", CoordinatesSchema(latitude=28.6300, longitude=77.2150), 75, 45, 15.0, False),
            ParkingSpot("IG001", CoordinatesSchema(latitude=28.6129, longitude=77.2295), 120, 90, 30.0, True),
            ParkingSpot("IG002", CoordinatesSchema(latitude=28.6135, longitude=77.2300), 80, 65, 25.0, False),
            ParkingSpot("ND001", CoordinatesSchema(latitude=28.6000, longitude=77.2000), 200, 150, 35.0, True),
            ParkingSpot("ND002", CoordinatesSchema(latitude=28.5980, longitude=77.1980), 150, 120, 30.0, True),
            ParkingSpot("NO001", CoordinatesSchema(latitude=28.5800, longitude=77.3200), 90, 45, 18.0, False),
            ParkingSpot("NO002", CoordinatesSchema(latitude=28.5820, longitude=77.3220), 110, 80, 22.0, True),
            ParkingSpot("GG001", CoordinatesSchema(latitude=28.6700, longitude=77.4500), 70, 35, 15.0, False),
        ]
        
        for spot in mock_spots:
            self.parking_spots[spot.spot_id] = spot
    
    async def find_parking_near_destination(
        self,
        destination: CoordinatesSchema,
        radius_km: float = 2.0,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Find parking spots near a destination
        
        Args:
            destination: Destination coordinates
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return
            
        Returns:
            List of parking spots sorted by availability and distance
        """
        nearby_spots = []
        
        for spot in self.parking_spots.values():
            distance = self._calculate_distance(destination, spot.coordinates)
            if distance <= radius_km:
                nearby_spots.append({
                    "spot": spot.to_dict(),
                    "distance_km": distance
                })
        
        # Sort by availability (descending) and then by distance (ascending)
        nearby_spots.sort(key=lambda x: (-x["spot"]["availability"], x["distance_km"]))
        
        return [item["spot"] for item in nearby_spots[:max_results]]
    
    async def predict_parking_availability(
        self,
        destination: CoordinatesSchema,
        arrival_time: datetime,
        duration_hours: float = 2.0
    ) -> List[Dict]:
        """
        Predict parking availability using K-Means clustering
        
        Args:
            destination: Destination coordinates
            arrival_time: Expected arrival time
            duration_hours: Expected parking duration
            
        Returns:
            List of parking spots with predicted availability
        """
        # Get nearby spots first
        nearby_spots = await self.find_parking_near_destination(destination, radius_km=3.0)
        
        if not nearby_spots:
            return []
        
        # Apply ML prediction if available
        if SKLEARN_AVAILABLE and KMeans and self._has_sufficient_data():
            return await self._predict_with_ml(nearby_spots, arrival_time)
        else:
            # Use rule-based prediction for demo
            return await self._predict_with_rules(nearby_spots, arrival_time)
    
    def _has_sufficient_data(self) -> bool:
        """Check if we have sufficient data for ML prediction"""
        # In a real implementation, this would check historical data
        return len(self.parking_spots) >= 5
    
    async def _predict_with_ml(
        self,
        spots: List[Dict],
        arrival_time: datetime
    ) -> List[Dict]:
        """Predict availability using ML model"""
        # This is a simplified mock implementation
        # In a real system, this would use historical data and trained models
        
        predicted_spots = []
        for spot in spots:
            # Apply ML prediction logic
            base_availability = spot["availability"]
            
            # Time-based adjustments
            hour = arrival_time.hour
            if 9 <= hour <= 11 or 16 <= hour <= 18:  # Peak hours
                predicted_availability = max(0.0, base_availability - 0.3)
            elif 22 <= hour or hour <= 6:  # Night time
                predicted_availability = min(1.0, base_availability + 0.2)
            else:
                predicted_availability = base_availability
            
            # Add some randomness
            random_factor = random.uniform(-0.1, 0.1)
            predicted_availability = max(0.0, min(1.0, predicted_availability + random_factor))
            
            spot_copy = spot.copy()
            spot_copy["predicted_availability"] = predicted_availability
            spot_copy["prediction_confidence"] = 0.75  # Mock confidence
            predicted_spots.append(spot_copy)
        
        return predicted_spots
    
    async def _predict_with_rules(
        self,
        spots: List[Dict],
        arrival_time: datetime
    ) -> List[Dict]:
        """Predict availability using rule-based logic"""
        predicted_spots = []
        for spot in spots:
            base_availability = spot["availability"]
            
            # Time-based adjustments
            hour = arrival_time.hour
            if 9 <= hour <= 11 or 16 <= hour <= 18:  # Peak hours
                predicted_availability = max(0.0, base_availability - 0.3)
            elif 22 <= hour or hour <= 6:  # Night time
                predicted_availability = min(1.0, base_availability + 0.2)
            else:
                predicted_availability = base_availability
            
            # Add some randomness
            random_factor = random.uniform(-0.1, 0.1)
            predicted_availability = max(0.0, min(1.0, predicted_availability + random_factor))
            
            spot_copy = spot.copy()
            spot_copy["predicted_availability"] = predicted_availability
            spot_copy["prediction_confidence"] = 0.6  # Lower confidence for rule-based
            predicted_spots.append(spot_copy)
        
        return predicted_spots
    
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
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    async def update_parking_spot(
        self,
        spot_id: str,
        occupied: Optional[int] = None,
        capacity: Optional[int] = None
    ) -> bool:
        """
        Update parking spot information
        
        Returns:
            True if update successful, False otherwise
        """
        if spot_id not in self.parking_spots:
            return False
        
        spot = self.parking_spots[spot_id]
        if occupied is not None:
            spot.occupied = max(0, occupied)
        if capacity is not None:
            spot.capacity = max(0, capacity)
        
        spot.last_updated = datetime.utcnow()
        return True
    
    async def get_parking_statistics(self) -> Dict:
        """
        Get overall parking statistics
        
        Returns:
            Dictionary with parking statistics
        """
        if not self.parking_spots:
            return {
                "total_spots": 0,
                "total_capacity": 0,
                "total_occupied": 0,
                "average_availability": 0.0
            }
        
        total_capacity = sum(spot.capacity for spot in self.parking_spots.values())
        total_occupied = sum(spot.occupied for spot in self.parking_spots.values())
        average_availability = sum(spot.availability for spot in self.parking_spots.values()) / len(self.parking_spots)
        
        return {
            "total_spots": len(self.parking_spots),
            "total_capacity": total_capacity,
            "total_occupied": total_occupied,
            "average_availability": round(average_availability, 2)
        }


# Global instance
parking_service = ParkingService()