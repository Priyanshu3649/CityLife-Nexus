/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'safeair': {
          'green': '#10B981',
          'blue': '#3B82F6',
          'red': '#EF4444',
          'yellow': '#F59E0B',
          'gray': '#6B7280'
        }
      }
    },
  },
  plugins: [],
}