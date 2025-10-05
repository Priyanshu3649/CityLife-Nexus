import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Settings = () => {
  const navigate = useNavigate();
  const [voiceAlerts, setVoiceAlerts] = useState(true);
  const [routePriority, setRoutePriority] = useState('balanced');
  const [maxDetour, setMaxDetour] = useState(10);
  const [pollutionSensitivity, setPollutionSensitivity] = useState('normal');
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [voicesLoaded, setVoicesLoaded] = useState(false);

  // Load available voices when component mounts
  useEffect(() => {
    const loadVoices = () => {
      if ('speechSynthesis' in window) {
        const voices = window.speechSynthesis.getVoices();
        console.log('Loading voices. Found:', voices.length, 'voices');
        console.log('Voice details:', voices.map(v => ({ name: v.name, lang: v.lang, default: v.default })));
        setAvailableVoices(voices);
        setVoicesLoaded(true);
        
        // Set default voice (preferably a high-quality English voice)
        const savedVoice = localStorage.getItem('selectedVoice');
        console.log('Saved voice in localStorage:', savedVoice);
        if (savedVoice) {
          const savedVoiceObj = voices.find(voice => voice.name === savedVoice);
          if (savedVoiceObj) {
            console.log('Found saved voice:', savedVoiceObj.name);
            setSelectedVoice(savedVoiceObj.name);
            return;
          } else {
            console.log('Saved voice not found in available voices');
          }
        }
        
        // Set default voice (preferably a high-quality English voice)
        const defaultVoice = voices.find(voice => 
          voice.lang.includes('en') && (voice.name.includes('Google') || voice.name.includes('Microsoft') || voice.default)
        ) || voices.find(voice => voice.default) || voices[0];
        
        if (defaultVoice) {
          console.log('Setting default voice:', defaultVoice.name);
          setSelectedVoice(defaultVoice.name);
        }
      } else {
        console.log('Speech synthesis not supported in this browser');
      }
    };
    
    // Load voices immediately if they're already available
    console.log('Checking if voices are already available...');
    if (window.speechSynthesis && window.speechSynthesis.getVoices().length > 0) {
      console.log('Voices already available, loading immediately');
      loadVoices();
    } else {
      console.log('No voices available yet, waiting for voiceschanged event');
      // Wait for voices to be loaded
      window.speechSynthesis.onvoiceschanged = loadVoices;
      // Also try after a small delay as a fallback
      setTimeout(loadVoices, 1000);
    }
    
    // Cleanup
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const handleSave = () => {
    // Save voice preference to localStorage
    if (selectedVoice) {
      localStorage.setItem('selectedVoice', selectedVoice);
    }
    alert('Settings saved successfully! 🎉');
  };

  const handleReset = () => {
    setVoiceAlerts(true);
    setRoutePriority('balanced');
    setMaxDetour(10);
    setPollutionSensitivity('normal');
    setNotifications(true);
    setDarkMode(false);
    
    // Reset voice to default
    const defaultVoice = availableVoices.find(voice => 
      voice.lang.includes('en') && (voice.name.includes('Google') || voice.name.includes('Microsoft') || voice.default)
    ) || availableVoices.find(voice => voice.default) || availableVoices[0];
    
    if (defaultVoice) {
      setSelectedVoice(defaultVoice.name);
    }
    
    alert('Settings reset to defaults');
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <header style={{ 
        backgroundColor: 'white', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '20px'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'none',
              border: 'none',
              color: '#3B82F6',
              cursor: 'pointer',
              marginBottom: '10px',
              fontSize: '14px',
              fontWeight: '500'
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
            ⚙️ Settings
          </h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
            Customize your CityLife Nexus experience
          </p>
        </div>
      </header>
      
      <main style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
        {/* Navigation Preferences */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px'
        }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600',
            color: '#1f2937',
            marginTop: 0,
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🧭 Navigation Preferences
          </h3>
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              cursor: 'pointer',
              marginBottom: '16px'
            }}>
              <input
                type="checkbox"
                checked={voiceAlerts}
                onChange={(e) => setVoiceAlerts(e.target.checked)}
                style={{ marginRight: '12px', transform: 'scale(1.2)' }}
              />
              <div>
                <div style={{ fontWeight: '500', color: '#1f2937' }}>🔊 Voice Navigation Alerts</div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>Get spoken directions and traffic updates</div>
              </div>
            </label>
          </div>
          
          {/* Voice Selection */}
          {voiceAlerts && (
            <div style={{ marginBottom: '24px' }}>
              <label style={{ 
                display: 'block', 
                fontSize: '14px', 
                fontWeight: '500',
                color: '#374151',
                marginBottom: '8px'
              }}>
                🎤 Voice Selection
              </label>
              {!voicesLoaded ? (
                <div style={{ 
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  backgroundColor: '#f9fafb',
                  textAlign: 'center',
                  color: '#6b7280'
                }}>
                  Loading voices...
                </div>
              ) : availableVoices.length > 0 ? (
                <>
                  <select 
                    value={selectedVoice || ''}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '8px',
                      fontSize: '16px',
                      backgroundColor: 'white',
                      cursor: 'pointer',
                      marginBottom: '8px'
                    }}
                  >
                    {availableVoices
                      .filter(voice => voice.lang.includes('en') || voice.lang.includes('hi')) // Filter for English and Hindi voices
                      .map((voice) => (
                        <option key={voice.name} value={voice.name}>
                          {voice.name} ({voice.lang}) {voice.default ? '(Default)' : ''}
                        </option>
                      ))}
                  </select>
                  <div style={{ 
                    display: 'flex',
                    gap: '8px',
                    marginBottom: '4px'
                  }}>
                    <button
                      onClick={() => {
                        console.log('Preview voice button clicked');
                        if (selectedVoice && 'speechSynthesis' in window) {
                          console.log('Selected voice:', selectedVoice);
                          // Determine language based on selected voice
                          let lang = 'en-US';
                          if (selectedVoice.includes('Hindi') || selectedVoice.includes('hi') || selectedVoice.includes('हिन्दी')) {
                            lang = 'hi-IN';
                            console.log('Detected Hindi voice, using language:', lang);
                          } else {
                            console.log('Using English language:', lang);
                          }
                          
                          const speech = new SpeechSynthesisUtterance('This is a preview of your selected voice.');
                          speech.lang = lang;
                          speech.volume = 1;
                          speech.rate = 1;
                          speech.pitch = 1;
                          
                          const voices = window.speechSynthesis.getVoices();
                          console.log('Available voices for preview:', voices.map(v => v.name + ' (' + v.lang + ')'));
                          const voice = voices.find(v => v.name === selectedVoice);
                          if (voice) {
                            speech.voice = voice;
                            console.log('Setting voice for preview:', voice.name, voice.lang);
                          } else {
                            console.log('Voice not found for preview:', selectedVoice);
                          }
                          
                          // Add event listeners for debugging
                          speech.onstart = function(event) {
                            console.log('Preview speech started');
                          };
                          
                          speech.onend = function(event) {
                            console.log('Preview speech ended');
                          };
                          
                          speech.onerror = function(event) {
                            console.error('Preview speech error:', event.error);
                          };
                          
                          window.speechSynthesis.speak(speech);
                          console.log('Preview speech synthesis command sent');
                        } else {
                          console.log('Cannot preview voice: either no voice selected or speech synthesis not supported');
                        }
                      }}
                      style={{
                        backgroundColor: '#3B82F6',
                        color: 'white',
                        padding: '8px 12px',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        flex: '1'
                      }}
                    >
                      🔊 Preview Voice
                    </button>
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#6b7280'
                  }}>
                    Select your preferred voice for navigation alerts (supports English and Hindi)
                  </div>
                </>
              ) : (
                <div style={{ 
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  backgroundColor: '#f9fafb',
                  textAlign: 'center',
                  color: '#6b7280'
                }}>
                  No voices available in your browser. Voice navigation may not work.
                </div>
              )}
            </div>
          )}
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              🎯 Default Route Priority
            </label>
            <select 
              value={routePriority}
              onChange={(e) => setRoutePriority(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '16px',
                backgroundColor: 'white',
                cursor: 'pointer'
              }}
            >
              <option value="fastest">⚡ Fastest Route - Minimize travel time</option>
              <option value="balanced">⚖️ Balanced - Time + air quality</option>
              <option value="cleanest">🌱 Cleanest Air - Minimize pollution exposure</option>
              <option value="safest">🛡️ Safest Route - Avoid high-risk areas</option>
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
              🕐 Maximum Detour Time: {maxDetour} minutes
            </label>
            <input
              type="range"
              min="0"
              max="30"
              value={maxDetour}
              onChange={(e) => setMaxDetour(parseInt(e.target.value))}
              style={{ 
                width: '100%', 
                height: '6px',
                borderRadius: '3px',
                background: '#e5e7eb',
                outline: 'none'
              }}
            />
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              fontSize: '12px',
              color: '#6b7280',
              marginTop: '4px'
            }}>
              <span>0 min (no detour)</span>
              <span>30 min (flexible)</span>
            </div>
          </div>
        </div>

        {/* Health Profile */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px'
        }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600',
            color: '#1f2937',
            marginTop: 0,
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🏥 Health Profile
          </h3>
          
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              🫁 Pollution Sensitivity
            </label>
            <select 
              value={pollutionSensitivity}
              onChange={(e) => setPollutionSensitivity(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '16px',
                backgroundColor: 'white',
                cursor: 'pointer'
              }}
            >
              <option value="low">🟢 Low - No known sensitivities</option>
              <option value="normal">🟡 Normal - Average sensitivity</option>
              <option value="high">🟠 High - Respiratory conditions</option>
              <option value="very_high">🔴 Very High - Severe conditions</option>
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              fontWeight: '500',
              color: '#374151',
              marginBottom: '12px'
            }}>
              🏃 Activity Level
            </label>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {[
                { value: 'low', label: '🚶 Low', desc: 'Mostly sedentary' },
                { value: 'moderate', label: '🚴 Moderate', desc: 'Regular activity' },
                { value: 'high', label: '🏃 High', desc: 'Very active' }
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => {/* Activity level would be handled here */}}
                  style={{
                    padding: '12px 16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '8px',
                    backgroundColor: 'white',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    transition: 'all 0.2s',
                    textAlign: 'center'
                  }}
                >
                  <div>{option.label}</div>
                  <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>{option.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* App Preferences */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px'
        }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600',
            color: '#1f2937',
            marginTop: 0,
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            📱 App Preferences
          </h3>
          
          <div style={{ marginBottom: '20px' }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              cursor: 'pointer',
              marginBottom: '16px'
            }}>
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                style={{ marginRight: '12px', transform: 'scale(1.2)' }}
              />
              <div>
                <div style={{ fontWeight: '500', color: '#1f2937' }}>🔔 Push Notifications</div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>Get alerts for traffic, air quality, and emergencies</div>
              </div>
            </label>

            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={darkMode}
                onChange={(e) => setDarkMode(e.target.checked)}
                style={{ marginRight: '12px', transform: 'scale(1.2)' }}
              />
              <div>
                <div style={{ fontWeight: '500', color: '#1f2937' }}>🌙 Dark Mode</div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>Use dark theme for better night visibility</div>
              </div>
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={handleSave}
            style={{
              backgroundColor: '#10B981',
              color: 'white',
              padding: '14px 24px',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              flex: 1,
              minWidth: '120px',
              transition: 'background-color 0.2s'
            }}
          >
            💾 Save Settings
          </button>
          <button
            onClick={handleReset}
            style={{
              backgroundColor: '#6b7280',
              color: 'white',
              padding: '14px 24px',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              flex: 1,
              minWidth: '120px',
              transition: 'background-color 0.2s'
            }}
          >
            🔄 Reset to Defaults
          </button>
        </div>
      </main>

      {/* Bottom Navigation */}
      <nav style={{ 
        backgroundColor: 'white', 
        borderTop: '1px solid #e5e7eb', 
        padding: '12px 16px',
        boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
        marginTop: '40px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', maxWidth: '400px', margin: '0 auto' }}>
          <button
            onClick={() => navigate('/')}
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
            <span style={{ fontSize: '20px', marginBottom: '2px' }}>🧭</span>
            <span style={{ fontSize: '12px' }}>Navigate</span>
          </button>
          <button
            onClick={() => navigate('/dashboard')}
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
            onClick={() => navigate('/settings')}
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
            <span style={{ fontSize: '20px', marginBottom: '2px' }}>⚙️</span>
            <span style={{ fontSize: '12px' }}>Settings</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default Settings;