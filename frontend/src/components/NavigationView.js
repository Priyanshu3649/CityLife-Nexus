import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import MapComponent from './MapComponent';

const NavigationView = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [routePreference, setRoutePreference] = useState('fastest');
  const [vehicleType, setVehicleType] = useState('car');
  const [showRoutes, setShowRoutes] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [trafficLights, setTrafficLights] = useState([]);
  const [mapCenter, setMapCenter] = useState({ lat: 28.6139, lng: 77.2090 });
  
  // Voice navigation state
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  
  // Keep track of announced signals to prevent repetition (moved outside useEffect)
  const announcedSignals = useRef(new Set());
  
  // New states for advanced features
  const [ecoScore, setEcoScore] = useState(null);
  const [emergencyAlert, setEmergencyAlert] = useState(null);
  
  // Google Maps autocomplete states
  const [fromSuggestions, setFromSuggestions] = useState([]);
  const [toSuggestions, setToSuggestions] = useState([]);
  const [showFromSuggestions, setShowFromSuggestions] = useState(false);
  const [showToSuggestions, setShowToSuggestions] = useState(false);
  const [selectedFromCoords, setSelectedFromCoords] = useState(null);
  const [selectedToCoords, setSelectedToCoords] = useState(null);
  
  const fromInputRef = useRef(null);
  const toInputRef = useRef(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [nextSignal, setNextSignal] = useState(null);
  const [userPosition, setUserPosition] = useState(null);
  const [currentInstruction, setCurrentInstruction] = useState({
    icon: '↑',
    text: 'Continue straight',
    detail: 'for 200 meters'
  });

  // Trip statistics tracking
  const [tripStats, setTripStats] = useState({
    signalsOnGreen: 0,
    signalsOnRed: 0,
    totalTime: 0,
    idlingTime: 0,
    pollutionExposure: 0,
    baselineIdling: 0
  });

  const calculateDistance = useCallback((coord1, coord2) => {
    const R = 6371;
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
    const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }, []);

  // Linear interpolation for AQI values between sensors
  const interpolateAQI = useCallback((point, sensor1, sensor2) => {
    if (!sensor1 || !sensor2) return 100; // Default AQI
    
    const distance1 = calculateDistance(point, sensor1.coordinates);
    const distance2 = calculateDistance(point, sensor2.coordinates);
    const totalDistance = distance1 + distance2;
    
    if (totalDistance === 0) return sensor1.aqi;
    
    // Linear interpolation formula
    const weight1 = distance2 / totalDistance;
    const weight2 = distance1 / totalDistance;
    
    return Math.round(sensor1.aqi * weight1 + sensor2.aqi * weight2);
  }, [calculateDistance]);

  // Get AQI for a specific location (moved to top to avoid temporal dead zone)
  const getAQIForLocation = useCallback(async (coordinates) => {
    try {
      // Fetch real AQI data from backend API
      const response = await fetch(`http://localhost:8001/api/v1/aqi/measurements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          latitude: coordinates.lat,
          longitude: coordinates.lng
        })
      });
      
      if (response.ok) {
        const aqiData = await response.json();
        if (aqiData && aqiData.length > 0) {
          // Return the AQI value from the most recent reading
          return aqiData[0].aqi_value;
        }
      }
      
      // Fallback to mock data if API fails
      console.warn('Failed to fetch real AQI data, using mock data');
      const mockAQIValues = [
        { coordinates: { lat: 28.6315, lng: 77.2167 }, aqi: 120 },
        { coordinates: { lat: 28.6280, lng: 77.2410 }, aqi: 180 },
        { coordinates: { lat: 28.6129, lng: 77.2295 }, aqi: 90 }
      ];
      
      // Find the two closest AQI sensors
      const sortedSensors = [...mockAQIValues].sort((a, b) => 
        calculateDistance(coordinates, a.coordinates) - calculateDistance(coordinates, b.coordinates)
      );
      
      if (sortedSensors.length >= 2) {
        return interpolateAQI(coordinates, sortedSensors[0], sortedSensors[1]);
      }
      
      return sortedSensors[0] ? sortedSensors[0].aqi : 100;
    } catch (error) {
      console.error('Error fetching AQI data:', error);
      // Fallback to mock data if API fails
      const mockAQIValues = [
        { coordinates: { lat: 28.6315, lng: 77.2167 }, aqi: 120 },
        { coordinates: { lat: 28.6280, lng: 77.2410 }, aqi: 180 },
        { coordinates: { lat: 28.6129, lng: 77.2295 }, aqi: 90 }
      ];
      
      // Find the two closest AQI sensors
      const sortedSensors = [...mockAQIValues].sort((a, b) => 
        calculateDistance(coordinates, a.coordinates) - calculateDistance(coordinates, b.coordinates)
      );
      
      if (sortedSensors.length >= 2) {
        return interpolateAQI(coordinates, sortedSensors[0], sortedSensors[1]);
      }
      
      return sortedSensors[0] ? sortedSensors[0].aqi : 100;
    }
  }, [calculateDistance, interpolateAQI]);
  // Initialize speech synthesis
  useEffect(() => {
    const initSpeech = () => {
      if ('speechSynthesis' in window) {
        // Load voices
        const loadVoices = () => {
          const availableVoices = speechSynthesis.getVoices();
          setVoices(availableVoices);
          
          // Select a default English voice
          const defaultVoice = availableVoices.find(voice => 
            voice.lang.includes('en') && voice.default
          ) || availableVoices.find(voice => 
            voice.lang.includes('en')
          );
          
          setSelectedVoice(defaultVoice || availableVoices[0]);
        };
        
        // Load voices immediately
        loadVoices();
        
        // Load voices again when they become available
        speechSynthesis.onvoiceschanged = loadVoices;
        
        return () => {
          speechSynthesis.onvoiceschanged = null;
        };
      }
    };
    
    initSpeech();
  }, []);

  // Cleanup speech synthesis when component unmounts
  useEffect(() => {
    return () => {
      // Cancel any ongoing speech when component unmounts
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
      }
    };
  }, []);

  // Speak function
  const speak = useCallback((text) => {
    if (!isVoiceEnabled || !('speechSynthesis' in window)) return;
    
    // Cancel any ongoing speech to prevent queue buildup
    speechSynthesis.cancel();
    
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = selectedVoice;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      speechSynthesis.speak(utterance);
    } catch (error) {
      console.error('Speech synthesis error:', error);
    }
  }, [isVoiceEnabled, selectedVoice]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      const isSuggestionClick = event.target.closest('[data-suggestion-item]');
      
      // Check if click is outside both input fields and suggestions
      if (fromInputRef.current && !fromInputRef.current.contains(event.target) && !isSuggestionClick) {
        setShowFromSuggestions(false);
      }
      if (toInputRef.current && !toInputRef.current.contains(event.target) && !isSuggestionClick) {
        setShowToSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Update traffic light timers
  useEffect(() => {
    if (trafficLights.length === 0) return;
    
    const timer = setInterval(() => {
      setTrafficLights(prevLights => 
        prevLights.map(light => {
          const newTimeRemaining = Math.max(0, light.current_state.time_remaining - 1);
          let newColor = light.current_state.color;
          let newTimeToNextChange = newTimeRemaining;
          
          if (light.current_state.time_remaining === 1) {
            if (light.current_state.color === 'red') {
              newColor = 'green';
              newTimeToNextChange = 30;
            } else if (light.current_state.color === 'green') {
              newColor = 'yellow';
              newTimeToNextChange = 3;
            } else if (light.current_state.color === 'yellow') {
              newColor = 'red';
              newTimeToNextChange = 45;
            }
          }
          
          return {
            ...light,
            current_state: {
              ...light.current_state,
              color: newColor,
              time_remaining: newTimeToNextChange
            }
          };
        })
      );
    }, 1000);
    
    return () => clearInterval(timer);
  }, [trafficLights]);

  // Emergency auto-reroute function
  const triggerReroute = useCallback(async () => {
    if (!selectedFromCoords || !selectedToCoords) return;
    
    try {
      const response = await fetch('http://localhost:8001/api/v1/maps/reroute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_coords: {
            latitude: userPosition ? userPosition.lat : selectedFromCoords.lat,
            longitude: userPosition ? userPosition.lng : selectedFromCoords.lng
          },
          end_coords: {
            latitude: selectedToCoords.lat,
            longitude: selectedToCoords.lng
          },
          preferences: {
            prioritize_time: routePreference === 'fastest' ? 0.8 : 0.2,
            prioritize_air_quality: routePreference === 'cleanest' ? 0.8 : 0.2,
            prioritize_safety: routePreference === 'safest' ? 0.8 : 0.2,
            max_detour_minutes: 15
          },
          vehicle_type: vehicleType,
          emergency_conditions: emergencyAlert
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRoutes([data.route]); // Assuming reroute returns a single optimal route
        setSelectedRouteId(data.route.id);
        await fetchTrafficLightData(
          userPosition || selectedFromCoords, 
          selectedToCoords
        );
        speak(`Emergency rerouting activated. New route calculated.`);
      }
    } catch (error) {
      console.error('Error during rerouting:', error);
      speak(`Error during emergency rerouting. Please check manually.`);
    }
  }, [selectedFromCoords, selectedToCoords, userPosition, routePreference, vehicleType, emergencyAlert, speak]);

  // Emergency auto-reroute monitoring
  useEffect(() => {
    if (!isNavigating) return;
    
    const monitorConditions = async () => {
      try {
        // Check for emergency conditions (accidents, congestion, pollution spikes)
        const response = await fetch('http://localhost:8001/api/v1/emergency/alerts', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (response.ok) {
          const alerts = await response.json();
          if (alerts && alerts.length > 0) {
            const criticalAlert = alerts.find(alert => alert.severity === 'critical');
            if (criticalAlert) {
              setEmergencyAlert(criticalAlert);
              triggerReroute();
            }
          }
        } else {
          console.error('Failed to fetch emergency alerts');
        }
      } catch (error) {
        console.error('Error checking emergency conditions:', error);
      }
    };
    
    const interval = setInterval(monitorConditions, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [isNavigating, triggerReroute]);

  const getDirectionIcon = (maneuver) => {
    switch (maneuver) {
      case 'turn-left':
        return '⬅️';
      case 'turn-right':
        return '➡️';
      case 'turn-slight-left':
        return '↖️';
      case 'turn-slight-right':
        return '↗️';
      case 'turn-sharp-left':
        return '↩️';
      case 'turn-sharp-right':
        return '↪️';
      case 'uturn-left':
      case 'uturn-right':
        return '↩️';
      case 'ramp-left':
      case 'ramp-right':
        return '↗️';
      case 'merge':
        return '↘️';
      case 'fork-left':
      case 'fork-right':
        return '⤵️';
      case 'roundabout-left':
      case 'roundabout-right':
        return '🔄';
      case 'keep-left':
      case 'keep-right':
        return '🛣️';
      default:
        return '↑'; // straight
    }
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  // Fetch traffic light data for the route
  const fetchTrafficLightData = async (fromCoords, toCoords) => {
    console.log('Fetching traffic light data', { fromCoords, toCoords });
    try {
      const routeCoordinates = [
        { latitude: fromCoords.lat, longitude: fromCoords.lng },
        { latitude: toCoords.lat, longitude: toCoords.lng }
      ];
      
      const response = await fetch('http://localhost:8001/api/v1/signals/along-route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(routeCoordinates)
      });
              
      console.log('Traffic light API response status:', response.status);
      
      if (response.ok) {
        const signals = await response.json();
        console.log('Traffic light data received:', signals);
        
        // If no signals found, that's OK - it just means no traffic lights along this route
        if (signals.length === 0) {
          console.log('No traffic lights found along the route - this is normal for some routes');
        }
        
        const trafficLightsData = signals.map(signal => ({
          light_id: signal.signal_id,
          coordinates: { 
            lat: signal.coordinates.latitude, 
            lng: signal.coordinates.longitude 
          },
          current_state: {
            color: signal.current_state,
            time_remaining: signal.time_to_next_change
          },
          intersection_name: signal.intersection_name || signal.signal_id
        }));
        console.log('Setting traffic lights data:', trafficLightsData);
        setTrafficLights(trafficLightsData);
      } else {
        // Only use mock data if API fails
        console.error('Failed to fetch traffic light data, using mock data');
        const mockTrafficLights = [
          {
            light_id: 'cp_outer_circle',
            coordinates: { lat: 28.6315, lng: 77.2167 },
            current_state: { color: 'green', time_remaining: 15 },
            intersection_name: 'Connaught Place Outer Circle'
          },
          {
            light_id: 'ito_intersection',
            coordinates: { lat: 28.6280, lng: 77.2410 },
            current_state: { color: 'red', time_remaining: 45 },
            intersection_name: 'ITO Intersection'
          },
          {
            light_id: 'india_gate_circle',
            coordinates: { lat: 28.6129, lng: 77.2295 },
            current_state: { color: 'yellow', time_remaining: 3 },
            intersection_name: 'India Gate Circle'
          }
        ];
        setTrafficLights(mockTrafficLights);
      }
    } catch (error) {
      console.error('Error fetching traffic light data:', error);
      // Only use mock data if API fails
      const mockTrafficLights = [
        {
          light_id: 'cp_outer_circle',
          coordinates: { lat: 28.6315, lng: 77.2167 },
          current_state: { color: 'green', time_remaining: 15 },
          intersection_name: 'Connaught Place Outer Circle'
        },
        {
          light_id: 'ito_intersection',
          coordinates: { lat: 28.6280, lng: 77.2410 },
          current_state: { color: 'red', time_remaining: 45 },
          intersection_name: 'ITO Intersection'
        },
        {
          light_id: 'india_gate_circle',
          coordinates: { lat: 28.6129, lng: 77.2295 },
          current_state: { color: 'yellow', time_remaining: 3 },
          intersection_name: 'India Gate Circle'
        }
      ];
      setTrafficLights(mockTrafficLights);
    }
  };

  // Google Places Autocomplete
  const searchPlaces = async (query, setSuggestions) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8001/api/v1/maps/autocomplete?query=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.predictions || []);
      } else {
        // Only use mock suggestions if API fails
        console.error('Failed to fetch place suggestions, using mock data');
        setSuggestions([
          { description: `${query} - Delhi, India`, place_id: 'mock1' },
          { description: `${query} - Mumbai, India`, place_id: 'mock2' },
          { description: `${query} - Bangalore, India`, place_id: 'mock3' }
        ]);
      }
    } catch (error) {
      console.error('Error fetching place suggestions:', error);
      // Only use mock suggestions when API fails
      setSuggestions([
        { description: `${query}, Delhi, India`, place_id: 'mock1' },
        { description: `${query}, Mumbai, India`, place_id: 'mock2' },
        { description: `${query}, Bangalore, India`, place_id: 'mock3' }
      ]);
    }
  };

  const handleFromLocationChange = (e) => {
    const value = e.target.value;
    setFromLocation(value);
    setShowFromSuggestions(true);
    searchPlaces(value, setFromSuggestions);
  };

  const handleToLocationChange = (e) => {
    const value = e.target.value;
    setToLocation(value);
    setShowToSuggestions(true);
    searchPlaces(value, setToSuggestions);
  };

  const selectFromLocation = async (suggestion) => {
    setFromLocation(suggestion.description);
    setShowFromSuggestions(false);
    setFromSuggestions([]);
    
    try {
      const response = await fetch(`http://localhost:8001/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          setSelectedFromCoords(convertedCoords);
        }
      } else {
        // Only use mock coordinates if API fails
        console.error('Failed to fetch geocode data, using mock coordinates');
      }
    } catch (error) {
      console.error('Error fetching geocode data:', error);
      // Don't set mock coordinates here - let the user know there was an error
    }
  };

  const selectToLocation = async (suggestion) => {
    setToLocation(suggestion.description);
    setShowToSuggestions(false);
    setToSuggestions([]);
    
    try {
      const response = await fetch(`http://localhost:8001/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          setSelectedToCoords(convertedCoords);
        }
      } else {
        // Only use mock coordinates if API fails
        console.error('Failed to fetch geocode data, using mock coordinates');
      }
    } catch (error) {
      console.error('Error fetching geocode data:', error);
      // Don't set mock coordinates here - let the user know there was an error
    }
  };

  const swapLocations = () => {
    const tempLocation = fromLocation;
    const tempCoords = selectedFromCoords;
    
    setFromLocation(toLocation);
    setSelectedFromCoords(selectedToCoords);
    
    setToLocation(tempLocation);
    setSelectedToCoords(tempCoords);
    
    setFromSuggestions([]);
    setToSuggestions([]);
    setShowFromSuggestions(false);
    setShowToSuggestions(false);
  };

  const handleRouteSearch = async () => {
    if (!fromLocation || !toLocation) {
      alert('Please enter both starting location and destination');
      return;
    }

    if (!selectedFromCoords || !selectedToCoords) {
      alert('Please select locations from the dropdown suggestions');
      return;
    }

    setIsLoading(true);
    setShowRoutes(false);
    setSelectedRouteId(null);

    try {
      const response = await fetch('http://localhost:8001/api/v1/maps/routes-with-aqi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_coords: {
            latitude: selectedFromCoords.lat,
            longitude: selectedFromCoords.lng
          },
          end_coords: {
            latitude: selectedToCoords.lat,
            longitude: selectedToCoords.lng
          },
          preferences: {
            prioritize_time: routePreference === 'fastest' ? 0.8 : 0.2,
            prioritize_air_quality: routePreference === 'cleanest' ? 0.8 : 0.2,
            prioritize_safety: routePreference === 'safest' ? 0.8 : 0.2,
            max_detour_minutes: 10
          },
          vehicle_type: vehicleType
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRoutes(data.routes || []);
        setShowRoutes(true);
        await fetchTrafficLightData(selectedFromCoords, selectedToCoords);
      } else {
        throw new Error('Failed to fetch routes');
      }
    } catch (error) {
      console.error('Error fetching routes:', error);
      // Only use mock data if API fails
      let mockRoute;
      switch (routePreference) {
        case 'fastest':
          mockRoute = {
            id: '1',
            name: 'Fastest Route',
            time: 18,
            aqi: 160,
            distance: 12.5,
            type: 'fastest',
            description: 'Via main roads with heavy traffic'
          };
          break;
        case 'cleanest':
          mockRoute = {
            id: '2',
            name: 'Clean Air Route',
            time: 25,
            aqi: 85,
            distance: 14.2,
            type: 'cleanest',
            description: 'Via parks and residential areas'
          };
          break;
        case 'safest':
          mockRoute = {
            id: '3',
            name: 'Safest Route',
            time: 22,
            aqi: 140,
            distance: 13.8,
            type: 'safest',
            description: 'Via well-lit, secure areas with low accident rates'
          };
          break;
        default:
          mockRoute = {
            id: '1',
            name: 'Fastest Route',
            time: 18,
            aqi: 160,
            distance: 12.5,
            type: 'fastest',
            description: 'Via main roads with heavy traffic'
          };
      }
      setRoutes([mockRoute]);
      setShowRoutes(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate Eco-Score after trip completion
  const calculateEcoScore = useCallback((tripStats) => {
    // Pollution dose calculation: ∑ (AQI × time spent per segment)
    const pollutionDose = tripStats.pollutionExposure;
    
    // Fuel saved calculation: baseline idling × avoided stops
    const fuelSaved = tripStats.baselineIdling * tripStats.signalsOnGreen * 0.03; // 30ml per green signal
    
    // Percentage reduction in pollution exposure
    const pollutionReduction = tripStats.signalsOnRed > 0 ? 
      Math.round((tripStats.signalsOnGreen / (tripStats.signalsOnGreen + tripStats.signalsOnRed)) * 100) : 100;
    
    return {
      signalsOnGreen: tripStats.signalsOnGreen,
      signalsOnRed: tripStats.signalsOnRed,
      pollutionDose,
      pollutionReduction,
      fuelSaved: Math.round(fuelSaved * 1000), // Convert to ml
      efficiencyScore: Math.round((tripStats.signalsOnGreen / Math.max(1, tripStats.signalsOnGreen + tripStats.signalsOnRed)) * 100)
    };
  }, []);

  const selectRoute = (route) => {
    setSelectedRouteId(route.id);
    const selectionMessage = `🗺️ Route selected: ${route.name}. Estimated time: ${route.time} minutes. Air quality index: ${route.aqi}. Click "START NAV" to begin turn-by-turn navigation within the app.`;
    alert(selectionMessage);
    speak(selectionMessage);
  };

  const startNavigation = async (route) => {
    if (selectedFromCoords && selectedToCoords) {
      setSelectedRouteId(route.id);
      setIsNavigating(true);
      setEcoScore(null); // Reset eco score
      setEmergencyAlert(null); // Reset emergency alerts
      setTripStats({
        signalsOnGreen: 0,
        signalsOnRed: 0,
        totalTime: 0,
        idlingTime: 0,
        pollutionExposure: 0,
        baselineIdling: 0
      });
      
      // Clear announced signals when starting new navigation
      announcedSignals.current.clear();
      
      await fetchTrafficLightData(selectedFromCoords, selectedToCoords);
      
      // Fetch real turn-by-turn directions from Google Maps API
      try {
        if (typeof window.google !== 'undefined' && window.google.maps && window.google.maps.DirectionsService) {
          const directionsService = new window.google.maps.DirectionsService();
          
          directionsService.route(
            {
              origin: { lat: selectedFromCoords.lat, lng: selectedFromCoords.lng },
              destination: { lat: selectedToCoords.lat, lng: selectedToCoords.lng },
              travelMode: window.google.maps.TravelMode.DRIVING
            },
            (response, status) => {
              if (status === 'OK' && response.routes && response.routes.length > 0) {
                // Store the directions for use in navigation
                const directions = response.routes[0];
                // Set the first instruction as the current instruction
                if (directions.legs && directions.legs.length > 0 && directions.legs[0].steps && directions.legs[0].steps.length > 0) {
                  const firstStep = directions.legs[0].steps[0];
                  const newInstruction = {
                    icon: getDirectionIcon(firstStep.maneuver),
                    text: firstStep.instructions.replace(/<[^>]*>/g, ''), // Remove HTML tags
                    detail: `for ${firstStep.distance.text}`
                  };
                  setCurrentInstruction(newInstruction);
                  speak(`${newInstruction.text} ${newInstruction.detail}`);
                }
              } else {
                console.error('Directions request failed due to ' + status);
                // Fallback to default instruction
                const fallbackInstruction = {
                  icon: '↑',
                  text: 'Continue straight',
                  detail: 'for 200 meters'
                };
                setCurrentInstruction(fallbackInstruction);
                speak('Continue straight for 200 meters');
              }
            }
          );
        } else {
          // Fallback to default instruction if Google Maps is not available
          const fallbackInstruction = {
            icon: '↑',
            text: 'Continue straight',
            detail: 'for 200 meters'
          };
          setCurrentInstruction(fallbackInstruction);
          speak('Continue straight for 200 meters');
        }
      } catch (error) {
        console.error('Error fetching directions:', error);
        // Fallback to default instruction
        const fallbackInstruction = {
          icon: '↑',
          text: 'Continue straight',
          detail: 'for 200 meters'
        };
        setCurrentInstruction(fallbackInstruction);
        speak('Continue straight for 200 meters');
      }
      
      setTimeout(() => {
        const mapElement = document.getElementById('navigation-map');
        if (mapElement) {
          mapElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
      
      const startMessage = `🧭 Navigation started! Following route: ${route.name}. Estimated time: ${route.time} minutes. Follow the directions on the map and listen for traffic advisories.`;
      speak(startMessage);
    } else {
      const errorMessage = 'Please select valid start and end locations first.';
      speak(errorMessage);
    }
  };

  // Monitor traffic light advisories during navigation
  useEffect(() => {
    console.log('Traffic light advisory system triggered', { isNavigating, trafficLightsLength: trafficLights.length, selectedFromCoords });
    if (!isNavigating || !selectedFromCoords) {
      console.log('Traffic light advisory system skipped', { isNavigating, trafficLightsLength: trafficLights.length, selectedFromCoords: !!selectedFromCoords });
      return;
    }
    
    // It's OK if there are no traffic lights - just continue without advisories
    if (trafficLights.length === 0) {
      console.log('No traffic lights to monitor - advisories will not be provided for this route');
      return;
    }
    
    const advisoryTimer = setInterval(() => {
      const lightsInRange = trafficLights
        .map(light => {
          const referencePosition = userPosition || selectedFromCoords;
          const distance = calculateDistance(referencePosition, light.coordinates);
          const distanceMeters = distance * 1000;
          return { ...light, distance, distanceMeters };
        })
        .filter(light => light.distanceMeters >= 200 && light.distanceMeters <= 1000)
        .sort((a, b) => a.distanceMeters - b.distanceMeters);
      
      if (lightsInRange.length > 0) {
        setNextSignal(lightsInRange[0]);
      }
      
      lightsInRange.slice(0, 3).forEach((light, index) => {
        const distanceMeters = light.distanceMeters;
        const timeRemaining = light.current_state.time_remaining;
        const color = light.current_state.color;
        const lightId = light.intersection_name || light.light_id || `TF_${index + 1}`;
        
        // Update trip statistics
        // Update trip statistics with AQI data
        getAQIForLocation(light.coordinates).then(aqiValue => {
          setTripStats(prev => {
            const newStats = { ...prev };
            if (color === 'red') {
              newStats.signalsOnRed += 1;
              newStats.idlingTime += timeRemaining;
            } else if (color === 'green') {
              newStats.signalsOnGreen += 1;
            }
            newStats.pollutionExposure += (aqiValue * (timeRemaining / 60)); // AQI * hours
            return newStats;
          });
        }).catch(error => {
          console.error('Error getting AQI for location:', error);
          // Use default AQI value of 100 if there's an error
          setTripStats(prev => {
            const newStats = { ...prev };
            if (color === 'red') {
              newStats.signalsOnRed += 1;
              newStats.idlingTime += timeRemaining;
            } else if (color === 'green') {
              newStats.signalsOnGreen += 1;
            }
            newStats.pollutionExposure += (100 * (timeRemaining / 60)); // Default AQI * hours
            return newStats;
          });
        });
        
        const recommendedSpeed = calculateRecommendedSpeed(distanceMeters, timeRemaining, color);
        
        // Create a unique identifier for this signal state
        const signalStateId = `${lightId}-${color}-${timeRemaining}`;
        
        let advisoryText = '';
        if (color === 'red') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            if (recommendedSpeed) {
              advisoryText = `Red signal ${Math.round(distanceMeters)}m ahead turning green in ${timeRemaining}s, slow down to ${recommendedSpeed} km/h to avoid waiting and save fuel.`;
            } else {
              advisoryText = `Red signal ${Math.round(distanceMeters)}m ahead turning green in ${timeRemaining}s, slow down to avoid waiting and save fuel.`;
            }
          } else if (timeRemaining === 0) {
            advisoryText = `Red signal ${Math.round(distanceMeters)}m ahead turning green now. Proceed carefully.`;
          }
        } else if (color === 'green') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            if (recommendedSpeed) {
              advisoryText = `Green signal ${Math.round(distanceMeters)}m ahead turning yellow in ${timeRemaining}s. Maintain speed at ${recommendedSpeed} km/h to save fuel.`;
            } else {
              advisoryText = `Green signal ${Math.round(distanceMeters)}m ahead turning yellow in ${timeRemaining}s. Maintain speed to save fuel.`;
            }
          } else if (timeRemaining === 0) {
            advisoryText = `Green signal ${Math.round(distanceMeters)}m ahead turning yellow now. Prepare to stop.`;
          }
        } else if (color === 'yellow') {
          if (timeRemaining > 0) {
            advisoryText = `Yellow signal ${Math.round(distanceMeters)}m ahead turning red in ${timeRemaining}s. Prepare to stop to save fuel.`;
          } else {
            advisoryText = `Yellow signal ${Math.round(distanceMeters)}m ahead turned red. Stop if safe to do so to save fuel.`;
          }
        }
        
        // Only announce if we haven't announced this exact signal state recently
        if (advisoryText && !announcedSignals.current.has(signalStateId)) {
          console.log(`Traffic Advisory ${index + 1}:`, advisoryText);
          announcedSignals.current.add(signalStateId);
          
          // Speak the advisory
          speak(advisoryText);
          
          // Remove this signal state from the set after 10 seconds to allow re-announcement
          setTimeout(() => {
            announcedSignals.current.delete(signalStateId);
          }, 10000);
        }
      });
    }, 5000);
    
    return () => clearInterval(advisoryTimer);
  }, [isNavigating, trafficLights, selectedFromCoords, userPosition, speak, getAQIForLocation]);

  // Simulate user position updates during navigation
  useEffect(() => {
    if (!isNavigating || !selectedFromCoords || !selectedToCoords) return;
    
    // Store directions and current step
    let directions = null;
    let steps = [];
    
    // Fetch real directions when navigation starts
    const fetchDirections = () => {
      if (typeof window.google !== 'undefined' && window.google.maps && window.google.maps.DirectionsService) {
        const directionsService = new window.google.maps.DirectionsService();
        
        directionsService.route(
          {
            origin: { lat: selectedFromCoords.lat, lng: selectedFromCoords.lng },
            destination: { lat: selectedToCoords.lat, lng: selectedToCoords.lng },
            travelMode: window.google.maps.TravelMode.DRIVING
          },
          (response, status) => {
            if (status === 'OK' && response.routes && response.routes.length > 0) {
              directions = response.routes[0];
              // Extract steps from all legs
              steps = [];
              directions.legs.forEach(leg => {
                steps = steps.concat(leg.steps);
              });
              
              // Set the first instruction as the current instruction
              if (steps.length > 0) {
                const firstStep = steps[0];
                const newInstruction = {
                  icon: getDirectionIcon(firstStep.maneuver),
                  text: firstStep.instructions.replace(/<[^>]*>/g, ''), // Remove HTML tags
                  detail: `for ${firstStep.distance.text}`
                };
                setCurrentInstruction(newInstruction);
                speak(`${newInstruction.text} ${newInstruction.detail}`);
              }
            } else {
              console.error('Directions request failed due to ' + status);
              // Fallback to default instruction
              const fallbackInstruction = {
                icon: '↑',
                text: 'Continue straight',
                detail: 'for 200 meters'
              };
              setCurrentInstruction(fallbackInstruction);
              speak('Continue straight for 200 meters');
            }
          }
        );
      }
    };
    
    fetchDirections();
    
    const startPosition = { lat: selectedFromCoords.lat, lng: selectedFromCoords.lng };
    const endPosition = { lat: selectedToCoords.lat, lng: selectedToCoords.lng };
    
    let progress = 0;
    const interval = setInterval(() => {
      progress += 0.01;
      if (progress <= 1) {
        const currentPosition = {
          lat: startPosition.lat + (endPosition.lat - startPosition.lat) * progress,
          lng: startPosition.lng + (endPosition.lng - startPosition.lng) * progress
        };
        setUserPosition(currentPosition);
        
        // For demo purposes, we'll still use simulated instructions
        // In a real app, this would be based on actual route progress and steps
        let newInstruction;
        if (steps.length > 0 && progress > 0.2 && progress < 0.25) {
          // Simulate reaching the first turn
          if (steps.length > 1) {
            const secondStep = steps[1];
            newInstruction = {
              icon: getDirectionIcon(secondStep.maneuver),
              text: secondStep.instructions.replace(/<[^>]*>/g, ''),
              detail: `in ${secondStep.distance.text}`
            };
          } else {
            newInstruction = {
              icon: '↑',
              text: 'Continue straight',
              detail: 'for 200 meters'
            };
          }
        } else if (progress < 0.2) {
          newInstruction = {
            icon: '↑',
            text: 'Continue straight',
            detail: 'for 200 meters'
          };
        } else if (progress < 0.4) {
          newInstruction = {
            icon: '➡️',
            text: 'Turn right onto Main Street',
            detail: 'in 100 meters'
          };
        } else if (progress < 0.7) {
          newInstruction = {
            icon: '🛣️',
            text: 'Continue on this road',
            detail: 'for 500 meters'
          };
        } else if (progress < 0.9) {
          newInstruction = {
            icon: '⬅️',
            text: 'Turn left to stay on route',
            detail: 'in 200 meters'
          };
        } else {
          newInstruction = {
            icon: '🏁',
            text: 'You have reached',
            detail: 'your destination'
          };
          
          // Trip completed - calculate Eco-Score
          const finalEcoScore = calculateEcoScore(tripStats);
          setEcoScore(finalEcoScore);
          speak('You have reached your destination. Trip completed.');
        }
        
        if (newInstruction && newInstruction.text !== currentInstruction.text) {
          setCurrentInstruction(newInstruction);
          speak(`${newInstruction.text} ${newInstruction.detail}`);
        } else if (newInstruction) {
          setCurrentInstruction(newInstruction);
        }
      } else {
        clearInterval(interval);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isNavigating, selectedFromCoords, selectedToCoords, currentInstruction, tripStats, calculateEcoScore, speak]);

  const toggleFullScreen = () => {
    const element = document.documentElement;
    if (!document.fullscreenElement) {
      if (element.requestFullscreen) {
        element.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const getRouteColor = (aqi) => {
    if (aqi <= 50) return '#10B981';
    if (aqi <= 100) return '#F59E0B';
    if (aqi <= 150) return '#F97316';
    return '#EF4444';
  };

  const getAQICategory = (aqi) => {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    return 'Unhealthy';
  };

  const calculateRecommendedSpeed = (distanceMeters, timeToChange, currentState) => {
    if (currentState === 'green' && timeToChange > 0) {
      const recommendedSpeed = (distanceMeters / 1000) / (timeToChange / 3600);
      return Math.max(10, Math.min(60, Math.round(recommendedSpeed)));
    } else if (currentState === 'red' && timeToChange > 0) {
      const recommendedSpeed = (distanceMeters / 1000) / (timeToChange / 3600);
      return Math.max(10, Math.min(40, Math.round(recommendedSpeed)));
    }
    return null;
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const userLoc = { lat: latitude, lng: longitude };
          setMapCenter(userLoc);
          setFromLocation('Current Location');
          setSelectedFromCoords(userLoc);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enter manually.');
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  useEffect(() => {
    getCurrentLocation();
  }, []);

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column', 
      backgroundColor: '#f8fafc',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    }}>
      <header style={{ 
        background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)', 
        color: 'white', 
        padding: '20px 24px', 
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        position: 'relative'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div>
            <h1 style={{ 
              margin: 0, 
              fontSize: '24px', 
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <span style={{ fontSize: '28px' }}>🧭</span>
              CityLife Nexus
            </h1>
            <p style={{ 
              margin: '4px 0 0 0', 
              fontSize: '15px', 
              opacity: 0.9,
              fontWeight: '400'
            }}>
              Smart navigation with pollution-aware routing
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={getCurrentLocation}
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                backdropFilter: 'blur(10px)',
                transition: 'background-color 0.3s ease'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.3)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.2)'}
            >
              Use Current Location
            </button>
            <button
              onClick={toggleFullScreen}
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                backdropFilter: 'blur(10px)',
                transition: 'background-color 0.3s ease'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.3)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.2)'}
            >
              Full Screen
            </button>
          </div>
        </div>
      </header>
      
      <main style={{ 
        flex: 1, 
        padding: '24px', 
        overflowY: 'auto',
        maxWidth: '1400px',
        margin: '0 auto',
        width: '100%'
      }}>
        {!isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '28px', 
            borderRadius: '16px', 
            marginBottom: '24px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '24px'
            }}>
              <h2 style={{ 
                margin: 0, 
                color: '#1f2937',
                fontSize: '22px',
                fontWeight: '600'
              }}>
                Plan Your Journey
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <label style={{ 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <input
                    type="checkbox"
                    checked={isVoiceEnabled}
                    onChange={(e) => setIsVoiceEnabled(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  Voice Navigation
                </label>
                {isVoiceEnabled && voices.length > 0 && (
                  <select
                    value={selectedVoice?.name || ''}
                    onChange={(e) => {
                      const voice = voices.find(v => v.name === e.target.value);
                      setSelectedVoice(voice);
                    }}
                    style={{
                      padding: '4px 8px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '12px',
                      backgroundColor: 'white'
                    }}
                  >
                    {voices.map((voice, index) => (
                      <option key={index} value={voice.name}>
                        {voice.name} ({voice.lang})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr auto 1fr', 
              gap: '16px', 
              alignItems: 'end',
              marginBottom: '24px'
            }}>
              <div style={{ position: 'relative' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '8px', 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  From
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    ref={fromInputRef}
                    type="text"
                    value={fromLocation}
                    onChange={handleFromLocationChange}
                    placeholder="Enter starting location"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '16px',
                      outline: 'none',
                      transition: 'border-color 0.2s ease'
                    }}
                    onFocus={() => {
                      setShowFromSuggestions(true);
                      // Show suggestions if there are any
                      if (fromSuggestions.length > 0) {
                        setShowFromSuggestions(true);
                      }
                    }}
                  />
                  {showFromSuggestions && fromSuggestions.length > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: 'white',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      marginTop: '4px',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      zIndex: 100,
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}>
                      {fromSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          data-suggestion-item
                          onClick={() => selectFromLocation(suggestion)}
                          style={{
                            padding: '12px 16px',
                            cursor: 'pointer',
                            borderBottom: index < fromSuggestions.length - 1 ? '1px solid #e5e7eb' : 'none',
                            fontSize: '14px',
                            transition: 'background-color 0.2s ease'
                          }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                        >
                          {suggestion.description}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={swapLocations}
                style={{
                  padding: '12px',
                  backgroundColor: '#3B82F6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  height: '44px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#2563EB'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#3B82F6'}
              >
                <span style={{ fontSize: '18px' }}>⇄</span>
              </button>

              <div style={{ position: 'relative' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '8px', 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  To
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    ref={toInputRef}
                    type="text"
                    value={toLocation}
                    onChange={handleToLocationChange}
                    placeholder="Enter destination"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '16px',
                      outline: 'none',
                      transition: 'border-color 0.2s ease'
                    }}
                    onFocus={() => setShowToSuggestions(true)}
                  />
                  {showToSuggestions && toSuggestions.length > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: 'white',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      marginTop: '4px',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      zIndex: 100,
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}>
                      {toSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          data-suggestion-item
                          onClick={() => selectToLocation(suggestion)}
                          style={{
                            padding: '12px 16px',
                            cursor: 'pointer',
                            borderBottom: index < toSuggestions.length - 1 ? '1px solid #e5e7eb' : 'none',
                            fontSize: '14px',
                            transition: 'background-color 0.2s ease'
                          }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                        >
                          {suggestion.description}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '16px',
              marginBottom: '24px'
            }}>
              <div>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '8px', 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  Route Preference
                </label>
                <select
                  value={routePreference}
                  onChange={(e) => setRoutePreference(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '16px',
                    outline: 'none',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="fastest">Fastest Route</option>
                  <option value="safest">Safest Route</option>
                  <option value="cleanest">Cleanest Air Route</option>
                </select>
              </div>

              <div>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '8px', 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  Vehicle Type
                </label>
                <select
                  value={vehicleType}
                  onChange={(e) => setVehicleType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '16px',
                    outline: 'none',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="car">Car</option>
                  <option value="bike">Bike</option>
                  <option value="bus">Bus</option>
                  <option value="truck">Truck</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleRouteSearch}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '14px',
                backgroundColor: isLoading ? '#9CA3AF' : '#3B82F6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
              onMouseEnter={(e) => {
                if (!isLoading) e.target.style.backgroundColor = '#2563EB';
              }}
              onMouseLeave={(e) => {
                if (!isLoading) e.target.style.backgroundColor = '#3B82F6';
              }}
            >
              {isLoading ? (
                <>
                  <span>🔍</span> Finding best routes...
                </>
              ) : (
                <>
                  <span>🔍</span> Find Routes
                </>
              )}
            </button>
          </div>
        )}

        {showRoutes && !isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '24px', 
            borderRadius: '16px', 
            marginBottom: '24px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <h2 style={{ 
              margin: '0 0 20px 0', 
              color: '#1f2937',
              fontSize: '20px',
              fontWeight: '600'
            }}>
              Available {routePreference.charAt(0).toUpperCase() + routePreference.slice(1)} Route
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {routes.map((route) => (
                <div 
                  key={route.id}
                  onClick={() => selectRoute(route)}
                  style={{
                    border: selectedRouteId === route.id ? '2px solid #3B82F6' : '1px solid #e5e7eb',
                    borderRadius: '12px',
                    padding: '20px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    backgroundColor: selectedRouteId === route.id ? '#EFF6FF' : 'white'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedRouteId !== route.id) e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.08)';
                  }}
                  onMouseLeave={(e) => {
                    if (selectedRouteId !== route.id) e.target.style.boxShadow = 'none';
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                    <div>
                      <h3 style={{ 
                        margin: '0 0 8px 0', 
                        fontSize: '18px',
                        fontWeight: '600',
                        color: '#1f2937'
                      }}>
                        {route.name}
                      </h3>
                      <p style={{ 
                        margin: 0, 
                        fontSize: '14px',
                        color: '#6b7280'
                      }}>
                        {route.description}
                      </p>
                    </div>
                    <div style={{ 
                      backgroundColor: getRouteColor(route.aqi),
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}>
                      {getAQICategory(route.aqi)}
                    </div>
                  </div>
                  
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(3, 1fr)', 
                    gap: '12px',
                    marginBottom: '16px'
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        fontSize: '20px',
                        fontWeight: '700',
                        color: '#1f2937'
                      }}>
                        {route.time}
                      </div>
                      <div style={{ 
                        fontSize: '12px',
                        color: '#6b7280'
                      }}>
                        mins
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        fontSize: '20px',
                        fontWeight: '700',
                        color: '#1f2937'
                      }}>
                        {route.distance}
                      </div>
                      <div style={{ 
                        fontSize: '12px',
                        color: '#6b7280'
                      }}>
                        km
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        fontSize: '20px',
                        fontWeight: '700',
                        color: '#1f2937'
                      }}>
                        {route.aqi}
                      </div>
                      <div style={{ 
                        fontSize: '12px',
                        color: '#6b7280'
                      }}>
                        AQI
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startNavigation(route);
                    }}
                    style={{
                      width: '100%',
                      padding: '10px',
                      backgroundColor: '#10B981',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#059669'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = '#10B981'}
                  >
                    START NAV
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '24px', 
            borderRadius: '16px', 
            marginBottom: '24px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <h2 style={{ 
                margin: 0, 
                color: '#1f2937',
                fontSize: '20px',
                fontWeight: '600'
              }}>
                Navigation in Progress
              </h2>
              <button
                onClick={() => setIsNavigating(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#EF4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#DC2626'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#EF4444'}
              >
                Stop Navigation
              </button>
            </div>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '20px',
              marginBottom: '24px'
            }}>
              <div style={{ 
                backgroundColor: '#F9FAFB',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid #E5E7EB'
              }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ 
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: '#3B82F6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '24px'
                  }}>
                    {currentInstruction.icon}
                  </div>
                  <div>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      {currentInstruction.text}
                    </h3>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '14px',
                      color: '#6b7280'
                    }}>
                      {currentInstruction.detail}
                    </p>
                  </div>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ 
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: '#F97316',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '24px'
                  }}>
                    ⏳
                  </div>
                  <div>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      {nextSignal ? `${nextSignal.current_state.color.toUpperCase()} signal in ${nextSignal.current_state.time_remaining}s` : 'No signals in range'}
                    </h3>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '14px',
                      color: '#6b7280'
                    }}>
                      {nextSignal ? `${nextSignal.distanceMeters}m ahead` : ''}
                    </p>
                  </div>
                </div>
              </div>
              
              <div style={{ 
                backgroundColor: '#F9FAFB',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid #E5E7EB'
              }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ 
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: '#1D4ED8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '24px'
                  }}>
                    📈
                  </div>
                  <div>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      Trip Statistics
                    </h3>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '14px',
                      color: '#6b7280'
                    }}>
                      {tripStats.signalsOnGreen} green signals, {tripStats.signalsOnRed} red signals
                    </p>
                  </div>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ 
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: '#EC4899',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '24px'
                  }}>
                    🌳
                  </div>
                  <div>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      Pollution Exposure
                    </h3>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '14px',
                      color: '#6b7280'
                    }}>
                      {tripStats.pollutionExposure.toFixed(2)} AQI-hours
                    </p>
                  </div>
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ 
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    backgroundColor: '#EAB308',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '24px'
                  }}>
                    ⏳
                  </div>
                  <div>
                    <h3 style={{ 
                      margin: '0 0 4px 0', 
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      Idling Time
                    </h3>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '14px',
                      color: '#6b7280'
                    }}>
                      {tripStats.idlingTime} seconds
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div id="navigation-map" style={{ height: '400px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #E5E7EB' }}>
              <MapComponent 
                center={mapCenter}
                trafficLights={trafficLights}
                userPosition={userPosition || selectedFromCoords}
                destination={selectedToCoords}
                fromCoords={selectedFromCoords}
                toCoords={selectedToCoords}
                isNavigating={isNavigating}
              />
            </div>
          </div>
        )}
        {ecoScore && (
          <div style={{ 
            backgroundColor: '#F9FAFB',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #E5E7EB',
            marginTop: '24px'
          }}>
            <h3 style={{ 
              margin: '0 0 16px 0', 
              fontSize: '18px',
              fontWeight: '600',
              color: '#1f2937'
            }}>
              📊 Trip Health Report
            </h3>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: '16px'
            }}>
              <div style={{ 
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #E5E7EB',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '24px',
                  fontWeight: '700',
                  color: '#10B981',
                  marginBottom: '8px'
                }}>
                  {ecoScore.signalsOnGreen}
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#6b7280'
                }}>
                  Signals on Green
                </div>
              </div>
              
              <div style={{ 
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #E5E7EB',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '24px',
                  fontWeight: '700',
                  color: '#EF4444',
                  marginBottom: '8px'
                }}>
                  {ecoScore.pollutionReduction}%
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#6b7280'
                }}>
                  Pollution Reduction
                </div>
              </div>
              
              <div style={{ 
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #E5E7EB',
                textAlign: 'center'
              }}>
                <div style={{ 
                  fontSize: '24px',
                  fontWeight: '700',
                  color: '#3B82F6',
                  marginBottom: '8px'
                }}>
                  {ecoScore.fuelSaved}ml
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#6b7280'
                }}>
                  Fuel Saved
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      
      <footer style={{ 
        background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)', 
        color: 'white', 
        padding: '20px 24px', 
        boxShadow: '0 -4px 6px rgba(0,0,0,0.1)',
        position: 'relative'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div>
            <p style={{ 
              margin: 0, 
              fontSize: '14px', 
              opacity: 0.9,
              fontWeight: '400'
            }}>
              © 2025 CityLife Nexus. All rights reserved.
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            
            
            <button
              onClick={() => handleNavigation('/dashboard')}
              style={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.3)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.2)'}
            >
              <span>📊</span>
              Dashboard
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default NavigationView;