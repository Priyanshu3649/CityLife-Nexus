import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import MapComponent from './MapComponent';

const NavigationView = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [routePreference, setRoutePreference] = useState('balanced');
  const [vehicleType, setVehicleType] = useState('car');
  const [showRoutes, setShowRoutes] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [trafficLights, setTrafficLights] = useState([]);
  const [voiceNavigation, setVoiceNavigation] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 28.6139, lng: 77.2090 });
  
  // New states for advanced features
  const [tripLogs, setTripLogs] = useState([]);
  const [ecoScore, setEcoScore] = useState(null);
  const [isRerouting, setIsRerouting] = useState(false);
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

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      const isSuggestionClick = event.target.closest('[data-suggestion-item]');
      
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

  // Emergency auto-reroute monitoring
  useEffect(() => {
    if (!isNavigating) return;
    
    const monitorConditions = async () => {
      try {
        // Check for emergency conditions (accidents, congestion, pollution spikes)
        const response = await fetch('http://127.0.0.1:8001/api/v1/emergency/alerts', {
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
              speakAlert(`Emergency Alert: ${criticalAlert.message}. Rerouting due to ${criticalAlert.type} ahead.`);
              triggerReroute();
            }
          }
        }
      } catch (error) {
        console.error('Error checking emergency conditions:', error);
      }
    };
    
    const interval = setInterval(monitorConditions, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [isNavigating]);

  const handleNavigation = (path) => {
    navigate(path);
  };

  // Fetch traffic light data for the route
  const fetchTrafficLightData = async (fromCoords, toCoords) => {
    try {
      const routeCoordinates = [
        { latitude: fromCoords.lat, longitude: fromCoords.lng },
        { latitude: toCoords.lat, longitude: toCoords.lng }
      ];
      
      const response = await fetch('http://127.0.0.1:8001/api/v1/signals/along-route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(routeCoordinates)
      });
      
      if (response.ok) {
        const signals = await response.json();
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
        setTrafficLights(trafficLightsData);
      } else {
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
  }, []);

  // Google Places Autocomplete
  const searchPlaces = async (query, setSuggestions) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8001/api/v1/maps/autocomplete?query=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.predictions || []);
      }
    } catch (error) {
      console.error('Error fetching place suggestions:', error);
      setSuggestions([
        { description: `${query} - Delhi, India`, place_id: 'mock1' },
        { description: `${query} - Mumbai, India`, place_id: 'mock2' },
        { description: `${query} - Bangalore, India`, place_id: 'mock3' }
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
      const response = await fetch(`http://127.0.0.1:8001/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          setSelectedFromCoords(convertedCoords);
        }
      }
    } catch (error) {
      console.error('Error fetching geocode data:', error);
    }
  };

  const selectToLocation = async (suggestion) => {
    setToLocation(suggestion.description);
    setShowToSuggestions(false);
    setToSuggestions([]);
    
    try {
      const response = await fetch(`http://127.0.0.1:8001/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          setSelectedToCoords(convertedCoords);
        }
      }
    } catch (error) {
      console.error('Error fetching geocode data:', error);
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

  // Emergency auto-reroute function
  const triggerReroute = async () => {
    if (!selectedFromCoords || !selectedToCoords) return;
    
    setIsRerouting(true);
    speakAlert("Rerouting due to emergency conditions ahead.");
    
    try {
      const response = await fetch('http://127.0.0.1:8001/api/v1/maps/reroute', {
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
            prioritize_time: routePreference === 'fastest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_air_quality: routePreference === 'cleanest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_safety: 0.9, // High priority for safety in rerouting
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
        speakAlert("New route calculated. Follow the updated directions.");
      }
    } catch (error) {
      console.error('Error during rerouting:', error);
      speakAlert("Unable to calculate new route. Continue on current path with caution.");
    } finally {
      setIsRerouting(false);
    }
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
      const response = await fetch('http://127.0.0.1:8001/api/v1/maps/routes-with-aqi', {
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
            prioritize_time: routePreference === 'fastest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_air_quality: routePreference === 'cleanest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_safety: 0.2,
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
      const mockRoutes = [
        {
          id: '1',
          name: 'Fastest Route',
          time: 18,
          aqi: 160,
          distance: 12.5,
          type: 'fastest',
          description: 'Via main roads with heavy traffic'
        },
        {
          id: '2', 
          name: 'Clean Air Route',
          time: 25,
          aqi: 85,
          distance: 14.2,
          type: 'cleanest',
          description: 'Via parks and residential areas'
        },
        {
          id: '3',
          name: 'Balanced Route',
          time: 21,
          aqi: 120,
          distance: 13.1,
          type: 'balanced',
          description: 'Optimal time and air quality'
        }
      ];
      setRoutes(mockRoutes);
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
    speakAlert(selectionMessage);
  };

  const startNavigation = async (route) => {
    if (selectedFromCoords && selectedToCoords) {
      setSelectedRouteId(route.id);
      setIsNavigating(true);
      setTripLogs([]); // Reset trip logs
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
      
      await fetchTrafficLightData(selectedFromCoords, selectedToCoords);
      
      setTimeout(() => {
        const mapElement = document.getElementById('navigation-map');
        if (mapElement) {
          mapElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
      
      const startMessage = `🧭 Navigation started! Following route: ${route.name}. Estimated time: ${route.time} minutes. Follow the directions on the map and listen for traffic advisories.`;
      alert(startMessage);
      speakAlert(startMessage);
    } else {
      const errorMessage = 'Please select valid start and end locations first.';
      alert(errorMessage);
      speakAlert(errorMessage);
    }
  };

  const calculateDistance = (coord1, coord2) => {
    const R = 6371;
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
    const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const speakAlert = (text) => {
    if (!voiceNavigation) return;
    
    if ('speechSynthesis' in window) {
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = 'en-US';
      speech.volume = 1;
      speech.rate = 1;
      speech.pitch = 1;
      window.speechSynthesis.speak(speech);
    } else {
      console.log('Text-to-speech not supported in this browser');
    }
  };

  const speakNavigationInstruction = (instruction) => {
    speakAlert(`Navigation: ${instruction.text} ${instruction.detail}`);
  };

  // Monitor traffic lights and provide advisories during navigation
  useEffect(() => {
    if (!isNavigating || trafficLights.length === 0 || !selectedFromCoords) return;
    
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
        setTripStats(prev => {
          const newStats = { ...prev };
          if (color === 'red') {
            newStats.signalsOnRed += 1;
            newStats.idlingTime += timeRemaining;
          } else if (color === 'green') {
            newStats.signalsOnGreen += 1;
          }
          newStats.pollutionExposure += (getAQIForLocation(light.coordinates) * (timeRemaining / 60)); // AQI * hours
          return newStats;
        });
        
        const recommendedSpeed = calculateRecommendedSpeed(distanceMeters, timeRemaining, color);
        const mlAdvisory = getMLBasedAdvisory(light, distanceMeters);
        
        let advisoryText = '';
        if (color === 'red') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            if (recommendedSpeed) {
              advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead changes to green in ${timeRemaining}s. Slow down to ${recommendedSpeed} km/h to avoid waiting. ${mlAdvisory.message}`;
            } else {
              advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead changes to green in ${timeRemaining}s. Slow down to avoid waiting. ${mlAdvisory.message}`;
            }
          } else if (timeRemaining === 0) {
            advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turning green now. Proceed carefully.`;
          }
        } else if (color === 'green') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            if (recommendedSpeed) {
              advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turning yellow in ${timeRemaining}s. Maintain speed at ${recommendedSpeed} km/h. ${mlAdvisory.message}`;
            } else {
              advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turning yellow in ${timeRemaining}s. Maintain speed. ${mlAdvisory.message}`;
            }
          } else if (timeRemaining === 0) {
            advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turning yellow now. Prepare to stop. ${mlAdvisory.message}`;
          }
        } else if (color === 'yellow') {
          if (timeRemaining > 0) {
            advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turning red in ${timeRemaining}s. Prepare to stop. ${mlAdvisory.message}`;
          } else {
            advisoryText = `${lightId} ${Math.round(distanceMeters)}m ahead turned red. Stop if safe to do so. ${mlAdvisory.message}`;
          }
        }
        
        if (advisoryText) {
          console.log(`Traffic Advisory ${index + 1}:`, advisoryText);
          speakAlert(advisoryText);
        }
      });
    }, 5000);
    
    return () => clearInterval(advisoryTimer);
  }, [isNavigating, trafficLights, selectedFromCoords, userPosition, voiceNavigation]);

  // Simulate user position updates during navigation
  useEffect(() => {
    if (!isNavigating || !selectedFromCoords || !selectedToCoords) return;
    
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
        
        let newInstruction;
        if (progress < 0.2) {
          newInstruction = {
            icon: '↑',
            text: 'Continue straight',
            detail: 'for 200 meters'
          };
        } else if (progress < 0.4) {
          newInstruction = {
            icon: '➡️',
            text: 'Turn left',
            detail: 'at next intersection'
          };
        } else if (progress < 0.7) {
          newInstruction = {
            icon: '🛣️',
            text: 'Continue on this road',
            detail: 'for 500 meters'
          };
        } else if (progress < 0.9) {
          newInstruction = {
            icon: '⬇️',
            text: 'Turn right',
            detail: 'to stay on route'
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
          speakAlert(`Trip completed! ${finalEcoScore.signalsOnGreen} signals caught green, ${finalEcoScore.pollutionReduction}% lower pollution exposure, ${finalEcoScore.fuelSaved}ml fuel saved.`);
        }
        
        if (newInstruction.text !== currentInstruction.text) {
          setCurrentInstruction(newInstruction);
          speakNavigationInstruction(newInstruction);
        } else {
          setCurrentInstruction(newInstruction);
        }
      } else {
        clearInterval(interval);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isNavigating, selectedFromCoords, selectedToCoords, currentInstruction, tripStats, calculateEcoScore]);

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

  const getMLBasedAdvisory = (light, distanceMeters, userSpeed = 40) => {
    const { current_state, time_remaining } = light;
    const color = current_state.color;
    const timeToReach = (distanceMeters / 1000) / (userSpeed / 3600);
    
    let recommendation = {};
    
    if (color === 'red') {
      if (timeToReach < time_remaining - 5) {
        recommendation = {
          action: 'slow_down',
          message: 'Slow down to reduce fuel consumption while waiting',
          speedAdjustment: -10
        };
      } else if (timeToReach > time_remaining + 10) {
        recommendation = {
          action: 'maintain_speed',
          message: 'Maintain current speed, light will be green when you arrive',
          speedAdjustment: 0
        };
      } else {
        recommendation = {
          action: 'optimal_approach',
          message: 'Approach at optimal speed to catch the green light',
          speedAdjustment: 5
        };
      }
    } else if (color === 'green') {
      if (timeToReach < time_remaining * 0.8) {
        recommendation = {
          action: 'maintain_speed',
          message: 'Maintain current speed, you\'ll clear the intersection comfortably',
          speedAdjustment: 0
        };
      } else if (timeToReach > time_remaining * 1.2) {
        recommendation = {
          action: 'slight_acceleration',
          message: 'Slight acceleration to clear intersection before yellow light',
          speedAdjustment: 5
        };
      } else {
        recommendation = {
          action: 'optimal_approach',
          message: 'Current approach is optimal for green light clearance',
          speedAdjustment: 0
        };
      }
    } else if (color === 'yellow') {
      if (timeToReach < time_remaining * 0.7) {
        recommendation = {
          action: 'maintain_speed',
          message: 'Maintain speed to clear intersection before red light',
          speedAdjustment: 0
        };
      } else {
        recommendation = {
          action: 'prepare_to_stop',
          message: 'Prepare to stop safely before the intersection',
          speedAdjustment: -20
        };
      }
    }
    
    return recommendation;
  };

  const getAQIForLocation = (coordinates) => {
    // Mock AQI values for demonstration
    const mockAQIValues = [
      { coordinates: { lat: 28.6315, lng: 77.2167 }, aqi: 120 },
      { coordinates: { lat: 28.6280, lng: 77.2410 }, aqi: 180 },
      { coordinates: { lat: 28.6129, lng: 77.2295 }, aqi: 90 }
    ];
    
    // Find the two closest AQI sensors
    const sortedSensors = mockAQIValues.sort((a, b) => 
      calculateDistance(coordinates, a.coordinates) - calculateDistance(coordinates, b.coordinates)
    );
    
    if (sortedSensors.length >= 2) {
      return interpolateAQI(coordinates, sortedSensors[0], sortedSensors[1]);
    }
    
    return sortedSensors[0] ? sortedSensors[0].aqi : 100;
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const userLoc = { lat: latitude, lng: longitude };
          setUserLocation(userLoc);
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
              SafeAir Navigator
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
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  fontSize: '14px',
                  color: '#4b5563',
                  fontWeight: '500'
                }}>
                  <input
                    type="checkbox"
                    checked={voiceNavigation}
                    onChange={(e) => setVoiceNavigation(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  Voice Navigation
                </label>
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
                    onFocus={() => setShowFromSuggestions(true)}
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
                  <option value="balanced">Balanced Route</option>
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
              Available Routes
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
                  justifyContent: 'space-between',
                  marginTop: '16px'
                }}>
                  <div>
                    <div style={{ 
                      fontSize: '12px',
                      color: '#6b7280',
                      marginBottom: '4px'
                    }}>
                      Next Signal
                    </div>
                    <div style={{ 
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      {nextSignal ? nextSignal.intersection_name : 'None detected'}
                    </div>
                  </div>
                  <div>
                    <div style={{ 
                      fontSize: '12px',
                      color: '#6b7280',
                      marginBottom: '4px'
                    }}>
                      Status
                    </div>
                    <div style={{ 
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1f2937'
                    }}>
                      {nextSignal ? nextSignal.current_state.color : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
              
              <div style={{ 
                backgroundColor: '#F9FAFB',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid #E5E7EB'
              }}>
                <h3 style={{ 
                  margin: '0 0 16px 0', 
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1f2937'
                }}>
                  Traffic Light Status
                </h3>
                
                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  {trafficLights.slice(0, 3).map((light, index) => (
                    <div 
                      key={light.light_id}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px',
                        backgroundColor: 'white',
                        borderRadius: '8px',
                        border: '1px solid #E5E7EB'
                      }}
                    >
                      <div style={{ 
                        fontSize: '14px',
                        fontWeight: '500',
                        color: '#1f2937'
                      }}>
                        {light.intersection_name}
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px'
                      }}>
                        <div style={{ 
                          width: '12px',
                          height: '12px',
                          borderRadius: '50%',
                          backgroundColor: light.current_state.color === 'red' ? '#EF4444' : light.current_state.color === 'yellow' ? '#F59E0B' : '#10B981'
                        }}>
                        </div>
                        <div style={{ 
                          fontSize: '14px',
                          fontWeight: '500',
                          color: '#6b7280'
                        }}>
                          {light.current_state.time_remaining}s
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div id="navigation-map" style={{ height: '400px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #E5E7EB' }}>
              <MapComponent 
                center={mapCenter}
                trafficLights={trafficLights}
                userPosition={userPosition || selectedFromCoords}
                destination={selectedToCoords}
              />
            </div>
            
            {/* Eco-Score / Trip Health Report */}
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
              © 2023 SafeAir Navigator. All rights reserved.
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => handleNavigation('/about')}
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
              About
            </button>
            <button
              onClick={() => handleNavigation('/contact')}
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
              <span>📍</span>
              Current Location
            </button>
            
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
