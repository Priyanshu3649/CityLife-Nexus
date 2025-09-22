import React, { useState, useCallback, useEffect, useRef } from 'react';
import { GoogleMap, LoadScript, Marker, DirectionsService, DirectionsRenderer } from "@react-google-maps/api";

const MapComponent = ({ 
  center = { lat: 28.6139, lng: 77.2090 }, 
  zoom = 12, 
  fromCoords = null, 
  toCoords = null,
  route = null,
  selectedRoute = null,
  trafficLights = [],
  onPlaceSelect = null,
  isFullScreen = false,
  isNavigating = false
}) => {
  console.log('MapComponent props:', { fromCoords, toCoords, selectedRoute, trafficLights });
  const googleMapsApiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
  const [directions, setDirections] = useState(null);
  const [userPosition, setUserPosition] = useState(null); // Track user position during navigation
  const directionsRendererRef = useRef(null);
  const mapRef = useRef(null);
  
  // Map container style - dynamic height based on isFullScreen
  const containerStyle = {
    height: isFullScreen ? "100%" : "400px",
    width: "100%"
  };

  // Map options
  const mapOptions = {
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: true,
    zoomControl: true
  };

  // Directions callback
  const directionsCallback = useCallback((response) => {
    if (response !== null) {
      if (response.status === 'OK') {
        setDirections(response);
      } else {
        console.error('Directions request failed due to ' + response.status);
      }
    }
  }, []);

  // Reset directions when fromCoords or toCoords change
  useEffect(() => {
    setDirections(null);
  }, [fromCoords, toCoords, selectedRoute]);

  // Handle directions renderer load
  const onDirectionsRendererLoad = useCallback((renderer) => {
    directionsRendererRef.current = renderer;
  }, []);

  // Simulate user position updates during navigation
  useEffect(() => {
    if (!isNavigating || !fromCoords || !toCoords) return;
    
    // In a real app, this would come from GPS
    // For demo, we'll simulate movement from start to end
    const startPosition = { lat: fromCoords.latitude, lng: fromCoords.longitude };
    const endPosition = { lat: toCoords.latitude, lng: toCoords.longitude };
    
    // Simple linear interpolation for demo
    let progress = 0;
    const interval = setInterval(() => {
      progress += 0.01;
      if (progress <= 1) {
        const currentPosition = {
          lat: startPosition.lat + (endPosition.lat - startPosition.lat) * progress,
          lng: startPosition.lng + (endPosition.lng - startPosition.lng) * progress
        };
        setUserPosition(currentPosition);
      } else {
        clearInterval(interval);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isNavigating, fromCoords, toCoords]);

  const onLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  return (
    <LoadScript 
      googleMapsApiKey={googleMapsApiKey} 
      libraries={['places']}
      onError={(error) => console.error("Google Maps API load error:", error)}
      onLoad={() => console.log("Google Maps API loaded successfully")}
    >
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={zoom}
        options={mapOptions}
        onLoad={onLoad}
      >
        {/* User position marker during navigation */}
        {isNavigating && userPosition && (
          <Marker 
            position={userPosition} 
            icon={{
              path: window.google && window.google.maps && window.google.maps.SymbolPath ? 
                window.google.maps.SymbolPath.CIRCLE : 
                'M 0,0 m -10,0 a 10,10 0 1,0 20,0 a 10,10 0 1,0 -20,0',
              scale: 2,
              fillColor: '#4285F4',
              fillOpacity: 1,
              strokeColor: '#FFFFFF',
              strokeWeight: 3
            }}
          />
        )}
        
        {/* Markers for start and end points */}
        {console.log('Rendering markers - fromCoords:', fromCoords, 'toCoords:', toCoords)}
        {fromCoords && (
          <Marker 
            position={{ lat: fromCoords.lat, lng: fromCoords.lng }} 
            label="A"
            icon={{
              path: window.google && window.google.maps && window.google.maps.SymbolPath ? 
                window.google.maps.SymbolPath.CIRCLE : 
                'M 0,0 m -10,0 a 10,10 0 1,0 20,0 a 10,10 0 1,0 -20,0',
              scale: 1.5,
              fillColor: '#4285F4',
              fillOpacity: 1,
              strokeColor: '#FFFFFF',
              strokeWeight: 2
            }}
          />
        )}
        
        {toCoords && (
          <Marker 
            position={{ lat: toCoords.lat, lng: toCoords.lng }} 
            label="B"
            icon={{
              path: window.google && window.google.maps && window.google.maps.SymbolPath ? 
                window.google.maps.SymbolPath.CIRCLE : 
                'M 0,0 m -10,0 a 10,10 0 1,0 20,0 a 10,10 0 1,0 -20,0',
              scale: 1.5,
              fillColor: '#EA4335',
              fillOpacity: 1,
              strokeColor: '#FFFFFF',
              strokeWeight: 2
            }}
          />
        )}
        
        {/* Directions from Google Maps API - fallback when no selected route */}
        {fromCoords && toCoords && !selectedRoute && !directions && 
         window.google && window.google.maps && window.google.maps.DirectionsService && (
          <DirectionsService
            options={{
              destination: { lat: toCoords.lat, lng: toCoords.lng },
              origin: { lat: fromCoords.lat, lng: fromCoords.lng },
              travelMode: "DRIVING"
            }}
            callback={directionsCallback}
          />
        )}
        
        {/* Display directions from Google Maps API */}
        {directions && window.google && window.google.maps && window.google.maps.DirectionsRenderer && (
          <DirectionsRenderer
            options={{
              directions: directions,
              suppressMarkers: true,
              polylineOptions: {
                strokeColor: '#4285F4',
                strokeOpacity: 0.8,
                strokeWeight: 6
              }
            }}
            onLoad={onDirectionsRendererLoad}
          />
        )}
        
        {/* Display selected route from our API */}
        {selectedRoute && selectedRoute.route_data && selectedRoute.route_data.waypoints && selectedRoute.route_data.waypoints.length > 1 && !directions && 
         window.google && window.google.maps && window.google.maps.DirectionsService && (
          (() => {
            // Validate route data
            if (!selectedRoute.route_data.start_coords || !selectedRoute.route_data.end_coords) {
              return null;
            }
            
            const origin = {
              lat: selectedRoute.route_data.start_coords.lat,
              lng: selectedRoute.route_data.start_coords.lng
            };
            
            const destination = {
              lat: selectedRoute.route_data.end_coords.lat,
              lng: selectedRoute.route_data.end_coords.lng
            };
            
            // Process waypoints (excluding first and last if there are more than 2)
            let waypoints = [];
            if (selectedRoute.route_data.waypoints.length > 2) {
              waypoints = selectedRoute.route_data.waypoints.slice(1, -1).map(wp => ({
                location: { lat: wp.lat, lng: wp.lng },
                stopover: true
              }));
            }
            
            const directionsOptions = {
              destination: destination,
              origin: origin,
              travelMode: "DRIVING"
            };
            
            // Only add waypoints if there are any
            if (waypoints.length > 0) {
              directionsOptions.waypoints = waypoints;
            }
            
            return (
              <DirectionsService
                options={directionsOptions}
                callback={directionsCallback}
              />
            );
          })()
        )}
        
        {/* Display traffic lights */}
        {trafficLights && trafficLights.map((light, index) => {
          // Validate traffic light data
          if (!light || !light.coordinates) {
            return null;
          }
          
          const position = {
            lat: light.coordinates.lat || light.coordinates.latitude,
            lng: light.coordinates.lng || light.coordinates.longitude
          };
          
          // Validate position
          if (isNaN(position.lat) || isNaN(position.lng)) {
            return null;
          }
          
          // Get color - with fallback
          let fillColor = '#00FF00'; // Default to green
          let colorLabel = 'Green';
          if (light.current_state && light.current_state.color) {
            switch (light.current_state.color.toLowerCase()) {
              case 'red':
                fillColor = '#FF0000';
                colorLabel = 'Red';
                break;
              case 'yellow':
                fillColor = '#FFFF00';
                colorLabel = 'Yellow';
                break;
              default:
                fillColor = '#00FF00';
                colorLabel = 'Green';
            }
          }
          
          // Check if Google Maps API is loaded, otherwise use simple circle
          const circlePath = window.google && window.google.maps && window.google.maps.SymbolPath ? 
            window.google.maps.SymbolPath.CIRCLE : 
            'M 0,0 m -10,0 a 10,10 0 1,0 20,0 a 10,10 0 1,0 -20,0';
          
          return (
            <Marker
              key={index}
              position={position}
              icon={{
                path: circlePath,
                scale: 1.5,
                fillColor: fillColor,
                fillOpacity: 1,
                strokeColor: '#000000',
                strokeWeight: 2
              }}
              title={`${light.intersection_name || 'Traffic Light'}\n${colorLabel} (${light.current_state && light.current_state.time_remaining ? light.current_state.time_remaining : '0'}s remaining)`}
            />
          );
        })}
      </GoogleMap>
    </LoadScript>
  );
};

export default MapComponent;