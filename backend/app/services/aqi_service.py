"""
Air Quality Index (AQI) service using OpenAQ API
"""
import httpx
import redis
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.schemas.base import CoordinatesSchema
from app.schemas.air_quality import AQIReading, RouteAQIData, HealthImpactEstimate
from app.schemas.user import HealthProfile
from app.models.air_quality import AQIReading as AQIReadingModel
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class AQIService:
    """Service for air quality data integration"""
    
    def __init__(self):
        self.openaq_base_url = settings.OPENAQ_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        # AQI breakpoints for US EPA standard
        self.aqi_breakpoints = [
            (0, 50, "Good", "green"),
            (51, 100, "Moderate", "yellow"),
            (101, 150, "Unhealthy for Sensitive Groups", "orange"),
            (151, 200, "Unhealthy", "red"),
            (201, 300, "Very Unhealthy", "purple"),
            (301, 500, "Hazardous", "maroon")
        ]
    
    async def get_measurements_by_location(
        self,
        coordinates: CoordinatesSchema,
        radius_km: float = 10.0,
        parameter: str = "pm25"
    ) -> List[AQIReading]:
        """
        Get air quality measurements near a location from OpenAQ API v3
        """
        # Check rate limit
        if not rate_limiter.is_allowed("openaq"):
            logger.warning("OpenAQ API rate limit exceeded")
            return await self._get_cached_measurements(coordinates, radius_km)
        
        # For OpenAQ v3, we need to use different endpoints
        url = f"{self.openaq_base_url}measurements"
        
        # OpenAQ v3 parameters
        params = {
            "coordinates": f"{coordinates.latitude},{coordinates.longitude}",
            "radius": int(radius_km * 1000),  # Convert km to meters
            "parameter": parameter,
            "limit": 100,
            "order_by": "datetime",
            "sort": "desc"
        }
        
        # Add API key header if available
        headers = {}
        openaq_api_key = getattr(settings, 'OPENAQ_API_KEY', None)
        if openaq_api_key and openaq_api_key != "your-openaq-api-key-here":
            headers['X-API-Key'] = openaq_api_key
        
        try:
            logger.info(f"Requesting OpenAQ data for {coordinates.latitude},{coordinates.longitude}")
            response = await self.client.get(url, params=params, headers=headers)
            
            logger.info(f"OpenAQ API response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("OpenAQ API requires authentication. Using mock data.")
                return await self._get_cached_measurements(coordinates, radius_km)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"OpenAQ API response structure: {list(data.keys())}")
            
            readings = []
            results = data.get("results", [])
            logger.info(f"Found {len(results)} measurements from OpenAQ")
            
            for result in results:
                try:
                    # Convert OpenAQ measurement to AQI reading
                    aqi_reading = self._convert_measurement_to_aqi(result)
                    if aqi_reading:
                        readings.append(aqi_reading)
                        
                        # Cache the reading
                        await self._cache_aqi_reading(aqi_reading)
                        
                except Exception as e:
                    logger.warning(f"Failed to process measurement: {e}")
                    continue
            
            # If we got real data, return it
            if readings:
                logger.info(f"Successfully fetched {len(readings)} real AQI readings from OpenAQ")
                return readings
            else:
                logger.info("No real AQI data available, falling back to cached/mock data")
                return await self._get_cached_measurements(coordinates, radius_km)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAQ API HTTP error: {e.response.status_code}")
            return await self._get_cached_measurements(coordinates, radius_km)
        except Exception as e:
            logger.error(f"OpenAQ API error: {e}")
            return await self._get_cached_measurements(coordinates, radius_km)
    
    def _convert_measurement_to_aqi(self, measurement: Dict[str, Any]) -> Optional[AQIReading]:
        """
        Convert OpenAQ measurement to AQI reading
        """
        try:
            # Extract coordinates
            coords = measurement.get("coordinates", {})
            if not coords:
                return None
            
            coordinates = CoordinatesSchema(
                latitude=coords["latitude"],
                longitude=coords["longitude"]
            )
            
            # Extract measurement value and convert to AQI
            value = measurement.get("value")
            parameter = measurement.get("parameter", "").lower()
            
            if value is None:
                return None
            
            # Convert concentration to AQI based on parameter
            aqi_value = self._calculate_aqi(value, parameter)
            
            # Parse datetime
            date_str = measurement.get("date", {}).get("utc")
            if date_str:
                reading_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                reading_time = datetime.utcnow()
            
            # Create AQI reading
            return AQIReading(
                coordinates=coordinates,
                aqi_value=aqi_value,
                pm25=value if parameter == "pm25" else None,
                pm10=value if parameter == "pm10" else None,
                no2=value if parameter == "no2" else None,
                o3=value if parameter == "o3" else None,
                source="openaq",
                reading_time=reading_time
            )
            
        except Exception as e:
            logger.error(f"Error converting measurement: {e}")
            return None
    
    def _calculate_aqi(self, concentration: float, parameter: str) -> int:
        """
        Calculate AQI from pollutant concentration
        Simplified calculation - in production would use EPA formulas
        """
        # Simplified AQI calculation based on parameter
        if parameter == "pm25":
            # PM2.5 breakpoints (µg/m³ to AQI)
            if concentration <= 12.0:
                return int(concentration * 50 / 12.0)
            elif concentration <= 35.4:
                return int(50 + (concentration - 12.0) * 50 / 23.4)
            elif concentration <= 55.4:
                return int(100 + (concentration - 35.4) * 50 / 20.0)
            elif concentration <= 150.4:
                return int(150 + (concentration - 55.4) * 50 / 95.0)
            elif concentration <= 250.4:
                return int(200 + (concentration - 150.4) * 100 / 100.0)
            else:
                return min(500, int(300 + (concentration - 250.4) * 200 / 249.6))
        
        elif parameter == "pm10":
            # PM10 breakpoints
            if concentration <= 54:
                return int(concentration * 50 / 54)
            elif concentration <= 154:
                return int(50 + (concentration - 54) * 50 / 100)
            elif concentration <= 254:
                return int(100 + (concentration - 154) * 50 / 100)
            elif concentration <= 354:
                return int(150 + (concentration - 254) * 50 / 100)
            elif concentration <= 424:
                return int(200 + (concentration - 354) * 100 / 70)
            else:
                return min(500, int(300 + (concentration - 424) * 200 / 176))
        
        else:
            # Generic conversion for other parameters
            return min(500, max(0, int(concentration * 2)))
    
    async def get_route_aqi_data(
        self,
        route_coordinates: List[CoordinatesSchema],
        radius_km: float = 2.0
    ) -> RouteAQIData:
        """
        Get AQI data for all points along a route
        """
        all_readings = []
        aqi_values = []
        pollution_hotspots = []
        
        # Sample points along the route (every few coordinates to avoid too many API calls)
        sample_coords = route_coordinates[::max(1, len(route_coordinates) // 10)]
        
        for coord in sample_coords:
            readings = await self.get_measurements_by_location(coord, radius_km)
            
            if readings:
                # Use the most recent reading
                latest_reading = max(readings, key=lambda r: r.reading_time)
                all_readings.append(latest_reading)
                aqi_values.append(latest_reading.aqi_value)
                
                # Mark as hotspot if AQI > 150 (Unhealthy)
                if latest_reading.aqi_value > 150:
                    pollution_hotspots.append(coord)
        
        # Calculate average and max AQI
        if aqi_values:
            average_aqi = int(sum(aqi_values) / len(aqi_values))
            max_aqi = max(aqi_values)
        else:
            # Fallback to moderate AQI if no data
            average_aqi = 75
            max_aqi = 75
        
        return RouteAQIData(
            route_coordinates=route_coordinates,
            aqi_readings=all_readings,
            average_aqi=average_aqi,
            max_aqi=max_aqi,
            pollution_hotspots=pollution_hotspots
        )
    
    def calculate_health_impact(
        self,
        route_aqi_data: RouteAQIData,
        health_profile: Optional[HealthProfile] = None,
        travel_time_minutes: int = 30
    ) -> HealthImpactEstimate:
        """
        Calculate health impact estimate for a route
        """
        average_aqi = route_aqi_data.average_aqi
        max_aqi = route_aqi_data.max_aqi
        
        # Base health risk calculation
        base_risk = self._calculate_base_health_risk(average_aqi)
        
        # Adjust for user health profile
        risk_multiplier = 1.0
        precautions = []
        
        if health_profile:
            # Age group adjustments
            if health_profile.age_group == "child":
                risk_multiplier *= 1.3
                precautions.append("Children are more sensitive to air pollution")
            elif health_profile.age_group == "senior":
                risk_multiplier *= 1.2
                precautions.append("Seniors should limit outdoor exposure")
            
            # Respiratory conditions
            if health_profile.respiratory_conditions:
                risk_multiplier *= 1.5
                precautions.extend([
                    "Consider wearing a mask",
                    "Keep rescue inhaler accessible",
                    "Avoid strenuous activity"
                ])
            
            # Pollution sensitivity
            risk_multiplier *= health_profile.pollution_sensitivity
        
        # Time-based exposure calculation
        exposure_factor = min(2.0, travel_time_minutes / 30.0)  # Cap at 2x for long trips
        
        # Calculate final health risk score
        health_risk_score = min(100, base_risk * risk_multiplier * exposure_factor)
        
        # Estimated PM2.5 exposure (simplified calculation)
        estimated_pm25_exposure = average_aqi * 0.5 * (travel_time_minutes / 60.0)
        
        # Add general precautions based on AQI level
        if average_aqi > 150:
            precautions.extend([
                "Air quality is unhealthy",
                "Consider postponing travel if possible",
                "Close vehicle windows and use recirculated air"
            ])
        elif average_aqi > 100:
            precautions.append("Air quality is unhealthy for sensitive groups")
        
        # Calculate comparison to baseline (clean air = AQI 50)
        baseline_exposure = 50 * 0.5 * (travel_time_minutes / 60.0)
        comparison_to_baseline = ((estimated_pm25_exposure - baseline_exposure) / baseline_exposure) * 100
        
        return HealthImpactEstimate(
            estimated_exposure_pm25=round(estimated_pm25_exposure, 2),
            health_risk_score=round(health_risk_score, 1),
            recommended_precautions=list(set(precautions)),  # Remove duplicates
            comparison_to_baseline=round(comparison_to_baseline, 1)
        )
    
    def _calculate_base_health_risk(self, aqi: int) -> float:
        """
        Calculate base health risk from AQI value
        """
        if aqi <= 50:
            return 10.0  # Good air quality
        elif aqi <= 100:
            return 25.0  # Moderate
        elif aqi <= 150:
            return 45.0  # Unhealthy for sensitive groups
        elif aqi <= 200:
            return 70.0  # Unhealthy
        elif aqi <= 300:
            return 85.0  # Very unhealthy
        else:
            return 95.0  # Hazardous
    
    def get_aqi_category(self, aqi: int) -> Tuple[str, str]:
        """
        Get AQI category and color based on value
        """
        for min_aqi, max_aqi, category, color in self.aqi_breakpoints:
            if min_aqi <= aqi <= max_aqi:
                return category, color
        
        return "Hazardous", "maroon"
    
    async def _cache_aqi_reading(self, reading: AQIReading):
        """
        Cache AQI reading in Redis
        """
        try:
            cache_key = f"aqi:{reading.coordinates.latitude}:{reading.coordinates.longitude}"
            cache_data = {
                "aqi_value": reading.aqi_value,
                "pm25": reading.pm25,
                "pm10": reading.pm10,
                "no2": reading.no2,
                "o3": reading.o3,
                "source": reading.source,
                "reading_time": reading.reading_time.isoformat(),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Cache for 30 minutes
            self.redis_client.setex(
                cache_key,
                1800,  # 30 minutes
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache AQI reading: {e}")
    
    async def _get_cached_measurements(
        self,
        coordinates: CoordinatesSchema,
        radius_km: float
    ) -> List[AQIReading]:
        """
        Get cached AQI measurements near a location
        """
        try:
            # Simple cache lookup - in production would use geospatial queries
            cache_key = f"aqi:{coordinates.latitude}:{coordinates.longitude}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                # Handle different types of cached data
                if hasattr(cached_data, '__await__'):
                    # If it's an awaitable, we need to await it (this shouldn't happen with sync Redis client)
                    return [self._generate_mock_aqi_reading(coordinates)]
                
                # Decode bytes to string if needed
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode('utf-8')
                elif not isinstance(cached_data, str):
                    # If it's not a string or bytes, convert to string
                    cached_data = str(cached_data)
                
                data = json.loads(cached_data)
                reading_time = datetime.fromisoformat(data["reading_time"])
                
                reading = AQIReading(
                    coordinates=coordinates,
                    aqi_value=data["aqi_value"],
                    pm25=data.get("pm25"),
                    pm10=data.get("pm10"),
                    no2=data.get("no2"),
                    o3=data.get("o3"),
                    source=data["source"],
                    reading_time=reading_time
                )
                
                return [reading]
            
            # Return mock data if no cache available
            return [self._generate_mock_aqi_reading(coordinates)]
            
        except Exception as e:
            logger.error(f"Error getting cached measurements: {e}")
            return [self._generate_mock_aqi_reading(coordinates)]
    
    def _generate_mock_aqi_reading(self, coordinates: CoordinatesSchema) -> AQIReading:
        """
        Generate mock AQI reading for demo purposes
        """
        import random
        
        # Generate realistic AQI values based on location
        # Urban areas tend to have higher pollution
        base_aqi = random.randint(60, 120)
        
        return AQIReading(
            coordinates=coordinates,
            aqi_value=base_aqi,
            pm25=base_aqi * 0.6,  # Approximate PM2.5 from AQI
            pm10=base_aqi * 0.8,  # Approximate PM10 from AQI
            no2=random.uniform(20, 60),
            o3=random.uniform(30, 80),
            source="mock",
            reading_time=datetime.utcnow()
        )
    
    async def store_aqi_reading(self, db: Session, reading: AQIReading):
        """
        Store AQI reading in database
        """
        try:
            db_reading = AQIReadingModel(
                latitude=reading.coordinates.latitude,
                longitude=reading.coordinates.longitude,
                aqi_value=reading.aqi_value,
                pm25=reading.pm25,
                pm10=reading.pm10,
                no2=reading.no2,
                o3=reading.o3,
                source=reading.source,
                reading_time=reading.reading_time
            )
            
            db.add(db_reading)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store AQI reading: {e}")
            db.rollback()
    
    async def close(self):
        """Close HTTP client and Redis connection"""
        await self.client.aclose()
        self.redis_client.close()


# Global instance
aqi_service = AQIService()