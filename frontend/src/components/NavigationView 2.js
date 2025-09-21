import React from 'react';

const NavigationView = () => {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <h1 className="text-xl font-bold">SafeAir Navigator</h1>
      </header>

      {/* Main content area - will contain map */}
      <main className="flex-1 relative">
        <div className="w-full h-full bg-gray-100 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">SafeAir Navigator</h2>
            <p className="text-gray-600 mb-4">Smart navigation with pollution-aware routing</p>
            <div className="bg-white p-6 rounded-lg shadow-md max-w-md mx-auto">
              <h3 className="text-lg font-semibold mb-2">Features:</h3>
              <ul className="text-left space-y-2">
                <li>🚦 Green Corridor Synchronization</li>
                <li>🌱 Pollution-Aware Routing</li>
                <li>📱 Driver Alert System</li>
                <li>🚨 Emergency Broadcast</li>
                <li>📊 Impact Dashboard</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="bg-white border-t border-gray-200 p-4">
        <div className="flex justify-around">
          <button className="flex flex-col items-center text-blue-600">
            <span className="text-xs">Navigate</span>
          </button>
          <button className="flex flex-col items-center text-gray-500">
            <span className="text-xs">Dashboard</span>
          </button>
          <button className="flex flex-col items-center text-gray-500">
            <span className="text-xs">Settings</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default NavigationView;