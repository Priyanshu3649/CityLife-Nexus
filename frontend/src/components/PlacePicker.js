import React, { useState } from 'react';

const PlacePicker = ({ onPlaceSelect, placeholder = "Search for a place" }) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Handle input change
  const handleInputChange = async (e) => {
    const value = e.target.value;
    setInputValue(value);
    
    if (value.length >= 2) {
      try {

        const response = await fetch(
          `http://localhost:8001/api/v1/routes/location/autocomplete?input_text=${encodeURIComponent(value)}&bias_to_ncr=true`
        );
        
        if (response.ok) {
          const data = await response.json();

          
          if (data.predictions && data.predictions.length > 0) {
            setSuggestions(data.predictions);
            setShowSuggestions(true);

            return;
          }
        } else {
          console.warn('API response not OK:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('Error fetching real place suggestions:', error);
      }
      
      // Fallback to mock data if API fails
      const mockPlaces = [
        { 
          description: "Connaught Place, New Delhi", 
          place_id: "cp_delhi",
          coordinates: { latitude: 28.6315, longitude: 77.2167 }
        },
        { 
          description: "India Gate, New Delhi", 
          place_id: "india_gate",
          coordinates: { latitude: 28.6129, longitude: 77.2295 }
        },
        { 
          description: "Red Fort, Delhi", 
          place_id: "red_fort",
          coordinates: { latitude: 28.6562, longitude: 77.2410 }
        },
        { 
          description: "Gurgaon City Center, Haryana", 
          place_id: "gurgaon_center",
          coordinates: { latitude: 28.4595, longitude: 77.0266 }
        },
        { 
          description: "Cyber City, Gurgaon", 
          place_id: "cyber_city",
          coordinates: { latitude: 28.4950, longitude: 77.0890 }
        },
        { 
          description: "Sector 18, Noida", 
          place_id: "sector_18",
          coordinates: { latitude: 28.5678, longitude: 77.3261 }
        }
      ];
      
      // Filter mock places based on input
      const filtered = mockPlaces.filter(place => 
        place.description.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Handle place selection
  const handlePlaceSelect = async (suggestion) => {
    setInputValue(suggestion.description);
    setSuggestions([]);
    setShowSuggestions(false);
    
    // For real Google Places API responses, get coordinates from place details
    if (suggestion.place_id && !suggestion.place_id.startsWith('fallback_')) {
      try {

        const response = await fetch(
          `http://localhost:8001/api/v1/routes/location/details/${encodeURIComponent(suggestion.place_id)}`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.coordinates && data.coordinates.latitude !== undefined) {
            const placeWithCoordinates = {
              ...suggestion,
              coordinates: {
                latitude: data.coordinates.latitude,
                longitude: data.coordinates.longitude
              }
            };
            
            // Notify parent component
            if (onPlaceSelect) {
              onPlaceSelect(placeWithCoordinates);
            }
            return;
          }
        }
      } catch (error) {
        console.error('Error getting place details:', error);
      }
    }
    
    // Fallback to mock coordinates
    const mockCoordinates = {
      "Connaught Place, New Delhi": { latitude: 28.6315, longitude: 77.2167 },
      "India Gate, New Delhi": { latitude: 28.6129, longitude: 77.2295 },
      "Red Fort, Delhi": { latitude: 28.6562, longitude: 77.2410 },
      "Gurgaon City Center, Haryana": { latitude: 28.4595, longitude: 77.0266 },
      "Cyber City, Gurgaon": { latitude: 28.4950, longitude: 77.0890 },
      "Sector 18, Noida": { latitude: 28.5678, longitude: 77.3261 }
    };
    
    const coordinates = mockCoordinates[suggestion.description] || 
      { latitude: 28.6139, longitude: 77.2090 }; // Default to Delhi center
    
    const placeWithCoordinates = {
      ...suggestion,
      coordinates: coordinates
    };
    
    // Notify parent component
    if (onPlaceSelect) {
      onPlaceSelect(placeWithCoordinates);
    }
  };

  // Handle input blur (close suggestions after a delay)
  const handleInputBlur = () => {
    // Small delay to allow click on suggestions
    setTimeout(() => {
      setShowSuggestions(false);
    }, 150);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleInputBlur}
        onFocus={() => inputValue.length >= 2 && setShowSuggestions(true)}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          fontSize: '14px',
          boxSizing: 'border-box'
        }}
      />
      
      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ccc',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          zIndex: 1000,
          maxHeight: '200px',
          overflowY: 'auto',
          marginTop: '2px'
        }}>
          {suggestions.map((place, index) => (
            <div
              key={place.place_id || index}
              onClick={() => handlePlaceSelect(place)}
              style={{
                padding: '10px',
                cursor: 'pointer',
                borderBottom: index < suggestions.length - 1 ? '1px solid #eee' : 'none'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {place.main_text || place.description}
              {place.secondary_text && (
                <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                  {place.secondary_text}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlacePicker;