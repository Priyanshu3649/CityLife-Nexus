import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [voiceAlerts, setVoiceAlerts] = useState(true);
  const [routePriority, setRoutePriority] = useState('balanced');
  const [maxDetour, setMaxDetour] = useState(10);

  const handleSave = () => {
    alert('Settings saved successfully!');
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <header style={{ 
        backgroundColor: 'white', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '20px'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'none',
              border: 'none',
              color: '#3B82F6',
              cursor: 'pointer',
              marginBottom: '10px'
            }}
          >
            ← Back to Navigation
          </button>
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: 'bold', 
            color: '#1f2937',
            margin: 0
          }}>
            Settings
          </h1>
        </div>
      </header>
      
      <main style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600',
            color: '#1f2937',
            marginTop: 0,
            marginBottom: '20px'
          }}>
            User Preferences
          </h3>
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Voice Alerts
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={voiceAlerts}
                onChange={(e) => setVoiceAlerts(e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              Enable voice navigation alerts
            </label>
          </div>
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Route Priority
            </label>
            <select 
              value={routePriority}
              onChange={(e) => setRoutePriority(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              <option value="balanced">Balanced (Time + Air Quality)</option>
              <option value="fastest">Fastest Route</option>
              <option value="cleanest">Cleanest Air</option>
              <option value="safest">Safest Route</option>
            </select>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Maximum Detour (minutes): {maxDetour}
            </label>
            <input
              type="range"
              min="0"
              max="30"
              value={maxDetour}
              onChange={(e) => setMaxDetour(parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              fontSize: '12px',
              color: '#6b7280',
              marginTop: '4px'
            }}>
              <span>0 min</span>
              <span>30 min</span>
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ 
              fontSize: '16px', 
              fontWeight: '600',
              color: '#1f2937',
              marginBottom: '12px'
            }}>
              Health Profile
            </h4>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500',
                color: '#374151',
                marginBottom: '8px'
              }}>
                Pollution Sensitivity
              </label>
              <select style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }}>
                <option>Normal</option>
                <option>High (Respiratory conditions)</option>
                <option>Very High (Severe conditions)</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleSave}
            style={{
              backgroundColor: '#3B82F6',
              color: 'white',
              padding: '12px 24px',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              cursor: 'pointer',
              width: '100%'
            }}
          >
            Save Settings
          </button>
        </div>
      </main>
    </div>
  );
};

export default Settings;