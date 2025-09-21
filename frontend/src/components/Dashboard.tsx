import React from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const metrics = [
    { label: 'Time Saved', value: '45 minutes', color: '#10B981' },
    { label: 'CO2 Avoided', value: '2.3 kg', color: '#3B82F6' },
    { label: 'Clean Routes', value: '12 trips', color: '#8B5CF6' },
    { label: 'Eco Score', value: '850 pts', color: '#F59E0B' }
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
            Impact Dashboard
          </h1>
        </div>
      </header>
      
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
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
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  backgroundColor: metric.color,
                  borderRadius: '50%',
                  marginRight: '16px'
                }}></div>
                <div>
                  <div style={{ 
                    fontSize: '14px', 
                    color: '#6b7280',
                    marginBottom: '4px'
                  }}>
                    {metric.label}
                  </div>
                  <div style={{ 
                    fontSize: '24px', 
                    fontWeight: 'bold',
                    color: '#1f2937'
                  }}>
                    {metric.value}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '16px' }}>Recent Activity</h2>
          <div style={{ color: '#6b7280' }}>
            <p>• Used clean route to downtown - saved 15 minutes</p>
            <p>• Avoided high pollution area on Main Street</p>
            <p>• Synchronized with 3 traffic signals</p>
            <p>• Earned 50 eco points for choosing green route</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;