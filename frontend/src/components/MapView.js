import React, { useState, useCallback, useEffect } from 'react';
import { GoogleMap, LoadScript, Marker, DirectionsService, DirectionsRenderer } from "@react-google-maps/api";

// Define libraries as a constant to fix performance warning
const LIBRARIES = ['places', 'directions'];

const MapView = ({ 
  center = { lat: 28.6139, lng: 77.2090 }, 
  zoom = 12, 
  fromCoords = null, 
  toCoords = null,
  route = null
}) => {
  const googleMapsApiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
  
  // Map container style
  const containerStyle = {
    height: "400px",
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
  const directionsCallback = React.useCallback((response) => {
    if (response !== null) {
      // Handle directions response if needed
      
    }
  }, []);

  return (
    <LoadScript 
      googleMapsApiKey={googleMapsApiKey} 
      libraries={LIBRARIES} // Use constant to fix performance warning
    >
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={zoom}
        options={mapOptions}
      >
        {/* Markers for start and end points */}
        {fromCoords && (
          <Marker 
            position={{ lat: fromCoords.latitude, lng: fromCoords.longitude }} 
            label="A"
          />
        )}
        
        {toCoords && (
          <Marker 
            position={{ lat: toCoords.latitude, lng: toCoords.longitude }} 
            label="B"
          />
        )}
        
        {/* Directions */}
        {fromCoords && toCoords && (
          <DirectionsService
            options={{
              destination: { lat: toCoords.latitude, lng: toCoords.longitude },
              origin: { lat: fromCoords.latitude, lng: fromCoords.longitude },
              travelMode: "DRIVING"
            }}
            callback={directionsCallback}
          />
        )}
        
        {route && (
          <DirectionsRenderer
            options={{
              directions: route
            }}
          />
        )}
      </GoogleMap>
    </LoadScript>
  );
};

export default MapView;