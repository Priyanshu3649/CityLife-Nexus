import React from 'react';

const NavigationView: React.FC = () => {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-safeair-blue text-white p-4 shadow-lg">
        <h1 className="text-xl font-bold">SafeAir Navigator</h1>
      </header>

      {/* Main content area - will contain map */}
      <main className="flex-1 relative">
        <div className="w-full h-full bg-gray-100 flex items-center justify-center">
          <p className="text-gray-600">Map component will be loaded here</p>
        </div>
      </main>

      {/* Bottom navigation */}
      <nav className="bg-white border-t border-gray-200 p-4">
        <div className="flex justify-around">
          <button className="flex flex-col items-center text-safeair-blue">
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