# CrisisFlow Map Visualization Enhancements

## Overview
Enhanced the CrisisFlow disaster intelligence platform with advanced map visualization layers including heatmaps, fire spread predictions, and flood zone indicators.

## New Features Implemented

### 1. Interactive Layer Control Panel
- **Location**: Top-right corner of the map
- **Features**:
  - Toggle individual map layers on/off
  - 5 controllable layers:
    - Event Markers (default: ON)
    - Risk Hotspots (default: ON)
    - Heatmap (default: OFF)
    - Fire Spread (default: OFF)
    - Flood Zones (default: OFF)
  - Color-coded labels for easy identification
  - Smooth hover effects

### 2. Heatmap Layer
- **Component**: `HeatmapLayer` in `MapLayers.jsx`
- **Technology**: Uses `leaflet.heat` plugin
- **Data Source**: Weather events with fire/flood indices
- **Visualization**:
  - Blue → Cyan → Green → Yellow → Red gradient
  - Intensity based on max(fire_index, flood_index)
  - Configurable radius and blur
- **Use Case**: Identify high-risk concentration areas at a glance

### 3. Fire Spread Visualization
- **Component**: `FireSpread` in `MapLayers.jsx`
- **Triggers**: Displays for events with fire_index > 50
- **Features**:
  - Main fire circle with color intensity based on severity
  - Predicted spread circle (1.5x radius) with dashed border
  - Time-based opacity (fades over 30 minutes)
  - Color scale:
    - Critical (≥70): Bright red (#ff0000)
    - High (≥50): Orange-red (#ff4400)
    - Moderate (≥30): Orange (#ff8800)
    - Low: Yellow (#ffaa00)
- **Use Case**: Predict fire expansion and prioritize evacuation zones

### 4. Flood Zone Visualization
- **Component**: `FloodZone` in `MapLayers.jsx`
- **Triggers**: Displays for events with flood_index > 30
- **Features**:
  - Polygon overlay showing affected area
  - Severity-based colors (blue spectrum)
  - Semi-transparent fill with solid border
  - Dashed border for critical zones
  - Approximately 22km x 22km coverage area per event
- **Use Case**: Identify flood-prone areas and plan evacuation routes

### 5. Global AI Q&A Input
- **Location**: Bottom of AlertPanel (always visible)
- **Features**:
  - Floating input field accessible from all tabs
  - Sends question and auto-switches to "CRISISFLOW AI" tab
  - Context-aware responses using Google Gemini
  - Real-time chat interface with message history
- **Use Case**: Quick access to AI assistance without navigation

## Technical Implementation

### Files Modified

#### `/frontend/src/components/Map.jsx`
- Added layer visibility state management
- Implemented `toggleLayer()` function
- Created data transformation functions:
  - `getHeatmapData()` - Prepares weather events for heatmap
  - `getFireEvents()` - Filters high fire index events
  - `getFloodZones()` - Extracts flood-prone areas
- Integrated visualization components
- Built interactive layer control UI
- Made existing layers (markers, hotspots) toggleable

#### `/frontend/src/components/MapLayers.jsx` (NEW)
Components created:
- `HeatmapLayer` - Gradient-based heat visualization
- `FloodZone` - Polygon-based flood area display
- `FireSpread` - Expanding circle fire prediction
- `WindIndicator` - SVG-based wind direction (ready for use)
- `RiskContours` - Contour line visualization (ready for use)

#### `/frontend/src/components/AlertPanel.jsx`
- Added global floating Q&A input at bottom
- Auto-switches to chat tab when question submitted
- Only hidden when user is already on chat tab
- Added bottom margin to content when input is visible

#### `/frontend/src/components/AlertPanel.css`
- Styled global floating input with glassmorphism effect
- Added focus states and transitions
- Ensured proper z-index layering

### Dependencies Added
```bash
npm install leaflet.heat --save
```

### Backend Integration Points

#### Existing Endpoints Used:
- `GET /api/events` - Weather and social event data
- `GET /api/hotspots` - Risk hotspot grid data
- `POST /api/ai/chat` - AI Q&A responses

#### Ready for Implementation:
- `POST /api/config/datasource` - Add new data sources
- `POST /api/config/location` - Configure monitored locations
- `POST /api/config/social` - Set social media keywords
- `GET /api/config/{type}` - Retrieve current configuration
- `DELETE /api/config/{type}/{id}` - Remove configuration

## How to Use

### Viewing Different Layers

1. **Start the Application**
   - Frontend: `npm run dev` (runs on http://localhost:5173)
   - Backend: `python backend/main.py` (runs on http://localhost:8000)

2. **Toggle Layers**
   - Look for "Map Layers" panel in top-right corner
   - Check/uncheck layers to show/hide them
   - Try combinations for different insights:
     - Heatmap + Fire Spread = Fire risk overview
     - Flood Zones + Hotspots = Water emergency zones
     - All layers = Complete risk assessment

3. **Interact with AI**
   - Use the floating input at the bottom of any tab
   - Type questions like:
     - "What are the most critical areas right now?"
     - "Should we evacuate the downtown area?"
     - "What's the fire spread prediction for San Diego?"
   - Automatically switches to AI chat tab with context-aware response

### Best Practices

- **Heatmap**: Use for initial risk assessment across large areas
- **Fire Spread**: Monitor in real-time during active wildfire events
- **Flood Zones**: Check during heavy rainfall or near water bodies
- **Event Markers**: Keep ON for precise incident locations
- **Risk Hotspots**: Always ON for AI-identified danger zones

## Data Flow

```
Weather API (Tomorrow.io)
  → Kafka Stream (Confluent Cloud)
    → FastAPI Backend
      → Event Processing
        → Frontend Map Components
          → Visualization Layers
```

## Performance Considerations

1. **Heatmap Rendering**
   - Uses Canvas-based rendering (leaflet.heat)
   - Efficient for 100+ points
   - Updates on data refresh only

2. **Fire Spread Circles**
   - SVG-based, conditional rendering
   - Only renders events with fire_index > 50
   - Time-based opacity reduces visual clutter

3. **Flood Zones**
   - Polygon rendering with transparency
   - Only shows flood_index > 30
   - Minimal performance impact

4. **Layer Toggle**
   - Instant show/hide with React state
   - No re-fetching required
   - Preserves map position

## Future Enhancements

### Ready to Implement:
- `WindIndicator` component (already created)
- `RiskContours` component (already created)
- Historical playback (time slider)
- Export map as image/PDF

### Potential Additions:
- 3D terrain visualization
- Satellite imagery overlay
- Traffic congestion layer
- Emergency shelter locations
- Evacuation route planning
- Population density heatmap

## Configuration Modal

The `ConfigModal` component allows users to:

1. **Add Data Sources**
   - 911 Emergency Calls
   - NOAA Weather Alerts
   - USGS Earthquake Data
   - Traffic Sensors
   - IoT Environmental Sensors
   - News APIs
   - Custom Webhooks

2. **Configure Locations**
   - Add cities/regions to monitor
   - Set priority levels
   - Define radius of concern

3. **Social Media Topics**
   - Keywords to track
   - Hashtags to monitor
   - Language preferences
   - Sentiment filters

## Testing Checklist

- [x] Heatmap renders correctly with weather data
- [x] Fire spread circles display for high fire index events
- [x] Flood zones appear for high flood index events
- [x] Layer controls toggle visibility properly
- [x] Global Q&A input sends messages and switches tabs
- [x] No compilation errors
- [x] Responsive design works on different screen sizes
- [ ] Backend configuration endpoints (pending implementation)

## Notes

- All visualization layers are data-driven and update automatically with new events
- Layer states persist during user interaction (zoom, pan)
- Map performance remains smooth even with all layers enabled
- Mobile-responsive design ensures usability across devices

## Credits

- **Map Library**: Leaflet + React-Leaflet
- **Heatmap**: leaflet.heat plugin
- **AI**: Google Gemini API
- **Streaming**: Confluent Kafka
- **Weather Data**: Tomorrow.io API
