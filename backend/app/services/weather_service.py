"""
Weather Service using OpenWeatherMap API
Provides weather-aware routing and environmental data
"""
import httpx
import json
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.base import CoordinatesSchema
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data structure"""
    temperature_celsius: float
    humidity_percent: float
    wind_speed_kmh: float
    wind_direction: int
    precipitation_mm: float
    weather_condition: str
    weather_description: str
    visibility_km: float
    uv_index: float
    reading_time: datetime
    location: CoordinatesSchema


@dataclass
class WeatherForecast:
    """Weather forecast structure"""
    timestamp: datetime
    temperature_celsius: float
    weather_condition: str
    precipitation_probability: float
    wind_speed_kmh: float


class WeatherService:
    """Service for weather data integration using OpenWeatherMap"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENWEATHER_API_KEY', 'demo_key')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Weather impact factors for routing
        self.weather_impact_factors = {
            "rain": {"speed_reduction": 0.8, "visibility_impact": 0.7, "safety_factor": 0.6},
            "heavy_rain": {"speed_reduction": 0.6, "visibility_impact": 0.5, "safety_factor": 0.4},
            "thunderstorm": {"speed_reduction": 0.5, "visibility_impact": 0.4, "safety_factor": 0.3},
            "snow": {"speed_reduction": 0.4, "visibility_impact": 0.6, "safety_factor": 0.5},
            "fog": {"speed_reduction": 0.7, "visibility_impact": 0.3, "safety_factor": 0.5},
            "mist": {"speed_reduction": 0.9, "visibility_impact": 0.8, "safety_factor": 0.8},
            "clear": {"speed_reduction": 1.0, "visibility_impact": 1.0, "safety_factor": 1.0},
            "clouds": {"speed_reduction": 0.95, "visibility_impact": 0.9, "safety_factor": 0.9}
        }
        
        # Temperature thresholds for comfort routing
        self.temperature_comfort = {
            "too_cold": 5,     # Below 5°C
            "cold": 15,        # 5-15°C
            "comfortable": 30, # 15-30°C
            "hot": 40,         # 30-40°C
            "too_hot": 40      # Above 40°C
        }
    
    async def get_current_weather(self, coordinates: CoordinatesSchema) -> Optional[WeatherData]:
        """Get current weather data for a location"""
        
        # Check rate limit
        if not rate_limiter.is_allowed("openweather"):
            logger.warning("OpenWeatherMap API rate limit exceeded")
            return self._generate_mock_weather(coordinates)
        
        url = f"{self.base_url}/weather"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = await self.client.get(url, params=params)
            
            if response.status_code == 401:
                logger.warning("OpenWeatherMap API key invalid or missing. Using mock data.")
                return self._generate_mock_weather(coordinates)
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_weather_data(data, coordinates)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenWeatherMap API HTTP error: {e.response.status_code}")
            return self._generate_mock_weather(coordinates)
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._generate_mock_weather(coordinates)
    
    async def get_weather_forecast(
        self, 
        coordinates: CoordinatesSchema, 
        hours: int = 24
    ) -> List[WeatherForecast]:
        """Get weather forecast for next few hours"""
        
        if not rate_limiter.is_allowed("openweather"):
            logger.warning("OpenWeatherMap API rate limit exceeded")
            return self._generate_mock_forecast(coordinates, hours)
        
        url = f"{self.base_url}/forecast"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "appid": self.api_key,
            "units": "metric",
            "cnt": min(40, hours // 3)  # OpenWeatherMap provides 3-hour intervals
        }
        
        try:
            response = await self.client.get(url, params=params)
            
            if response.status_code == 401:
                logger.warning("OpenWeatherMap API key invalid. Using mock forecast.")
                return self._generate_mock_forecast(coordinates, hours)
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_forecast_data(data)
            
        except Exception as e:
            logger.error(f"Weather forecast error: {e}")
            return self._generate_mock_forecast(coordinates, hours)
    
    def _parse_weather_data(self, data: Dict[str, Any], coordinates: CoordinatesSchema) -> WeatherData:
        """Parse OpenWeatherMap current weather response"""
        try:
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            visibility = data.get("visibility", 10000)  # meters
            
            return WeatherData(
                temperature_celsius=main.get("temp", 25.0),
                humidity_percent=main.get("humidity", 60.0),
                wind_speed_kmh=wind.get("speed", 0) * 3.6,  # Convert m/s to km/h
                wind_direction=wind.get("deg", 0),
                precipitation_mm=data.get("rain", {}).get("1h", 0) + data.get("snow", {}).get("1h", 0),
                weather_condition=weather.get("main", "Clear").lower(),
                weather_description=weather.get("description", "clear sky"),
                visibility_km=visibility / 1000.0,
                uv_index=data.get("uvi", 5.0),  # Default moderate UV
                reading_time=datetime.utcnow(),
                location=coordinates
            )
        except Exception as e:
            logger.error(f"Weather data parsing failed: {e}")
            return self._generate_mock_weather(coordinates)
    
    def _parse_forecast_data(self, data: Dict[str, Any]) -> List[WeatherForecast]:
        """Parse OpenWeatherMap forecast response"""
        forecasts = []
        
        try:
            for item in data.get("list", []):
                forecast = WeatherForecast(
                    timestamp=datetime.fromtimestamp(item.get("dt", 0)),
                    temperature_celsius=item.get("main", {}).get("temp", 25.0),
                    weather_condition=item.get("weather", [{}])[0].get("main", "Clear").lower(),
                    precipitation_probability=item.get("pop", 0) * 100,  # Convert to percentage
                    wind_speed_kmh=item.get("wind", {}).get("speed", 0) * 3.6
                )
                forecasts.append(forecast)
                
        except Exception as e:
            logger.error(f"Forecast parsing failed: {e}")
        
        return forecasts
    
    def _generate_mock_weather(self, coordinates: CoordinatesSchema) -> WeatherData:
        """Generate realistic mock weather data for Indian cities"""
        import random
        
        # India-specific weather patterns
        base_temp = 30  # Average temperature in India
        if coordinates.latitude > 30:  # Northern India (cooler)
            base_temp = 25
        elif coordinates.latitude < 20:  # Southern India (warmer)
            base_temp = 32
        
        # Add seasonal variation (simplified)
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # Winter
            base_temp -= 8
        elif current_month in [3, 4, 5]:  # Summer
            base_temp += 5
        elif current_month in [6, 7, 8, 9]:  # Monsoon
            base_temp -= 3
        
        conditions = ["clear", "clouds", "rain", "mist"]
        # Higher probability of rain during monsoon
        if current_month in [6, 7, 8, 9]:
            condition = random.choices(conditions, weights=[20, 30, 40, 10])[0]
        else:
            condition = random.choices(conditions, weights=[40, 40, 10, 10])[0]
        
        return WeatherData(
            temperature_celsius=base_temp + random.uniform(-5, 5),
            humidity_percent=random.uniform(40, 80) if current_month in [6, 7, 8, 9] else random.uniform(20, 60),
            wind_speed_kmh=random.uniform(5, 25),
            wind_direction=random.randint(0, 360),
            precipitation_mm=random.uniform(0, 10) if condition == "rain" else 0,
            weather_condition=condition,
            weather_description=f"{condition} sky",
            visibility_km=random.uniform(8, 15) if condition in ["clear", "clouds"] else random.uniform(2, 8),
            uv_index=random.uniform(3, 9),
            reading_time=datetime.utcnow(),
            location=coordinates
        )
    
    def _generate_mock_forecast(self, coordinates: CoordinatesSchema, hours: int) -> List[WeatherForecast]:
        """Generate mock weather forecast"""
        forecasts = []
        current_weather = self._generate_mock_weather(coordinates)
        
        for i in range(0, hours, 3):  # 3-hour intervals
            timestamp = datetime.utcnow() + timedelta(hours=i)
            temp_variation = random.uniform(-3, 3)
            
            forecast = WeatherForecast(
                timestamp=timestamp,
                temperature_celsius=current_weather.temperature_celsius + temp_variation,
                weather_condition=current_weather.weather_condition,
                precipitation_probability=random.uniform(0, 60) if current_weather.weather_condition == "rain" else random.uniform(0, 20),
                wind_speed_kmh=current_weather.wind_speed_kmh + random.uniform(-5, 5)
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def calculate_weather_impact_on_route(
        self, 
        weather_data: WeatherData,
        base_travel_time: int
    ) -> Dict[str, Any]:
        """Calculate weather impact on route safety and timing"""
        
        condition = weather_data.weather_condition.lower()
        impact_factors = self.weather_impact_factors.get(condition, self.weather_impact_factors["clear"])
        
        # Calculate adjusted travel time
        speed_factor = impact_factors["speed_reduction"]
        adjusted_time = int(base_travel_time / speed_factor)
        
        # Calculate safety score
        safety_score = impact_factors["safety_factor"] * 100
        
        # Temperature comfort factor
        temp = weather_data.temperature_celsius
        comfort_level = "comfortable"
        if temp < self.temperature_comfort["too_cold"]:
            comfort_level = "too_cold"
        elif temp < self.temperature_comfort["cold"]:
            comfort_level = "cold"
        elif temp > self.temperature_comfort["too_hot"]:
            comfort_level = "too_hot"
        elif temp > self.temperature_comfort["hot"]:
            comfort_level = "hot"
        
        # Generate recommendations
        recommendations = self._generate_weather_recommendations(weather_data, impact_factors)
        
        return {
            "original_travel_time": base_travel_time,
            "weather_adjusted_time": adjusted_time,
            "time_increase_minutes": adjusted_time - base_travel_time,
            "safety_score": round(safety_score, 1),
            "visibility_impact": impact_factors["visibility_impact"],
            "comfort_level": comfort_level,
            "weather_condition": weather_data.weather_condition,
            "temperature": weather_data.temperature_celsius,
            "precipitation": weather_data.precipitation_mm,
            "wind_speed": weather_data.wind_speed_kmh,
            "recommendations": recommendations
        }
    
    def _generate_weather_recommendations(
        self, 
        weather: WeatherData, 
        impact_factors: Dict[str, float]
    ) -> List[str]:
        """Generate weather-specific travel recommendations"""
        recommendations = []
        
        condition = weather.weather_condition.lower()
        
        if condition in ["rain", "heavy_rain"]:
            recommendations.extend([
                "Reduce speed and increase following distance",
                "Use headlights and wipers",
                "Avoid flooded areas and underpasses",
                "Consider delaying travel if heavy rain"
            ])
        
        elif condition in ["thunderstorm"]:
            recommendations.extend([
                "Avoid travel if possible - severe weather",
                "Stay away from trees and open areas",
                "Use extreme caution on roads"
            ])
        
        elif condition in ["fog", "mist"]:
            recommendations.extend([
                "Use fog lights if available",
                "Reduce speed significantly",
                "Increase following distance",
                "Avoid overtaking"
            ])
        
        elif condition in ["snow"]:
            recommendations.extend([
                "Use winter tires or chains",
                "Drive very slowly",
                "Avoid sudden movements",
                "Keep emergency kit in vehicle"
            ])
        
        # Temperature-based recommendations
        if weather.temperature_celsius > 40:
            recommendations.extend([
                "Stay hydrated",
                "Use air conditioning",
                "Park in shade when possible",
                "Avoid midday travel"
            ])
        elif weather.temperature_celsius < 5:
            recommendations.extend([
                "Warm up vehicle before driving",
                "Check for ice on roads",
                "Keep warm clothing in vehicle"
            ])
        
        # Wind recommendations
        if weather.wind_speed_kmh > 40:
            recommendations.append("Strong winds - maintain firm grip on steering")
        
        # Visibility recommendations
        if weather.visibility_km < 5:
            recommendations.append("Poor visibility - use headlights and drive slowly")
        
        return recommendations
    
    async def get_route_weather_analysis(
        self, 
        route_coordinates: List[CoordinatesSchema],
        travel_time_minutes: int
    ) -> Dict[str, Any]:
        """Analyze weather conditions along a route"""
        
        # Sample points along route
        sample_coords = route_coordinates[::max(1, len(route_coordinates) // 5)]
        weather_data = []
        
        for coord in sample_coords:
            weather = await self.get_current_weather(coord)
            if weather:
                weather_data.append(weather)
        
        if not weather_data:
            return {"error": "No weather data available"}
        
        # Aggregate weather analysis
        avg_temp = sum(w.temperature_celsius for w in weather_data) / len(weather_data)
        max_precipitation = max(w.precipitation_mm for w in weather_data)
        min_visibility = min(w.visibility_km for w in weather_data)
        avg_wind = sum(w.wind_speed_kmh for w in weather_data) / len(weather_data)
        
        # Find most severe weather condition
        severe_conditions = ["thunderstorm", "heavy_rain", "snow", "fog"]
        worst_condition = "clear"
        for weather in weather_data:
            if weather.weather_condition in severe_conditions:
                if severe_conditions.index(weather.weather_condition) < severe_conditions.index(worst_condition):
                    worst_condition = weather.weather_condition
        
        # Calculate overall impact
        representative_weather = WeatherData(
            temperature_celsius=avg_temp,
            humidity_percent=sum(w.humidity_percent for w in weather_data) / len(weather_data),
            wind_speed_kmh=avg_wind,
            wind_direction=0,  # Not relevant for route analysis
            precipitation_mm=max_precipitation,
            weather_condition=worst_condition,
            weather_description=f"Route weather: {worst_condition}",
            visibility_km=min_visibility,
            uv_index=sum(w.uv_index for w in weather_data) / len(weather_data),
            reading_time=datetime.utcnow(),
            location=route_coordinates[0]
        )
        
        impact_analysis = self.calculate_weather_impact_on_route(
            representative_weather, travel_time_minutes
        )
        
        return {
            "route_weather_summary": {
                "average_temperature": round(avg_temp, 1),
                "max_precipitation": round(max_precipitation, 1),
                "minimum_visibility": round(min_visibility, 1),
                "average_wind_speed": round(avg_wind, 1),
                "worst_condition": worst_condition
            },
            "impact_analysis": impact_analysis,
            "weather_points": len(weather_data),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
weather_service = WeatherService()