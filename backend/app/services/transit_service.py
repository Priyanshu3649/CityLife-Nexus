"""
Public Transit Service for Indian Cities
Comprehensive transit integration for major Indian cities
"""
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from app.schemas.base import CoordinatesSchema

logger = logging.getLogger(__name__)


@dataclass
class TransitStop:
    """Transit stop/station information"""
    stop_id: str
    name: str
    coordinates: CoordinatesSchema
    stop_type: str  # metro, bus, train, brt
    city: str
    lines: List[str]


@dataclass
class TransitRoute:
    """Transit route information"""
    route_id: str
    name: str
    route_type: str  # metro, bus, train, brt
    city: str
    stops: List[TransitStop]
    color: str
    frequency_minutes: int


@dataclass
class TransitLeg:
    """Single leg of transit journey"""
    route_id: str
    route_name: str
    transport_type: str
    from_stop: TransitStop
    to_stop: TransitStop
    departure_time: datetime
    arrival_time: datetime
    travel_time_minutes: int
    cost_inr: float


@dataclass
class MultimodalRoute:
    """Complete multimodal route with walking and transit"""
    total_time_minutes: int
    total_cost_inr: float
    walking_distance_km: float
    transit_legs: List[TransitLeg]
    co2_savings_kg: float
    route_description: str


