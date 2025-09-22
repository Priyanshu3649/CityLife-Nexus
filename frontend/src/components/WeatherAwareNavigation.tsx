import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface WeatherData {
  temperature_celsius: number;
  humidity_percent: number;
  wind_speed_kmh: number;
  precipitation_mm: number;
  weather_condition: string;
  weather_description: string;
  visibility_km: number;
  reading_time: string;
}

interface WeatherImpact {
  overall_impact: 'low' | 'medium' | 'high';
  speed_factor: number;
  safety_factor: number;
  visibility_factor: number;
  recommendations: string[];
}

interface RouteWeatherData {
  origin_weather: WeatherData | null;
  destination_weather: WeatherData | null;
  route_impact: WeatherImpact;
  recommendations: string[];
}

const WeatherAwareNavigation: React.FC = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [weatherData, setWeatherData] = useState<RouteWeatherData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showWeatherInfo, setShowWeatherInfo] = useState(false);

  const getWeatherRouteImpact = async () => {
    if (!fromLocation || !toLocation) {
      alert('Please enter both starting location and destination');
      return;
    }

    setIsLoading(true);
    setShowWeatherInfo(false);

    try {
      // Mock coordinates - in real app, would geocode addresses
      const mockCoordinates = {
        from: { latitude: 28.6139, longitude: 77.2090 }, // Delhi
        to: { latitude: 19.0760, longitude: 72.8777 } // Mumbai
      };

      const response = await fetch(`http://localhost:8000/api/v1/routes/weather/route-impact?latitude=${mockCoordinates.from.latitude}&longitude=${mockCoordinates.from.longitude}&departure_time=${new Date().toISOString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        setWeatherData(data);
        setShowWeatherInfo(true);
      } else {
        throw new Error('Failed to fetch weather data');
      }
    } catch (error) {
      console.error('Error fetching weather data:', error);
      // Mock data for demo
      setWeatherData({
        origin_weather: {
          temperature_celsius: 32,
          humidity_percent: 65,
          wind_speed_kmh: 12,
          precipitation_mm: 0,
          weather_condition: 'clear',
          weather_description: 'clear sky',
          visibility_km: 10,
          reading_time: new Date().toISOString()
        },
        destination_weather: {
          temperature_celsius: 29,
          humidity_percent: 78,
          wind_speed_kmh: 15,
          precipitation_mm: 2.5,
          weather_condition: 'rain',
          weather_description: 'light rain',
          visibility_km: 6,
          reading_time: new Date().toISOString()
        },
        route_impact: {
          overall_impact: 'medium',
          speed_factor: 0.8,
          safety_factor: 0.7,
          visibility_factor: 0.6,
          recommendations: [
            'Light rain at destination. Drive carefully and reduce speed.',
            'Consider using covered parking at destination.',
            'Visibility may be reduced - use headlights.'
          ]
        },
        recommendations: [
          'Light rain at destination. Drive carefully and reduce speed.',
          'Consider using covered parking at destination.',
          'Visibility may be reduced - use headlights.'
        ]
      });
      setShowWeatherInfo(true);
    } finally {
      setIsLoading(false);
    }
  };

  const getWeatherIcon = (condition: string) => {
    switch (condition.toLowerCase()) {
      case 'clear': return '☀️';
      case 'clouds': return '☁️';
      case 'rain': return '🌧️';
      case 'thunderstorm': return '⛈️';
      case 'snow': return '❄️';
      case 'mist':
      case 'fog': return '🌫️';
      default: return '🌤️';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'low': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'high': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getImpactLabel = (impact: string) => {
    switch (impact) {
      case 'low': return 'Minimal Weather Impact';
      case 'medium': return 'Moderate Weather Impact';
      case 'high': return 'Significant Weather Impact';
      default: return 'Unknown Impact';
    }
  };

  const formatTemperature = (temp: number) => `${Math.round(temp)}°C`;

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      {/* Header */}
      <header style={{ 
        backgroundColor: '#0ea5e9', 
        color: 'white', 
        padding: '16px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)' 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'none',
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'white',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ← Back
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
              🌤️ Weather-Aware Navigation
            </h1>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', opacity: 0.9 }}>
              Smart routing based on weather conditions
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        
        {/* Search Section */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '12px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
            🔍 Check Weather Impact on Your Route
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#374151' }}>
                📍 From:
              </label>
              <input
                type="text"
                value={fromLocation}
                onChange={(e) => setFromLocation(e.target.value)}
                placeholder="Enter starting location"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#374151' }}>
                🎯 To:
              </label>
              <input
                type="text"
                value={toLocation}
                onChange={(e) => setToLocation(e.target.value)}
                placeholder="Enter destination"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '16px'
                }}
              />
            </div>
          </div>

          <button
            onClick={getWeatherRouteImpact}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isLoading ? '#9ca3af' : '#0ea5e9',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? '🔄 Checking Weather...' : '🌤️ Analyze Weather Impact'}
          </button>
        </div>

        {/* Weather Results */}
        {showWeatherInfo && weatherData && (
          <>
            {/* Overall Impact Summary */}
            <div style={{ 
              backgroundColor: 'white', 
              padding: '20px', 
              borderRadius: '12px',
              marginBottom: '20px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: `3px solid ${getImpactColor(weatherData.route_impact.overall_impact)}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{
                  backgroundColor: getImpactColor(weatherData.route_impact.overall_impact),
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '20px',
                  fontSize: '14px',
                  fontWeight: '600'
                }}>
                  {getImpactLabel(weatherData.route_impact.overall_impact)}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '4px' }}>⚡</div>
                  <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                    {Math.round(weatherData.route_impact.speed_factor * 100)}%
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>Speed Factor</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '4px' }}>🛡️</div>
                  <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                    {Math.round(weatherData.route_impact.safety_factor * 100)}%
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>Safety Factor</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '4px' }}>👁️</div>
                  <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                    {Math.round(weatherData.route_impact.visibility_factor * 100)}%
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>Visibility</div>
                </div>
              </div>

              {/* Weather Recommendations */}
              {weatherData.recommendations.length > 0 && (
                <div style={{ 
                  backgroundColor: '#fef3c7', 
                  border: '1px solid #f59e0b',
                  borderRadius: '8px', 
                  padding: '12px' 
                }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>
                    ⚠️ Weather Recommendations:
                  </div>
                  {weatherData.recommendations.map((rec, index) => (
                    <div key={index} style={{ fontSize: '13px', color: '#92400e', marginBottom: '4px' }}>
                      • {rec}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Origin and Destination Weather */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              {/* Origin Weather */}
              {weatherData.origin_weather && (
                <div style={{ 
                  backgroundColor: 'white', 
                  padding: '20px', 
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  <h4 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
                    📍 Origin Weather
                  </h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ fontSize: '36px' }}>
                      {getWeatherIcon(weatherData.origin_weather.weather_condition)}
                    </div>
                    <div>
                      <div style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>
                        {formatTemperature(weatherData.origin_weather.temperature_celsius)}
                      </div>
                      <div style={{ fontSize: '14px', color: '#6b7280', textTransform: 'capitalize' }}>
                        {weatherData.origin_weather.weather_description}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
                    <div>
                      <span style={{ color: '#6b7280' }}>Humidity:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.origin_weather.humidity_percent}%
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Wind:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {Math.round(weatherData.origin_weather.wind_speed_kmh)} km/h
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Visibility:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.origin_weather.visibility_km} km
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Rain:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.origin_weather.precipitation_mm} mm
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Destination Weather */}
              {weatherData.destination_weather && (
                <div style={{ 
                  backgroundColor: 'white', 
                  padding: '20px', 
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  <h4 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
                    🎯 Destination Weather
                  </h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ fontSize: '36px' }}>
                      {getWeatherIcon(weatherData.destination_weather.weather_condition)}
                    </div>
                    <div>
                      <div style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>
                        {formatTemperature(weatherData.destination_weather.temperature_celsius)}
                      </div>
                      <div style={{ fontSize: '14px', color: '#6b7280', textTransform: 'capitalize' }}>
                        {weatherData.destination_weather.weather_description}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
                    <div>
                      <span style={{ color: '#6b7280' }}>Humidity:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.destination_weather.humidity_percent}%
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Wind:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {Math.round(weatherData.destination_weather.wind_speed_kmh)} km/h
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Visibility:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.destination_weather.visibility_km} km
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#6b7280' }}>Rain:</span>
                      <span style={{ marginLeft: '4px', fontWeight: '600' }}>
                        {weatherData.destination_weather.precipitation_mm} mm
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Weather Features Info */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
            🌦️ Weather-Aware Features
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {[
              { icon: '🌧️', title: 'Rain Detection', desc: 'Automatic rain impact analysis' },
              { icon: '🌫️', title: 'Visibility Tracking', desc: 'Fog and mist condition alerts' },
              { icon: '🌡️', title: 'Temperature Analysis', desc: 'Extreme temperature warnings' },
              { icon: '💨', title: 'Wind Assessment', desc: 'High wind speed notifications' },
              { icon: '⚡', title: 'Speed Adjustment', desc: 'Weather-based speed recommendations' },
              { icon: '🛡️', title: 'Safety Alerts', desc: 'Hazardous weather warnings' }
            ].map((feature, index) => (
              <div key={index} style={{ textAlign: 'center', padding: '16px' }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>{feature.icon}</div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
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
    </div>
  );
};

export default WeatherAwareNavigation;