import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const NavigationView = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [routePreference, setRoutePreference] = useState('balanced');
  const [showRoutes, setShowRoutes] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
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
      if (fromInputRef.current && !fromInputRef.current.contains(event.target)) {
        setShowFromSuggestions(false);
      }
      if (toInputRef.current && !toInputRef.current.contains(event.target)) {
        setShowToSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleNavigation = (path) => {
    navigate(path);
  };

  // Google Places Autocomplete
  const searchPlaces = async (query, setSuggestions) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8002/api/v1/maps/autocomplete?query=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.predictions || []);
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
    
    // Get coordinates for the selected place
    try {
      const response = await fetch(`http://127.0.0.1:8002/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedFromCoords(data.coordinates);
      }
    } catch (error) {
      console.error('Error geocoding from location:', error);
    }
  };

  const selectToLocation = async (suggestion) => {
    setToLocation(suggestion.description);
    setShowToSuggestions(false);
    setToSuggestions([]);
    
    // Get coordinates for the selected place
    try {
      const response = await fetch(`http://127.0.0.1:8002/api/v1/maps/geocode?address=${encodeURIComponent(suggestion.description)}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedToCoords(data.coordinates);
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

    try {
      // Call backend API to get real routes with AQI data
      const response = await fetch('http://127.0.0.1:8002/api/v1/maps/routes-with-aqi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_coords: selectedFromCoords,
          end_coords: selectedToCoords,
          preferences: {
            prioritize_time: routePreference === 'fastest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_air_quality: routePreference === 'cleanest' ? 0.8 : routePreference === 'balanced' ? 0.4 : 0.2,
            prioritize_safety: 0.2,
            max_detour_minutes: 10
          },
          vehicle_type: 'car'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRoutes(data.routes || []);
        setShowRoutes(true);
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
    // Open Google Maps navigation
    if (selectedFromCoords && selectedToCoords) {
      const googleMapsUrl = `https://www.google.com/maps/dir/${selectedFromCoords.latitude},${selectedFromCoords.longitude}/${selectedToCoords.latitude},${selectedToCoords.longitude}`;
      
      // Try to open in Google Maps app first, fallback to web
      const mapsAppUrl = `comgooglemaps://?saddr=${selectedFromCoords.latitude},${selectedFromCoords.longitude}&daddr=${selectedToCoords.latitude},${selectedToCoords.longitude}&directionsmode=driving`;
      
      // Check if on mobile device
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      if (isMobile) {
        // Try to open Google Maps app
        window.location.href = mapsAppUrl;
        // Fallback to web version after a short delay
        setTimeout(() => {
          window.open(googleMapsUrl, '_blank');
        }, 1000);
      } else {
        // Open in new tab for desktop
        window.open(googleMapsUrl, '_blank');
      }
      
      // Show confirmation
      alert(`🚀 Opening navigation for ${route.name}\n⏱️ ${route.time} min • 🌫️ AQI ${route.aqi}\n📍 Starting navigation in Google Maps...`);
    } else {
      alert('Please search for routes first to enable navigation');
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
                {fromSuggestions.map((suggestion, index) => (
                  <div
                    key={index}
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
                {toSuggestions.map((suggestion, index) => (
                  <div
                    key={index}
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

        {/* Route Results */}
        {showRoutes && routes.length > 0 && (
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
                  <button style={{
                    backgroundColor: '#3B82F6',
                    color: 'white',
                    border: 'none',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}>
                    SELECT
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Features Section */}
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
      </main>

      {/* Bottom navigation */}
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
    </div>
  );
};

export default NavigationView;