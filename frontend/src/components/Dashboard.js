import React from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();

  const metrics = [
    { label: 'Time Saved', value: '45 minutes', color: '#10B981', icon: '⏰' },
    { label: 'CO2 Avoided', value: '2.3 kg', color: '#3B82F6', icon: '🌱' },
    { label: 'Clean Routes', value: '12 trips', color: '#8B5CF6', icon: '🛣️' },
    { label: 'Eco Score', value: '850 pts', color: '#F59E0B', icon: '🏆' }
  ];

  const recentActivity = [
    { action: 'Used clean route to downtown', benefit: 'saved 15 minutes', time: '2 hours ago' },
    { action: 'Avoided high pollution area on Main Street', benefit: 'reduced exposure by 40%', time: '5 hours ago' },
    { action: 'Synchronized with 3 traffic signals', benefit: 'smooth green wave', time: '1 day ago' },
    { action: 'Earned 50 eco points for choosing green route', benefit: 'level up!', time: '2 days ago' }
  ];

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
            📊 Impact Dashboard
          </h1>
          <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
            Track your environmental impact and savings
          </p>
        </div>
      </header>
      
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
        {/* Metrics Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '24px',
          marginBottom: '32px'
        }}>
          {metrics.map((metric, index) => (
            <div key={index} style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: `3px solid ${metric.color}20`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  backgroundColor: `${metric.color}20`,
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  marginRight: '16px'
                }}>
                  {metric.icon}
                </div>
                <div>
                  <div style={{ 
                    fontSize: '14px', 
                    color: '#6b7280',
                    marginBottom: '4px',
                    fontWeight: '500'
                  }}>
                    {metric.label}
                  </div>
                  <div style={{ 
                    fontSize: '24px', 
                    fontWeight: 'bold',
                    color: metric.color
                  }}>
                    {metric.value}
                  </div>
                </div>
              </div>
              <div style={{
                width: '100%',
                height: '4px',
                backgroundColor: '#f3f4f6',
                borderRadius: '2px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${60 + index * 10}%`,
                  height: '100%',
                  backgroundColor: metric.color,
                  borderRadius: '2px'
                }}></div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px'
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#1f2937' }}>
            🕒 Recent Activity
          </h2>
          <div style={{ space: '16px' }}>
            {recentActivity.map((activity, index) => (
              <div key={index} style={{
                padding: '16px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                marginBottom: '12px',
                backgroundColor: '#fafafa'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                      • {activity.action}
                    </div>
                    <div style={{ color: '#10B981', fontSize: '14px', fontWeight: '500' }}>
                      ✓ {activity.benefit}
                    </div>
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '12px', marginLeft: '16px' }}>
                    {activity.time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Summary */}
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#1f2937' }}>
            📈 This Week's Impact
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🚗</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937' }}>23</div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Smart Routes Taken</div>
            </div>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🌍</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#10B981' }}>8.7 kg</div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>CO2 Emissions Avoided</div>
            </div>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>⏱️</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#3B82F6' }}>2.5 hrs</div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Time Saved</div>
            </div>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🏅</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#F59E0B' }}>Level 7</div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Eco Driver Rank</div>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Navigation */}
      <nav style={{ 
        backgroundColor: 'white', 
        borderTop: '1px solid #e5e7eb', 
        padding: '12px 16px',
        boxShadow: '0 -2px 8px rgba(0,0,0,0.1)',
        position: 'sticky',
        bottom: 0
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
              color: '#3B82F6',
              cursor: 'pointer',
              padding: '8px 12px',
              borderRadius: '8px',
              fontWeight: '600'
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

export default Dashboard;