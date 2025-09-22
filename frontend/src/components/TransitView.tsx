import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface TransitRoute {
  total_time_minutes: number;
  total_cost_inr: number;
  walking_distance_km: number;
  co2_savings_kg: number;
  route_description: string;
  transit_legs: Array<{
    route_name: string;
    transport_type: string;
    from_stop: { name: string };
    to_stop: { name: string };
    travel_time_minutes: number;
    cost_inr: number;
  }>;
}

interface SupportedCity {
  name: string;
  center: { latitude: number; longitude: number };
  population?: number;
  has_metro: boolean;
  has_brt: boolean;
  has_local_train?: boolean;
  metro_system?: string;
  bus_system?: string;
}

const TransitView: React.FC = () => {
  const navigate = useNavigate();
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [transitRoutes, setTransitRoutes] = useState<TransitRoute[]>([]);
  const [supportedCities, setSupportedCities] = useState<Record<string, SupportedCity>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showRoutes, setShowRoutes] = useState(false);
  const [selectedCity, setSelectedCity] = useState('');

  useEffect(() => {
    // Load supported cities on component mount
    loadSupportedCities();
  }, []);

  const loadSupportedCities = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/routes/transit/cities');
      if (response.ok) {
        const data = await response.json();
        setSupportedCities(data.supported_cities);
      }
    } catch (error) {
      console.error('Error loading supported cities:', error);
    }
  };

  const searchTransitRoutes = async () => {
    if (!fromLocation || !toLocation) {
      alert('Please enter both starting location and destination');
      return;
    }

    setIsLoading(true);
    setShowRoutes(false);

    try {
      // Mock coordinates - in real app, would geocode addresses
      const mockCoordinates = {
        from: { latitude: 28.6139, longitude: 77.2090 }, // Delhi
        to: { latitude: 28.5355, longitude: 77.3910 } // Noida
      };

      const response = await fetch('http://localhost:8000/api/v1/routes/transit/multimodal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origin: mockCoordinates.from,
          destination: mockCoordinates.to,
          departure_time: new Date().toISOString()
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTransitRoutes(data.routes || []);
        setShowRoutes(true);
      } else {
        throw new Error('No transit routes found');
      }
    } catch (error) {
      console.error('Error fetching transit routes:', error);
      // Show message about city support
      alert('Transit routes not available for these locations. Please check supported cities.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toFixed(0)}`;
  };

  const getTransportIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'metro': return '🚇';
      case 'bus': return '🚌';
      case 'train': return '🚊';
      case 'brt': return '🚌';
      default: return '🚌';
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      {/* Header */}
      <header style={{ 
        backgroundColor: '#059669', 
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
              🚇 Public Transit Navigator
            </h1>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', opacity: 0.9 }}>
              Multimodal transportation across India
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        
        {/* Supported Cities Info */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '12px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
            🏙️ Supported Cities ({Object.keys(supportedCities).length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
            {Object.entries(supportedCities).slice(0, 6).map(([code, city]) => (
              <div
                key={code}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '12px',
                  fontSize: '14px'
                }}
              >
                <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                  {city.name}
                </div>
                <div style={{ color: '#6b7280', fontSize: '12px' }}>
                  {city.metro_system && `🚇 ${city.metro_system}`}
                  {city.bus_system && <div>🚌 {city.bus_system}</div>}
                  {city.population && <div>👥 {(city.population / 1000000).toFixed(1)}M people</div>}
                </div>
              </div>
            ))}
          </div>
          {Object.keys(supportedCities).length > 6 && (
            <div style={{ textAlign: 'center', marginTop: '12px' }}>
              <span style={{ color: '#6b7280', fontSize: '14px' }}>
                +{Object.keys(supportedCities).length - 6} more cities...
              </span>
            </div>
          )}
        </div>

        {/* Search Section */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '12px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
            🔍 Plan Your Journey
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
            onClick={searchTransitRoutes}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isLoading ? '#9ca3af' : '#059669',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? '🔄 Finding Routes...' : '🚇 Find Transit Routes'}
          </button>
        </div>

        {/* Transit Routes Results */}
        {showRoutes && transitRoutes.length > 0 && (
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '12px',
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
              🚇 Transit Route Options
            </h3>
            
            {transitRoutes.map((route, index) => (
              <div
                key={index}
                style={{
                  border: '2px solid #10b981',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '12px',
                  backgroundColor: index === 0 ? '#ecfdf5' : 'white'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h4 style={{ margin: 0, color: '#1f2937', fontSize: '16px', fontWeight: '600' }}>
                      {route.route_description}
                      {index === 0 && <span style={{ 
                        marginLeft: '8px', 
                        backgroundColor: '#10b981', 
                        color: 'white', 
                        padding: '2px 8px', 
                        borderRadius: '4px', 
                        fontSize: '12px' 
                      }}>RECOMMENDED</span>}
                    </h4>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '18px', fontWeight: '600', color: '#059669' }}>
                      {formatTime(route.total_time_minutes)}
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>
                      {formatCurrency(route.total_cost_inr)}
                    </div>
                  </div>
                </div>

                {/* Transit Legs */}
                {route.transit_legs.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                      Journey Details:
                    </div>
                    {route.transit_legs.map((leg, legIndex) => (
                      <div key={legIndex} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px', 
                        marginBottom: '4px',
                        fontSize: '13px'
                      }}>
                        <span>{getTransportIcon(leg.transport_type)}</span>
                        <span style={{ color: '#1f2937' }}>
                          {leg.from_stop.name} → {leg.to_stop.name}
                        </span>
                        <span style={{ color: '#6b7280' }}>
                          ({formatTime(leg.travel_time_minutes)})
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Environmental Impact */}
                <div style={{ 
                  backgroundColor: '#f0fdf4', 
                  padding: '12px', 
                  borderRadius: '8px',
                  marginBottom: '12px'
                }}>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
                    <div>
                      <span style={{ color: '#059669', fontWeight: '600' }}>🚶</span>
                      <span style={{ color: '#6b7280', marginLeft: '4px' }}>
                        {route.walking_distance_km.toFixed(1)} km walking
                      </span>
                    </div>
                    <div>
                      <span style={{ color: '#059669', fontWeight: '600' }}>🌱</span>
                      <span style={{ color: '#6b7280', marginLeft: '4px' }}>
                        {route.co2_savings_kg.toFixed(1)} kg CO₂ saved
                      </span>
                    </div>
                  </div>
                </div>

                <button style={{
                  backgroundColor: '#059669',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  width: '100%'
                }}>
                  Select This Route
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Features Info */}
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#1f2937' }}>
            ✨ Transit Features
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {[
              { icon: '🚇', title: 'Metro Integration', desc: 'All major Indian metro systems' },
              { icon: '🚌', title: 'Bus Networks', desc: 'City bus and BRT systems' },
              { icon: '🚊', title: 'Local Trains', desc: 'Mumbai local & suburban trains' },
              { icon: '🌱', title: 'Eco-Friendly', desc: 'Reduce carbon footprint' },
              { icon: '💰', title: 'Cost Effective', desc: 'Affordable public transport' },
              { icon: '⏱️', title: 'Real-Time', desc: 'Live timing and delays' }
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

export default TransitView;