# CityLife Nexus - App Workflow

CityLife Nexus is a smart navigation application that provides pollution-aware routing with real-time traffic light advisories and voice navigation capabilities.

## Main Workflow

### 1. Initial Load
- Application loads the NavigationView component as the default route
- Automatically detects user's current location using Geolocation API
- Sets the "From" field to "Current Location"
- Initializes the map with user's current position as center

### 2. Location Selection
**Starting Point:**
- User can either use current location (auto-detected) or enter a custom starting location
- As user types in the "From" field, autocomplete suggestions appear
- User selects a suggestion to set the starting coordinates

**Destination:**
- User enters destination in the "To" field
- As user types, autocomplete suggestions appear
- User selects a suggestion to set the destination coordinates

**Location Swap:**
- User can swap start and end locations using the swap button (⇄)

### 3. Route Preferences
User can customize their route by selecting:
- **Route Preference:**
  - Fastest Route: Prioritizes travel time
  - Balanced Route: Balances time and air quality
  - Cleanest Air Route: Prioritizes air quality over time
  
- **Vehicle Type:**
  - Car
  - Bike
  - Bus
  - Truck

### 4. Route Search
- User clicks "Find Routes" button
- Application sends request to backend API with:
  - Start coordinates
  - End coordinates
  - Route preferences
  - Vehicle type
- Backend returns multiple route options with:
  - Estimated travel time
  - Distance
  - Air Quality Index (AQI)
  - Route description

### 5. Route Selection
- User views available routes displayed in cards
- Each route shows:
  - Route name
  - Travel time
  - Distance
  - AQI with color coding
  - Route description
- User selects a route by clicking on the route card
- Application provides voice feedback about selected route

### 6. Navigation Start
- User clicks "START NAV" button on selected route
- Application:
  - Initializes navigation mode
  - Fetches traffic light data along the route
  - Begins simulating user position updates
  - Starts providing turn-by-turn directions
  - Begins monitoring traffic lights for advisories

### 7. Active Navigation
During navigation, the app provides:

**Turn-by-Turn Directions:**
- Visual display of next instruction (icon, text, detail)
- Voice announcements of navigation instructions
- Progress simulation along the route

**Traffic Light Advisory System:**
- Real-time monitoring of traffic lights along the route
- Color-coded display of traffic light status (red, yellow, green)
- Countdown timers for light changes
- Proactive advisories based on:
  - Distance to traffic light
  - Current light color
  - Time remaining for color change
  - Recommended speed adjustments
  - ML-based optimization suggestions

**Voice Navigation:**
- Turn-by-turn directions announced
- Traffic light advisories announced
- Speed recommendations announced
- ML-based driving suggestions announced

### 8. Navigation Controls
- User can stop navigation at any time using "Stop Navigation" button
- Map updates in real-time to show current position
- Next traffic signal information displayed
- Current instruction prominently shown

## Additional Features

### Dashboard Access
- User can navigate to dashboard using the header button
- Dashboard likely shows analytics and historical data

### Settings Access
- User can access settings through navigation routes
- Settings likely include preferences and customization options

### Fullscreen Mode
- Map can be viewed in fullscreen mode (toggleFullScreen function available)

## Technical Components

### API Integrations
1. **Maps API:**
   - Autocomplete for location search
   - Geocoding for coordinate conversion
   - Route calculation with AQI data

2. **Traffic Light API:**
   - Real-time traffic light status along routes
   - Signal timing data

### UI Components
1. **MapComponent:**
   - Interactive Google Map display
   - Traffic light markers
   - User position tracking
   - Route visualization

2. **NavigationView:**
   - Main navigation interface
   - Route planning controls
   - Traffic advisory display
   - Voice navigation controls

### State Management
- Location data (start, end, current)
- Route preferences
- Available routes
- Selected route
- Traffic light data
- Navigation status
- Voice navigation toggle
- User position simulation

## Data Flow
1. User inputs → Location search → Coordinate conversion
2. Coordinates + preferences → Route API → Route options
3. Route selection → Traffic light API → Light data
4. Navigation start → Position simulation → Real-time updates
5. Light data + position → Advisory system → Voice/text alerts

This workflow provides a comprehensive navigation experience with environmental awareness and intelligent traffic advisories.