class IndianTransitService:
    """Comprehensive transit service for Indian cities"""
    
    def __init__(self):
        self.supported_cities = self._initialize_city_data()
        self.transit_networks = self._initialize_transit_networks()
        
    def _initialize_city_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize data for major Indian cities"""
        return {
            # Delhi NCR
            "delhi": {
                "name": "Delhi",
                "center": CoordinatesSchema(latitude=28.6139, longitude=77.2090),
                "metro_system": "Delhi Metro",
                "bus_system": "DTC",
                "population": 32000000,
                "has_metro": True,
                "has_brt": True,
                "metro_lines": 12,
                "metro_stations": 286
            },
            "gurgaon": {
                "name": "Gurgaon",
                "center": CoordinatesSchema(latitude=28.4595, longitude=77.0266),
                "metro_system": "Delhi Metro (Yellow Line Extension)",
                "bus_system": "Haryana Roadways",
                "population": 1200000,
                "has_metro": True,
                "has_brt": False
            },
            "noida": {
                "name": "Noida",
                "center": CoordinatesSchema(latitude=28.5355, longitude=77.3910),
                "metro_system": "Delhi Metro (Blue Line Extension)",
                "bus_system": "Noida Authority",
                "population": 650000,
                "has_metro": True,
                "has_brt": False
            },
            
            # Mumbai
            "mumbai": {
                "name": "Mumbai",
                "center": CoordinatesSchema(latitude=19.0760, longitude=72.8777),
                "metro_system": "Mumbai Metro",
                "bus_system": "BEST",
                "population": 21000000,
                "has_metro": True,
                "has_local_train": True,
                "metro_lines": 3,
                "local_train_lines": ["Western", "Central", "Harbour"]
            },
            
            # Bangalore
            "bangalore": {
                "name": "Bangalore",
                "center": CoordinatesSchema(latitude=12.9716, longitude=77.5946),
                "metro_system": "Namma Metro",
                "bus_system": "BMTC",
                "population": 13000000,
                "has_metro": True,
                "has_brt": False,
                "metro_lines": 2,
                "metro_stations": 64
            },
            
            # Chennai
            "chennai": {
                "name": "Chennai",
                "center": CoordinatesSchema(latitude=13.0827, longitude=80.2707),
                "metro_system": "Chennai Metro",
                "bus_system": "MTC",
                "population": 11000000,
                "has_metro": True,
                "has_local_train": True,
                "metro_lines": 2,
                "metro_stations": 32
            },
            
            # Kolkata
            "kolkata": {
                "name": "Kolkata",
                "center": CoordinatesSchema(latitude=22.5726, longitude=88.3639),
                "metro_system": "Kolkata Metro",
                "bus_system": "CSTC",
                "population": 15000000,
                "has_metro": True,
                "has_tram": True,
                "metro_lines": 6,
                "metro_stations": 52
            },
            
            # Hyderabad
            "hyderabad": {
                "name": "Hyderabad",
                "center": CoordinatesSchema(latitude=17.3850, longitude=78.4867),
                "metro_system": "Hyderabad Metro",
                "bus_system": "TSRTC",
                "population": 10000000,
                "has_metro": True,
                "metro_lines": 3,
                "metro_stations": 64
            },
            
            # Pune
            "pune": {
                "name": "Pune",
                "center": CoordinatesSchema(latitude=18.5204, longitude=73.8567),
                "metro_system": "Pune Metro",
                "bus_system": "PMPML",
                "population": 7400000,
                "has_metro": True,
                "has_brt": True,
                "metro_lines": 3
            },
            
            # Ahmedabad
            "ahmedabad": {
                "name": "Ahmedabad",
                "center": CoordinatesSchema(latitude=23.0225, longitude=72.5714),
                "metro_system": "Ahmedabad Metro",
                "bus_system": "AMTS, BRTS",
                "population": 8000000,
                "has_metro": True,
                "has_brt": True,
                "metro_lines": 2
            },
            
            # Jaipur
            "jaipur": {
                "name": "Jaipur",
                "center": CoordinatesSchema(latitude=26.9124, longitude=75.7873),
                "metro_system": "Jaipur Metro",
                "bus_system": "JCTSL",
                "population": 4000000,
                "has_metro": True,
                "metro_lines": 2
            },
            
            # Kochi
            "kochi": {
                "name": "Kochi",
                "center": CoordinatesSchema(latitude=9.9312, longitude=76.2673),
                "metro_system": "Kochi Metro",
                "bus_system": "KSRTC",
                "population": 2100000,
                "has_metro": True,
                "metro_lines": 1,
                "metro_stations": 22
            },
            
            # Lucknow
            "lucknow": {
                "name": "Lucknow",
                "center": CoordinatesSchema(latitude=26.8467, longitude=80.9462),
                "metro_system": "Lucknow Metro",
                "bus_system": "Lucknow Mahanagar Parivahan",
                "population": 3500000,
                "has_metro": True,
                "metro_lines": 1
            },
            
            # Nagpur
            "nagpur": {
                "name": "Nagpur",
                "center": CoordinatesSchema(latitude=21.1458, longitude=79.0882),
                "metro_system": "Nagpur Metro",
                "bus_system": "NMC",
                "population": 3100000,
                "has_metro": True,
                "metro_lines": 2
            },
            
            # Additional Tier-2 cities with good public transport
            "indore": {
                "name": "Indore",
                "center": CoordinatesSchema(latitude=22.7196, longitude=75.8577),
                "bus_system": "AICTSL, City Bus",
                "population": 3200000,
                "has_metro": False,
                "has_brt": True
            },
            
            "bhopal": {
                "name": "Bhopal",
                "center": CoordinatesSchema(latitude=23.2599, longitude=77.4126),
                "bus_system": "AIPL",
                "population": 2400000,
                "has_metro": False,
                "has_brt": True
            },
            
            "chandigarh": {
                "name": "Chandigarh",
                "center": CoordinatesSchema(latitude=30.7333, longitude=76.7794),
                "bus_system": "CTU",
                "population": 1200000,
                "has_metro": False,
                "has_brt": False
            },
            
            "surat": {
                "name": "Surat",
                "center": CoordinatesSchema(latitude=21.1702, longitude=72.8311),
                "bus_system": "SMTS",
                "population": 6500000,
                "has_metro": False,
                "has_brt": True
            },
            
            "coimbatore": {
                "name": "Coimbatore",
                "center": CoordinatesSchema(latitude=11.0168, longitude=76.9558),
                "bus_system": "TNSTC",
                "population": 2200000,
                "has_metro": False,
                "has_brt": False
            },
            
            "visakhapatnam": {
                "name": "Visakhapatnam",
                "center": CoordinatesSchema(latitude=17.6868, longitude=83.2185),
                "bus_system": "APSRTC",
                "population": 2200000,
                "has_metro": False,
                "has_brt": False
            }
        }
    
    def _initialize_transit_networks(self) -> Dict[str, List[TransitRoute]]:
        """Initialize comprehensive transit network data"""
        networks = {}
        
        # Delhi Metro Network (Simplified major stations)
        networks["delhi"] = [
            self._create_delhi_metro_routes(),
            self._create_delhi_bus_routes()
        ]
        
        # Mumbai Local Train + Metro
        networks["mumbai"] = [
            self._create_mumbai_local_train_routes(),
            self._create_mumbai_metro_routes()
        ]
        
        # Bangalore Metro
        networks["bangalore"] = [
            self._create_bangalore_metro_routes(),
            self._create_bangalore_bus_routes()
        ]
        
        # Chennai Metro + Local Train
        networks["chennai"] = [
            self._create_chennai_metro_routes(),
            self._create_chennai_bus_routes()
        ]
        
        # Other cities with simplified networks
        for city in ["kolkata", "hyderabad", "pune", "ahmedabad", "jaipur", "kochi", "lucknow", "nagpur"]:
            networks[city] = self._create_generic_metro_routes(city)
        
        return networks
    
    def _create_delhi_metro_routes(self) -> List[TransitRoute]:
        """Create Delhi Metro route data"""
        return [
            TransitRoute(
                route_id="delhi_red_line",
                name="Red Line (Rithala - Shaheed Sthal)",
                route_type="metro",
                city="delhi",
                stops=self._generate_metro_stops("delhi", "red_line", [
                    ("Rithala", 28.7218, 77.0919),
                    ("Rohini West", 28.7096, 77.1147),
                    ("Kashmere Gate", 28.6675, 77.2273),
                    ("Red Fort", 28.6562, 77.2410),
                    ("Chandni Chowk", 28.6580, 77.2300),
                    ("New Delhi", 28.6437, 77.2167),
                    ("Rajiv Chowk", 28.6328, 77.2197),
                    ("Khan Market", 28.6000, 77.2270),
                    ("Welcome", 28.6715, 77.2773)
                ]),
                color="#FF0000",
                frequency_minutes=4
            ),
            TransitRoute(
                route_id="delhi_blue_line",
                name="Blue Line (Dwarka - Noida/Vaishali)",
                route_type="metro",
                city="delhi",
                stops=self._generate_metro_stops("delhi", "blue_line", [
                    ("Dwarka", 28.5729, 77.0713),
                    ("Rajouri Garden", 28.6466, 77.1200),
                    ("Rajiv Chowk", 28.6328, 77.2197),
                    ("Mandi House", 28.6252, 77.2345),
                    ("Pragati Maidan", 28.6170, 77.2470),
                    ("Akshardham", 28.6127, 77.2773),
                    ("Noida Sector 62", 28.6074, 77.3714),
                    ("Electronic City", 28.6130, 77.3648)
                ]),
                color="#0000FF",
                frequency_minutes=3
            ),
            TransitRoute(
                route_id="delhi_yellow_line",
                name="Yellow Line (Samaypur Badli - HUDA City Centre)",
                route_type="metro",
                city="delhi",
                stops=self._generate_metro_stops("delhi", "yellow_line", [
                    ("Samaypur Badli", 28.7361, 77.2075),
                    ("Civil Lines", 28.6767, 77.2212),
                    ("Chandni Chowk", 28.6580, 77.2300),
                    ("Rajiv Chowk", 28.6328, 77.2197),
                    ("Central Secretariat", 28.6157, 77.2152),
                    ("Udyog Bhawan", 28.6090, 77.2034),
                    ("AIIMS", 28.5687, 77.2070),
                    ("Gurgaon", 28.4595, 77.0266),
                    ("HUDA City Centre", 28.4595, 77.0730)
                ]),
                color="#FFFF00",
                frequency_minutes=4
            )
        ]
    
    def _create_mumbai_local_train_routes(self) -> List[TransitRoute]:
        """Create Mumbai Local Train routes"""
        return [
            TransitRoute(
                route_id="mumbai_western_line",
                name="Western Line",
                route_type="train",
                city="mumbai",
                stops=self._generate_metro_stops("mumbai", "western", [
                    ("Churchgate", 18.9344, 72.8267),
                    ("Marine Lines", 18.9459, 72.8226),
                    ("Charni Road", 18.9536, 72.8190),
                    ("Grant Road", 18.9625, 72.8148),
                    ("Mumbai Central", 18.9690, 72.8205),
                    ("Dadar", 19.0178, 72.8478),
                    ("Bandra", 19.0544, 72.8406),
                    ("Andheri", 19.1136, 72.8697),
                    ("Borivali", 19.2307, 72.8567),
                    ("Virar", 19.4559, 72.8119)
                ]),
                color="#8B4513",
                frequency_minutes=3
            ),
            TransitRoute(
                route_id="mumbai_central_line",
                name="Central Line",
                route_type="train",
                city="mumbai",
                stops=self._generate_metro_stops("mumbai", "central", [
                    ("CST", 18.9398, 72.8355),
                    ("Masjid", 18.9476, 72.8317),
                    ("Sandhurst Road", 18.9543, 72.8319),
                    ("King's Circle", 19.0176, 72.8562),
                    ("Dadar", 19.0178, 72.8478),
                    ("Kurla", 19.0728, 72.8826),
                    ("Ghatkopar", 19.0864, 72.9081),
                    ("Thane", 19.1972, 72.9722),
                    ("Kalyan", 19.2437, 73.1355)
                ]),
                color="#800080",
                frequency_minutes=3
            )
        ]
    
    def _generate_metro_stops(self, city: str, line: str, station_data: List[Tuple[str, float, float]]) -> List[TransitStop]:
        """Generate transit stops from station data"""
        stops = []
        for i, (name, lat, lng) in enumerate(station_data):
            stop = TransitStop(
                stop_id=f"{city}_{line}_{i:03d}",
                name=name,
                coordinates=CoordinatesSchema(latitude=lat, longitude=lng),
                stop_type="metro" if "metro" in line else "train",
                city=city,
                lines=[line]
            )
            stops.append(stop)
        return stops
    
    def _create_bangalore_metro_routes(self) -> List[TransitRoute]:
        """Create Bangalore Metro routes"""
        return [
            TransitRoute(
                route_id="bangalore_purple_line",
                name="Purple Line (Mysuru Road - Whitefield)",
                route_type="metro",
                city="bangalore",
                stops=self._generate_metro_stops("bangalore", "purple", [
                    ("Mysuru Road", 12.9537, 77.5327),
                    ("Majestic", 12.9760, 77.5715),
                    ("Cubbon Park", 12.9750, 77.5900),
                    ("MG Road", 12.9750, 77.6042),
                    ("Trinity", 12.9718, 77.6220),
                    ("Halasuru", 12.9718, 77.6270),
                    ("Indiranagar", 12.9784, 77.6408),
                    ("Whitefield", 12.9698, 77.7500)
                ]),
                color="#800080",
                frequency_minutes=5
            ),
            TransitRoute(
                route_id="bangalore_green_line",
                name="Green Line (Silk Institute - Nagasandra)",
                route_type="metro",
                city="bangalore",
                stops=self._generate_metro_stops("bangalore", "green", [
                    ("Silk Institute", 12.9176, 77.6162),
                    ("Jayanagar", 12.9279, 77.5831),
                    ("South End Circle", 12.9344, 77.5910),
                    ("Majestic", 12.9760, 77.5715),
                    ("Peenya Industry", 13.0280, 77.5195),
                    ("Nagasandra", 13.0388, 77.5010)
                ]),
                color="#00FF00",
                frequency_minutes=6
            )
        ]
    
    def _create_generic_metro_routes(self, city: str) -> List[TransitRoute]:
        """Create generic metro routes for other cities"""
        city_info = self.supported_cities.get(city, {})
        if not city_info.get("has_metro", False):
            return []
        
        # Create simplified metro network based on city center
        center = city_info["center"]
        
        return [
            TransitRoute(
                route_id=f"{city}_line_1",
                name=f"{city_info['name']} Metro Line 1",
                route_type="metro",
                city=city,
                stops=self._generate_radial_stops(center, city, 8),
                color="#FF6B6B",
                frequency_minutes=5
            )
        ]
    
    def _generate_radial_stops(self, center: CoordinatesSchema, city: str, count: int) -> List[TransitStop]:
        """Generate stops in a radial pattern around city center"""
        import math
        stops = []
        
        # Add center station
        stops.append(TransitStop(
            stop_id=f"{city}_center",
            name=f"{city.title()} Central",
            coordinates=center,
            stop_type="metro",
            city=city,
            lines=["line_1"]
        ))
        
        # Add radial stations
        radius_km = 15  # 15km radius
        for i in range(count):
            angle = (i * 2 * math.pi) / count
            lat_offset = (radius_km / 111.0) * math.cos(angle)  # 1 degree lat ≈ 111 km
            lng_offset = (radius_km / (111.0 * math.cos(math.radians(center.latitude)))) * math.sin(angle)
            
            stop = TransitStop(
                stop_id=f"{city}_station_{i:02d}",
                name=f"Station {i+1}",
                coordinates=CoordinatesSchema(
                    latitude=center.latitude + lat_offset,
                    longitude=center.longitude + lng_offset
                ),
                stop_type="metro",
                city=city,
                lines=["line_1"]
            )
            stops.append(stop)
        
        return stops
    
    def _create_delhi_bus_routes(self) -> List[TransitRoute]:
        """Create sample Delhi bus routes"""
        return []  # Simplified for now
    
    def _create_mumbai_metro_routes(self) -> List[TransitRoute]:
        """Create Mumbai Metro routes"""
        return []  # Mumbai Metro is limited, focus on local trains
    
    def _create_bangalore_bus_routes(self) -> List[TransitRoute]:
        """Create Bangalore bus routes"""
        return []  # Simplified for now
    
    def _create_chennai_metro_routes(self) -> List[TransitRoute]:
        """Create Chennai Metro routes"""
        return []  # Simplified for now
    
    def _create_chennai_bus_routes(self) -> List[TransitRoute]:
        """Create Chennai bus routes"""
        return []  # Simplified for now
    
    def get_city_from_coordinates(self, coordinates: CoordinatesSchema) -> Optional[str]:
        """Determine which city based on coordinates"""
        min_distance = float('inf')
        closest_city = None
        
        for city_code, city_info in self.supported_cities.items():
            center = city_info["center"]
            distance = self._calculate_distance(coordinates, center)
            
            if distance < min_distance and distance < 50:  # Within 50km of city center
                min_distance = distance
                closest_city = city_code
        
        return closest_city
    
    def _calculate_distance(self, coord1: CoordinatesSchema, coord2: CoordinatesSchema) -> float:
        """Calculate distance between coordinates in kilometers"""
        import math
        
        lat1, lon1, lat2, lon2 = map(math.radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return c * 6371  # Earth's radius in km
    
    async def find_multimodal_routes(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        departure_time: Optional[datetime] = None
    ) -> List[MultimodalRoute]:
        """Find multimodal routes combining walking and transit"""
        
        if departure_time is None:
            departure_time = datetime.now()
        
        # Determine origin and destination cities
        origin_city = self.get_city_from_coordinates(origin)
        dest_city = self.get_city_from_coordinates(destination)
        
        if not origin_city or not dest_city:
            return []
        
        if origin_city != dest_city:
            # Inter-city travel - recommend train/flight (simplified)
            return self._create_intercity_route(origin, destination, origin_city, dest_city)
        
        # Intra-city travel
        city_routes = self.transit_networks.get(origin_city, [])
        if not city_routes:
            return []
        
        # Find nearest transit stops
        nearest_origin_stops = self._find_nearest_stops(origin, city_routes, max_walk_km=2.0)
        nearest_dest_stops = self._find_nearest_stops(destination, city_routes, max_walk_km=2.0)
        
        if not nearest_origin_stops or not nearest_dest_stops:
            return []
        
        # Generate possible routes
        possible_routes = []
        
        for origin_stop, origin_distance in nearest_origin_stops[:3]:  # Top 3 nearest
            for dest_stop, dest_distance in nearest_dest_stops[:3]:
                route = self._plan_transit_route(
                    origin, destination, origin_stop, dest_stop,
                    origin_distance, dest_distance, departure_time, origin_city
                )
                if route:
                    possible_routes.append(route)
        
        # Sort by total time and return top routes
        possible_routes.sort(key=lambda r: r.total_time_minutes)
        return possible_routes[:3]
    
    def _find_nearest_stops(
        self, 
        location: CoordinatesSchema, 
        city_routes: List[TransitRoute], 
        max_walk_km: float = 2.0
    ) -> List[Tuple[TransitStop, float]]:
        """Find nearest transit stops within walking distance"""
        
        nearby_stops = []
        
        for route in city_routes:
            for stop in route.stops:
                distance = self._calculate_distance(location, stop.coordinates)
                if distance <= max_walk_km:
                    nearby_stops.append((stop, distance))
        
        # Sort by distance and return closest
        nearby_stops.sort(key=lambda x: x[1])
        return nearby_stops[:10]  # Top 10 nearest stops
    
    def _plan_transit_route(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        origin_stop: TransitStop,
        dest_stop: TransitStop,
        origin_walk_distance: float,
        dest_walk_distance: float,
        departure_time: datetime,
        city: str
    ) -> Optional[MultimodalRoute]:
        """Plan a complete transit route"""
        
        # Calculate walking times (assuming 5 km/h walking speed)
        origin_walk_time = int((origin_walk_distance / 5.0) * 60)  # minutes
        dest_walk_time = int((dest_walk_distance / 5.0) * 60)
        
        # Simplified transit routing (in real implementation, would use pathfinding)
        transit_time = 30  # Default 30 minutes transit time
        transit_cost = self._calculate_transit_cost(city, origin_stop.stop_type)
        
        # Create transit leg
        transit_leg = TransitLeg(
            route_id=origin_stop.lines[0] if origin_stop.lines else "unknown",
            route_name=f"{origin_stop.name} to {dest_stop.name}",
            transport_type=origin_stop.stop_type,
            from_stop=origin_stop,
            to_stop=dest_stop,
            departure_time=departure_time + timedelta(minutes=origin_walk_time),
            arrival_time=departure_time + timedelta(minutes=origin_walk_time + transit_time),
            travel_time_minutes=transit_time,
            cost_inr=transit_cost
        )
        
        total_time = origin_walk_time + transit_time + dest_walk_time
        total_walking = origin_walk_distance + dest_walk_distance
        
        # Calculate CO2 savings compared to car
        car_distance = self._calculate_distance(origin, destination)
        co2_savings = car_distance * 0.21  # 210g CO2 per km for average car
        
        return MultimodalRoute(
            total_time_minutes=total_time,
            total_cost_inr=transit_cost,
            walking_distance_km=total_walking,
            transit_legs=[transit_leg],
            co2_savings_kg=co2_savings,
            route_description=f"Walk {origin_walk_time}min → {origin_stop.name} → {dest_stop.name} → Walk {dest_walk_time}min"
        )
    
    def _calculate_transit_cost(self, city: str, transport_type: str) -> float:
        """Calculate transit cost based on city and transport type"""
        # Indian metro/transit pricing (in INR)
        base_costs = {
            "delhi": {"metro": 20, "bus": 10, "train": 15},
            "mumbai": {"metro": 25, "bus": 8, "train": 5},
            "bangalore": {"metro": 15, "bus": 12, "train": 20},
            "chennai": {"metro": 20, "bus": 8, "train": 10},
            "kolkata": {"metro": 15, "bus": 7, "train": 8},
            "hyderabad": {"metro": 25, "bus": 10, "train": 15},
            "pune": {"metro": 20, "bus": 15, "train": 18},
            "ahmedabad": {"metro": 18, "bus": 8, "train": 12},
        }
        
        city_costs = base_costs.get(city, {"metro": 20, "bus": 10, "train": 15})
        return city_costs.get(transport_type, 15)
    
    def _create_intercity_route(
        self, 
        origin: CoordinatesSchema, 
        destination: CoordinatesSchema, 
        origin_city: str, 
        dest_city: str
    ) -> List[MultimodalRoute]:
        """Create intercity travel route recommendations"""
        
        # Calculate distance for intercity travel
        distance_km = self._calculate_distance(origin, destination)
        
        # Estimate travel times and costs for different modes
        routes = []
        
        # Train option (most common for intercity in India)
        if distance_km > 100:  # Long distance
            train_time = int(distance_km / 60 * 60)  # 60 km/h average for trains
            train_cost = distance_km * 0.5  # ₹0.5 per km approximate
            
            train_route = MultimodalRoute(
                total_time_minutes=train_time,
                total_cost_inr=train_cost,
                walking_distance_km=2.0,  # Airport/station access
                transit_legs=[],  # Simplified - would include detailed train schedule
                co2_savings_kg=distance_km * 0.15,  # 150g CO2 saving vs car per km
                route_description=f"Train from {origin_city.title()} to {dest_city.title()}"
            )
            routes.append(train_route)
        
        # Flight option for long distances
        if distance_km > 500:
            flight_time = 120 + int(distance_km / 800 * 60)  # 800 km/h + 2h airport time
            flight_cost = distance_km * 3.0  # ₹3 per km approximate
            
            flight_route = MultimodalRoute(
                total_time_minutes=flight_time,
                total_cost_inr=flight_cost,
                walking_distance_km=1.0,
                transit_legs=[],
                co2_savings_kg=0,  # Flights have higher emissions
                route_description=f"Flight from {origin_city.title()} to {dest_city.title()}"
            )
            routes.append(flight_route)
        
        # Bus option
        bus_time = int(distance_km / 40 * 60)  # 40 km/h average for buses
        bus_cost = distance_km * 0.8  # ₹0.8 per km
        
        bus_route = MultimodalRoute(
            total_time_minutes=bus_time,
            total_cost_inr=bus_cost,
            walking_distance_km=1.5,
            transit_legs=[],
            co2_savings_kg=distance_km * 0.12,  # 120g CO2 saving vs car per km
            route_description=f"Bus from {origin_city.title()} to {dest_city.title()}"
        )
        routes.append(bus_route)
        
        return routes
    
    async def get_real_time_updates(self, route_id: str) -> Dict[str, Any]:
        """Get real-time updates for transit routes"""
        # In real implementation, would connect to transit APIs
        return {
            "route_id": route_id,
            "status": "on_time",
            "delay_minutes": 0,
            "next_arrival": datetime.now() + timedelta(minutes=5),
            "crowding_level": "medium",
            "service_alerts": []
        }
    
    async def get_transit_accessibility_info(self, stop_id: str) -> Dict[str, Any]:
        """Get accessibility information for transit stops"""
        return {
            "stop_id": stop_id,
            "wheelchair_accessible": True,
            "elevator_available": True,
            "tactile_guidance": True,
            "audio_announcements": True,
            "braille_signage": False
        }
    
    def get_supported_cities(self) -> List[str]:
        """Get list of all supported cities"""
        return list(self.supported_cities.keys())
    
    def get_city_info(self, city_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific city"""
        return self.supported_cities.get(city_code)
    
    async def estimate_carbon_footprint(
        self, 
        route: MultimodalRoute, 
        passenger_count: int = 1
    ) -> Dict[str, float]:
        """Estimate carbon footprint for a multimodal route"""
        
        # CO2 emissions per km per passenger (in kg)
        emission_factors = {
            "walking": 0.0,
            "metro": 0.04,  # Very low for electric metro
            "bus": 0.08,   # Shared transport
            "train": 0.06, # Electric/diesel trains
            "car": 0.21,   # Private car baseline
            "flight": 0.25 # High emissions
        }
        
        total_emissions = 0.0
        walking_emissions = route.walking_distance_km * emission_factors["walking"]
        
        for leg in route.transit_legs:
            leg_distance = self._calculate_distance(
                leg.from_stop.coordinates, 
                leg.to_stop.coordinates
            )
            transport_factor = emission_factors.get(leg.transport_type, 0.1)
            total_emissions += leg_distance * transport_factor
        
        total_emissions += walking_emissions
        total_emissions *= passenger_count
        
        # Compare with car travel
        direct_distance = 0  # Would calculate from route
        car_emissions = direct_distance * emission_factors["car"] * passenger_count
        
        return {
            "total_emissions_kg": total_emissions,
            "car_emissions_kg": car_emissions,
            "savings_kg": max(0, car_emissions - total_emissions),
            "savings_percentage": max(0, (car_emissions - total_emissions) / car_emissions * 100) if car_emissions > 0 else 0
        }


# Global instance
transit_service = IndianTransitService()