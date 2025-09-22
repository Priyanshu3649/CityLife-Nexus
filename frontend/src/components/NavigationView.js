import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MapComponent from './MapComponent'; // Import MapComponent

const NavigationView = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [routePreference, setRoutePreference] = useState('balanced');
  const [vehicleType, setVehicleType] = useState('car'); // Add vehicle type state
  const [showRoutes, setShowRoutes] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRouteId, setSelectedRouteId] = useState(null); // Add selected route state
  const [trafficLights, setTrafficLights] = useState([]); // Add traffic lights state
  
  // Google Maps autocomplete states
  const [fromSuggestions, setFromSuggestions] = useState([]);
  const [toSuggestions, setToSuggestions] = useState([]);
  const [showFromSuggestions, setShowFromSuggestions] = useState(false);
  const [showToSuggestions, setShowToSuggestions] = useState(false);
  const [selectedFromCoords, setSelectedFromCoords] = useState(null);
  const [selectedToCoords, setSelectedToCoords] = useState(null);
  
  const fromInputRef = useRef(null);
  const toInputRef = useRef(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Check if click is on a suggestion item
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
          // Always update the time remaining, even if it goes to 0 or below
          const newTimeRemaining = Math.max(0, light.current_state.time_remaining - 1);
          
          // If time reaches 0, we need to determine the next state
          let newColor = light.current_state.color;
          let newTimeToNextChange = newTimeRemaining;
          
          // When time reaches 0, change the signal state
          if (light.current_state.time_remaining === 1) {
            if (light.current_state.color === 'red') {
              newColor = 'green';
              // In a real system, this would come from the API, but for demo we'll simulate
              newTimeToNextChange = 30; // Simulate green duration
            } else if (light.current_state.color === 'green') {
              newColor = 'yellow';
              newTimeToNextChange = 3; // Simulate yellow duration
            } else if (light.current_state.color === 'yellow') {
              newColor = 'red';
              // In a real system, this would come from the API, but for demo we'll simulate
              newTimeToNextChange = 45; // Simulate red duration
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

  const handleNavigation = (path) => {
    navigate(path);
  };

  // Fetch traffic light data for the route
  const fetchTrafficLightData = async (fromCoords, toCoords) => {
    try {
      // Create a simple route with start and end points
      const routeCoordinates = [
        { latitude: fromCoords.latitude, longitude: fromCoords.longitude },
        { latitude: toCoords.latitude, longitude: toCoords.longitude }
      ];
      
      // Fetch traffic lights along the route
      const response = await fetch('http://127.0.0.1:8000/api/v1/signals/along-route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(routeCoordinates)
      });
      
      if (response.ok) {
        const signals = await response.json();
        
        // Transform the data to match our expected format
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
        // Fallback to mock data if API fails
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
      // Fallback to mock data on error
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
    console.log('Searching places for query:', query);
    if (query.length < 3) {
      console.log('Query too short, clearing suggestions');
      setSuggestions([]);
      return;
    }

    try {
      console.log('Fetching suggestions for:', query);
      const response = await fetch(`http://127.0.0.1:8000/api/v1/maps/autocomplete?query=${encodeURIComponent(query)}`);
      console.log('API response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('Received suggestions:', data.predictions);
        setSuggestions(data.predictions || []);
      } else {
        console.error('API error response:', response.status);
      }
    } catch (error) {
      console.error('Error fetching place suggestions:', error);
      // Fallback to mock suggestions for demo
      setSuggestions([
        { description: `${query} - Delhi, India`, place_id: 'mock1' },
        { description: `${query} - Mumbai, India`, place_id: 'mock2' },
        { description: `${query} - Bangalore, India`, place_id: 'mock3' }
      ]);
    }
  };

  const handleFromLocationChange = (e) => {
    const value = e.target.value;
    console.log('From location changed:', value);
    setFromLocation(value);
    setShowFromSuggestions(true);
    searchPlaces(value, setFromSuggestions);
  };

  const handleToLocationChange = (e) => {
    const value = e.target.value;
    console.log('To location changed:', value);
    setToLocation(value);
    setShowToSuggestions(true);
    searchPlaces(value, setToSuggestions);
  };

  const selectFromLocation = async (suggestion) => {
    console.log('Selecting from location:', suggestion);
    setFromLocation(suggestion.description);
    setShowFromSuggestions(false);
    setFromSuggestions([]);
    
    // Get coordinates for the selected place
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      console.log('Geocode response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('Geocode data:', data);
        console.log('Coordinates:', data.coordinates);
        // Convert coordinates format from {latitude, longitude} to {lat, lng}
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          console.log('Converted coordinates:', convertedCoords);
          setSelectedFromCoords(convertedCoords);
        }
      } else {
        console.error('Geocode API error:', response.status);
      }
    } catch (error) {
      console.error('Error geocoding from location:', error);
    }
  };

  const selectToLocation = async (suggestion) => {
    console.log('Selecting to location:', suggestion);
    setToLocation(suggestion.description);
    setShowToSuggestions(false);
    setToSuggestions([]);
    
    // Get coordinates for the selected place
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      console.log('Geocode response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('Geocode data:', data);
        console.log('Coordinates:', data.coordinates);
        // Convert coordinates format from {latitude, longitude} to {lat, lng}
        if (data.coordinates) {
          const convertedCoords = {
            lat: data.coordinates.latitude,
            lng: data.coordinates.longitude
          };
          console.log('Converted coordinates:', convertedCoords);
          setSelectedToCoords(convertedCoords);
        }
      } else {
        console.error('Geocode API error:', response.status);
      }
    } catch (error) {
      console.error('Error geocoding to location:', error);
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
    setSelectedRouteId(null); // Clear any previously selected route

    try {
      // Call backend API to get real routes with AQI data
      const response = await fetch('http://127.0.0.1:8000/api/v1/maps/routes-with-aqi', {
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
          vehicle_type: vehicleType // Use vehicleType state instead of hardcoded 'car'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRoutes(data.routes || []);
        setShowRoutes(true);
      
        // Fetch traffic light data for the route
        await fetchTrafficLightData(
          { latitude: selectedFromCoords.lat, longitude: selectedFromCoords.lng },
          { latitude: selectedToCoords.lat, longitude: selectedToCoords.lng }
        );
      } else {
        throw new Error('Failed to fetch routes');
      }
    } catch (error) {
      console.error('Error fetching routes:', error);
      // Fallback to mock data if API fails
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

  const selectRoute = (route) => {
    // Set the selected route to display on the map (preview mode)
    setSelectedRouteId(route.id);
    
    // Show route selection confirmation (preview mode)
    alert(`🗺️ Route selected: ${route.name}\n⏱️ ${route.time} min • 🌫️ AQI ${route.aqi}\nRoute is now displayed on the map for preview.`);
  };

  const startNavigation = async (route) => {
    // Set the selected route to display on the map
    setSelectedRouteId(route.id);
    
    // Initialize navigation state
    setIsNavigating(true);
    
    // Fetch traffic lights along the route if not already fetched
    if (selectedFromCoords && selectedToCoords) {
      await fetchTrafficLightData(
        { latitude: selectedFromCoords.lat, longitude: selectedFromCoords.lng },
        { latitude: selectedToCoords.lat, longitude: selectedToCoords.lng }
      );
    }
    
    // Scroll to map view
    setTimeout(() => {
      const mapElement = document.getElementById('navigation-map');
      if (mapElement) {
        mapElement.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  const calculateDistance = (coord1, coord2) => {
    // Calculate distance between two coordinates (Haversine formula)
    const R = 6371; // Earth radius in km
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
    const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // Distance in km
  };

  const speakAlert = (text) => {
    // Text-to-Speech for voice alerts
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

  const [isNavigating, setIsNavigating] = useState(false);
  const [nextSignal, setNextSignal] = useState(null);
  // const [vehicleSpeed, setVehicleSpeed] = useState(40); // Default speed in km/h - will be used later

  // Monitor traffic lights and provide advisories during navigation
  useEffect(() => {
    if (!isNavigating || trafficLights.length === 0 || !selectedFromCoords) return;
    
    const advisoryTimer = setInterval(() => {
      // Find the next traffic light on the route based on distance, not just time remaining
      const lightsWithDistance = trafficLights
        .map(light => {
          // Calculate distance to this traffic light from start position
          const distance = calculateDistance(selectedFromCoords, light.coordinates);
          return { ...light, distance };
        })
        .sort((a, b) => a.distance - b.distance);
      
      if (lightsWithDistance.length > 0) {
        const nextLight = lightsWithDistance[0];
        setNextSignal(nextLight);
        
        const distanceMeters = nextLight.distance * 1000;
        const timeRemaining = nextLight.current_state.time_remaining;
        const color = nextLight.current_state.color;
        
        // Provide advisories based on signal state and timing
        if (color === 'red') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            const advisoryText = `⚠️ Red light ahead in ${Math.round(distanceMeters)}m, turns green in ${timeRemaining}s. Slow down to avoid stopping.`;
            console.log(advisoryText);
            speakAlert(`Red light ahead in ${Math.round(distanceMeters)} meters, turns green in ${timeRemaining} seconds. Slow down to avoid stopping.`);
          } else if (timeRemaining === 0) {
            // Red light just turned green
            const advisoryText = `✅ Red light just turned green! Proceed carefully.`;
            console.log(advisoryText);
            speakAlert('Red light just turned green. Proceed carefully.');
          }
        } else if (color === 'green') {
          if (timeRemaining <= 15 && timeRemaining > 0) {
            const advisoryText = `⚠️ Green light ahead in ${Math.round(distanceMeters)}m, turns yellow in ${timeRemaining}s. Maintain speed.`;
            console.log(advisoryText);
            speakAlert(`Green light ahead in ${Math.round(distanceMeters)} meters, turns yellow in ${timeRemaining} seconds. Maintain speed.`);
          } else if (timeRemaining === 0) {
            // Green light just turned yellow
            const advisoryText = `⚠️ Green light just turned yellow! Prepare to stop.`;
            console.log(advisoryText);
            speakAlert('Green light just turned yellow. Prepare to stop.');
          }
        } else if (color === 'yellow') {
          if (timeRemaining > 0) {
            const advisoryText = `⚠️ Yellow light ahead in ${Math.round(distanceMeters)}m. Prepare to stop.`;
            console.log(advisoryText);
            speakAlert(`Yellow light ahead in ${Math.round(distanceMeters)} meters. Prepare to stop.`);
          } else {
            // Yellow light just turned red
            const advisoryText = `🛑 Yellow light just turned red! Stop if safe to do so.`;
            console.log(advisoryText);
            speakAlert('Yellow light just turned red. Stop if safe to do so.');
          }
        }
      }
    }, 3000); // Check every 3 seconds during navigation
    
    return () => clearInterval(advisoryTimer);
  }, [isNavigating, trafficLights, selectedFromCoords]);

  const toggleFullScreen = () => {
    // Toggle full-screen mode for navigation
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
    if (aqi <= 50) return '#10B981'; // Green
    if (aqi <= 100) return '#F59E0B'; // Yellow
    if (aqi <= 150) return '#F97316'; // Orange
    return '#EF4444'; // Red
  };

  const getAQICategory = (aqi) => {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    return 'Unhealthy';
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      {console.log('NavigationView state:', { fromLocation, toLocation, selectedFromCoords, selectedToCoords, showRoutes, routes, selectedRouteId })}
      {/* Header */}
      <header style={{ 
        backgroundColor: '#3B82F6', 
        color: 'white', 
        padding: '16px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)' 
      }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
          SafeAir Navigator
        </h1>
        <p style={{ margin: '4px 0 0 0', fontSize: '14px', opacity: 0.9 }}>
          Smart navigation with pollution-aware routing
        </p>
      </header>

      {/* Main content area */}
      <main style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
        {/* Route Planning Section */}
        {!isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '12px', 
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>Plan Your Route</h2>
            
            <div style={{ marginBottom: '16px', position: 'relative' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', color: '#374151' }}>
                📍 From:
              </label>
              <input
                ref={fromInputRef}
                type="text"
                value={fromLocation}
                onChange={handleFromLocationChange}
                onFocus={() => setShowFromSuggestions(true)}
                placeholder="Enter starting location (e.g., Connaught Place, Delhi)"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              />
              
              {/* Autocomplete Dropdown for From Location */}
              {showFromSuggestions && fromSuggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  zIndex: 1000,
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {console.log('Rendering from suggestions:', fromSuggestions)}
                  {fromSuggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      data-suggestion-item="true"
                      onClick={() => selectFromLocation(suggestion)}
                      style={{
                        padding: '12px',
                        cursor: 'pointer',
                        borderBottom: index < fromSuggestions.length - 1 ? '1px solid #f3f4f6' : 'none',
                        fontSize: '14px',
                        color: '#374151'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                    >
                      📍 {suggestion.description}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ marginBottom: '16px', position: 'relative' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', color: '#374151' }}>
                🎯 To:
              </label>
              <input
                ref={toInputRef}
                type="text"
                value={toLocation}
                onChange={handleToLocationChange}
                onFocus={() => setShowToSuggestions(true)}
                placeholder="Enter destination (e.g., India Gate, Delhi)"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              />
              
              {/* Autocomplete Dropdown for To Location */}
              {showToSuggestions && toSuggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  zIndex: 1000,
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {console.log('Rendering to suggestions:', toSuggestions)}
                  {toSuggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      data-suggestion-item="true"
                      onClick={() => selectToLocation(suggestion)}
                      style={{
                        padding: '12px',
                        cursor: 'pointer',
                        borderBottom: index < toSuggestions.length - 1 ? '1px solid #f3f4f6' : 'none',
                        fontSize: '14px',
                        color: '#374151'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                    >
                      🎯 {suggestion.description}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Vehicle Type Selection */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#374151' }}>
                🚗 Vehicle Type:
              </label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[
                  { value: 'bike', label: '🏍️ Bike' },
                  { value: 'auto', label: '🛺 Auto' },
                  { value: 'car', label: '🚗 Car' },
                  { value: 'bus', label: '🚌 Bus' }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setVehicleType(option.value)}
                    style={{
                      padding: '8px 12px',
                      border: `2px solid ${vehicleType === option.value ? '#3B82F6' : '#e5e7eb'}`,
                      borderRadius: '8px',
                      backgroundColor: vehicleType === option.value ? '#eff6ff' : 'white',
                      color: vehicleType === option.value ? '#3B82F6' : '#6b7280',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      transition: 'all 0.2s'
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Route Preferences */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#374151' }}>
                ⚙️ Route Preference:
              </label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[
                  { value: 'fastest', label: '⚡ Fastest', desc: 'Minimize travel time' },
                  { value: 'cleanest', label: '🌱 Cleanest', desc: 'Low pollution exposure' },
                  { value: 'balanced', label: '⚖️ Balanced', desc: 'Time + air quality' }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setRoutePreference(option.value)}
                    style={{
                      padding: '8px 12px',
                      border: `2px solid ${routePreference === option.value ? '#3B82F6' : '#e5e7eb'}`,
                      borderRadius: '8px',
                      backgroundColor: routePreference === option.value ? '#eff6ff' : 'white',
                      color: routePreference === option.value ? '#3B82F6' : '#6b7280',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div>{option.label}</div>
                    <div style={{ fontSize: '12px', opacity: 0.8 }}>{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleRouteSearch}
              disabled={isLoading}
              style={{
                backgroundColor: isLoading ? '#9ca3af' : '#10B981',
                color: 'white',
                padding: '14px 24px',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                width: '100%',
                transition: 'background-color 0.2s'
              }}
            >
              {isLoading ? '🔍 Finding Routes...' : '🚀 Find Smart Routes'}
            </button>
          </div>
        )}

        {/* Route Results */}
        {showRoutes && routes.length > 0 && !isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '12px',
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
              🗺️ Route Options
            </h3>
            
            {routes.map((route, index) => (
              <div
                key={route.id}
                onClick={() => selectRoute(route)}
                style={{
                  border: `2px solid ${getRouteColor(route.aqi)}`,
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: index === 0 ? '#f0fdf4' : 'white'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <h4 style={{ margin: 0, color: '#1f2937', fontSize: '16px', fontWeight: '600' }}>
                      {route.name}
                      {index === 0 && <span style={{ 
                        marginLeft: '8px', 
                        backgroundColor: '#10B981', 
                        color: 'white', 
                        padding: '2px 8px', 
                        borderRadius: '12px', 
                        fontSize: '12px' 
                      }}>
                        RECOMMENDED
                      </span>}
                    </h4>
                    <p style={{ margin: '4px 0 0 0', color: '#6b7280', fontSize: '14px' }}>
                      {route.distance} km • {route.type} route
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '18px', fontWeight: '700', color: '#1f2937' }}>
                      {route.time} min
                    </div>
                  </div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>Air Quality:</span>
                    <span style={{ 
                      backgroundColor: getRouteColor(route.aqi), 
                      color: 'white', 
                      padding: '4px 8px', 
                      borderRadius: '6px', 
                      fontSize: '12px', 
                      fontWeight: '600' 
                    }}>
                      AQI {route.aqi} • {getAQICategory(route.aqi)}
                    </span>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent triggering the parent click handler
                      startNavigation(route);
                    }}
                    style={{
                      backgroundColor: '#3B82F6',
                      color: 'white',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    SELECT
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Traffic Light Advisories */}
        {selectedRouteId && trafficLights.length > 0 && !isNavigating && (
          <div style={{ 
            backgroundColor: '#eff6ff', 
            padding: '16px', 
            borderRadius: '12px',
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h4 style={{ margin: 0, color: '#1f2937' }}>
                🚦 Traffic Light Advisories
              </h4>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                Updated in real-time
              </span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              {trafficLights
                .filter(light => light.current_state.time_remaining > 0 && light.current_state.time_remaining <= 30)
                .map((light, index) => (
                  <div key={index} style={{
                    backgroundColor: 'white',
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    minWidth: '200px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: '600', color: '#1f2937' }}>{light.intersection_name}</span>
                      <span style={{
                        backgroundColor: light.current_state.color === 'red' ? '#ef4444' : 
                                       light.current_state.color === 'yellow' ? '#f59e0b' : '#10b981',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px'
                      }}>
                        {light.current_state.color.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>
                      <span>⏱️ {light.current_state.time_remaining}s remaining</span>
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#3b82f6', fontStyle: 'italic', fontWeight: '600' }}>
                      {light.current_state.color === 'red' && light.current_state.time_remaining <= 10 && '⚠️ Prepare to stop'}
                      {light.current_state.color === 'green' && light.current_state.time_remaining <= 15 && '✅ Maintain current speed'}
                      {light.current_state.color === 'yellow' && '⚠️ Prepare to stop'}
                      {light.current_state.color === 'red' && light.current_state.time_remaining > 10 && '⏱️ Wait for green'}
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Floating Traffic Light Advisory (during navigation) */}
        {isNavigating && nextSignal && (
          <div style={{
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: nextSignal.current_state.color === 'red' ? '#ef4444' : 
                           nextSignal.current_state.color === 'yellow' ? '#f59e0b' : '#10b981',
            color: 'white',
            padding: '16px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: 1000,
            maxWidth: '90%',
            textAlign: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>
                {nextSignal.current_state.color === 'red' ? '🔴' : 
                 nextSignal.current_state.color === 'yellow' ? '🟡' : '🟢'}
              </span>
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                  Next Signal: {nextSignal.intersection_name || nextSignal.signal_id}
                </div>
                <div style={{ fontSize: '14px' }}>
                  {Math.round(nextSignal.distance * 1000)}m ahead • 
                  {nextSignal.current_state.time_remaining > 0 ? 
                    ` Changes in ${nextSignal.current_state.time_remaining}s` : 
                    ` Just changed to ${nextSignal.current_state.color}`}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Map Display */}
        {selectedRouteId && (
          <div 
            id="navigation-map"
            style={{ 
              backgroundColor: 'white', 
              padding: '20px', 
              borderRadius: '12px',
              marginBottom: '16px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              height: isNavigating ? '80vh' : 'auto'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: '#1f2937' }}>
                {isNavigating ? '🧭 Navigation' : '🗺️ Route Preview'}
              </h3>
              <div>
                {isNavigating && (
                  <button 
                    onClick={() => setIsNavigating(false)}
                    style={{
                      backgroundColor: '#EF4444',
                      color: 'white',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '600',
                  cursor: 'pointer',
                      marginRight: '8px'
                    }}
                  >
                    Exit Navigation
                  </button>
                )}
                <button 
                  onClick={toggleFullScreen}
                  style={{
                    backgroundColor: '#3B82F6',
                    color: 'white',
                    border: 'none',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  {document.fullscreenElement ? 'Exit Full Screen' : 'Full Screen'}
                </button>
              </div>
            </div>
            {console.log('Passing to MapComponent - fromCoords:', selectedFromCoords, 'toCoords:', selectedToCoords)}
            <MapComponent 
              fromCoords={selectedFromCoords}
              toCoords={selectedToCoords}
              selectedRoute={routes.find(r => r.id === selectedRouteId) || null}
              trafficLights={trafficLights}
              isFullScreen={!!document.fullscreenElement}
              isNavigating={isNavigating}
            />
          </div>
        )}

        {/* Features Section */}
        {!isNavigating && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>✨ Smart Features</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              {[
                { icon: '🚦', title: 'Green Wave Sync', desc: 'Coordinated traffic signals' },
                { icon: '🌱', title: 'Clean Air Routes', desc: 'Minimize pollution exposure' },
                { icon: '📱', title: 'Smart Alerts', desc: 'Real-time notifications' },
                { icon: '🚨', title: 'Emergency Alerts', desc: 'Instant rerouting' },
                { icon: '📊', title: 'Impact Tracking', desc: 'Environmental benefits' },
                { icon: '🎯', title: 'Predictive AI', desc: 'Traffic & incident prediction' }
              ].map((feature, index) => (
                <div key={index} style={{
                  padding: '12px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '24px', marginBottom: '4px' }}>{feature.icon}</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '2px' }}>
                    {feature.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    {feature.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bottom navigation */}
        {!isNavigating && (
          <nav style={{ 
            backgroundColor: 'white', 
            borderTop: '1px solid #e5e7eb', 
            padding: '12px 16px',
            boxShadow: '0 -2px 8px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
              <button
                onClick={() => handleNavigation('/')}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  background: 'none',
                  border: 'none',
                  color: '#3B82F6',
                  cursor: 'pointer',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontWeight: '600'
                }}
              >
                <span style={{ fontSize: '20px', marginBottom: '2px' }}>🧭</span>
                <span style={{ fontSize: '12px' }}>Navigate</span>
              </button>
              <button
                onClick={() => handleNavigation('/dashboard')}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  background: 'none',
                  border: 'none',
                  color: '#6B7280',
                  cursor: 'pointer',
                  padding: '8px 12px',
                  borderRadius: '8px'
                }}
              >
                <span style={{ fontSize: '20px', marginBottom: '2px' }}>📊</span>
                <span style={{ fontSize: '12px' }}>Dashboard</span>
              </button>
              <button
                onClick={() => handleNavigation('/settings')}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  background: 'none',
                  border: 'none',
                  color: '#6B7280',
                  cursor: 'pointer',
                  padding: '8px 12px',
                  borderRadius: '8px'
                }}
              >
                <span style={{ fontSize: '20px', marginBottom: '2px' }}>⚙️</span>
                <span style={{ fontSize: '12px' }}>Settings</span>
              </button>
            </div>
          </nav>
        )}
      </main>

    </div>
  );
};

export default NavigationView;