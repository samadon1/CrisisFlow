# CrisisFlow Map Layer Controls - Visual Guide

## Layer Control Panel Location

```
┌─────────────────────────────────────────────────────┐
│ [Search Bar]                    ┌─────────────────┐ │
│                                 │  MAP LAYERS     │ │
│                                 │ ☑ Event Markers │ │
│                                 │ ☑ Risk Hotspots │ │
│                                 │ ☐ Heatmap       │ │
│                                 │ ☐ Fire Spread   │ │
│                                 │ ☐ Flood Zones   │ │
│                                 └─────────────────┘ │
│                                 ┌─────────────────┐ │
│                                 │  Reset View     │ │
│         MAP AREA                └─────────────────┘ │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Event Markers (White) - Default ON
```
● Small colored circles
● Red = Fire events
● Blue = Flood events
● Orange = Social media reports
● Click for popup with details
```

### 2. Risk Hotspots (White) - Default ON
```
□ Grid rectangles (0.5° x 0.5°)
□ Red = Critical risk
□ Orange = High risk
□ Yellow = Moderate risk
□ Green = Low risk
□ Semi-transparent fill
```

### 3. Heatmap (Red) - Default OFF
```
🔥 Gradient overlay
🔥 Blue (low) → Red (high)
🔥 Shows risk concentration
🔥 Based on fire/flood indices
🔥 Smooth transitions
```

### 4. Fire Spread (Orange) - Default OFF
```
○ Expanding circles for fires
○ Solid inner circle = current extent
○ Dashed outer circle = predicted spread (1.5x)
○ Opacity fades over time (30 min)
○ Only shows when fire_index > 50
○ Color intensity = severity
```

### 5. Flood Zones (Blue) - Default OFF
```
▭ Polygon areas
▭ Blue shades by severity
▭ Critical zones have dashed borders
▭ ~22km coverage per event
▭ Only shows when flood_index > 30
▭ Semi-transparent overlay
```

## Usage Scenarios

### Scenario 1: Initial Risk Assessment
```
✓ Event Markers - ON
✓ Risk Hotspots - ON
✓ Heatmap - ON
✗ Fire Spread - OFF
✗ Flood Zones - OFF

Result: Quick overview of all risks with concentration areas
```

### Scenario 2: Active Wildfire Monitoring
```
✓ Event Markers - ON
✗ Risk Hotspots - OFF
✗ Heatmap - OFF
✓ Fire Spread - ON
✗ Flood Zones - OFF

Result: Clear view of fire locations and predicted expansion
```

### Scenario 3: Flood Emergency Response
```
✓ Event Markers - ON
✓ Risk Hotspots - ON
✗ Heatmap - OFF
✗ Fire Spread - OFF
✓ Flood Zones - ON

Result: Identify flooded areas and affected grid zones
```

### Scenario 4: Complete Crisis Overview
```
✓ Event Markers - ON
✓ Risk Hotspots - ON
✓ Heatmap - ON
✓ Fire Spread - ON
✓ Flood Zones - ON

Result: All available intelligence on single map
Warning: May be visually dense in high-activity areas
```

## Color Legend

### Event Markers
- 🔴 Red Circle = Fire Event (fire_index > flood_index)
- 🔵 Blue Circle = Flood Event (flood_index > fire_index)
- 🟠 Orange Circle = Social Media Report

### Risk Hotspots (Rectangles)
- 🟥 Red = Critical Risk (≥10 events)
- 🟧 Orange = High Risk (5-9 events)
- 🟨 Yellow = Moderate Risk (2-4 events)
- 🟩 Green = Low Risk (1 event)

### Fire Spread Circles
- 🔴 Bright Red = Critical (fire_index ≥ 70)
- 🟠 Orange-Red = High (fire_index ≥ 50)
- 🟠 Orange = Moderate (fire_index ≥ 30)
- 🟡 Yellow = Low (fire_index < 30)

### Flood Zones (Polygons)
- 🔷 Dark Blue = Critical (flood_index ≥ 70)
- 🔹 Blue = High (flood_index ≥ 50)
- 🔵 Light Blue = Moderate (flood_index ≥ 30)
- ⬜ Very Light Blue = Low (flood_index < 30)

### Heatmap Gradient
```
Low Risk                                      High Risk
  ↓                                              ↓
[Blue] → [Cyan] → [Green] → [Yellow] → [Red]
```

## Interactive Features

### Layer Control Panel
- **Click checkbox**: Toggle layer on/off
- **Hover over label**: Highlights with semi-transparent background
- **Always visible**: Panel stays on screen during map interaction

### Map Interactions
- **Click event marker**: Shows popup with details
- **Click hotspot**: Shows aggregated risk information
- **Zoom in/out**: All layers scale appropriately
- **Pan map**: All layers move together
- **Reset View**: Returns to default view showing all hotspots

### Global AI Q&A Input
```
┌──────────────────────────────────────────────────────┐
│                    MAIN CONTENT AREA                 │
│                                                      │
│   (Any tab: Dashboard, AI Command, Stats)           │
│                                                      │
├──────────────────────────────────────────────────────┤
│ 🤖 Ask CrisisFlow AI anything...          [Send ➤]  │
└──────────────────────────────────────────────────────┘
```

- **Always visible**: Except on "CRISISFLOW AI" tab (to avoid duplication)
- **Type question**: Hit Enter or click Send
- **Auto-navigation**: Automatically switches to AI chat tab
- **Context-aware**: AI knows current crisis situation

## Performance Tips

1. **Start with defaults**: Event Markers + Risk Hotspots are optimal for most cases
2. **Enable layers as needed**: Toggle additional layers for specific scenarios
3. **Disable unused layers**: Improves rendering performance on slower devices
4. **Combine strategically**:
   - Heatmap + Fire Spread = Fire overview
   - Flood Zones + Hotspots = Water emergency
   - All layers = Complete intelligence (may be dense)

## Data Update Behavior

- **Real-time updates**: All layers refresh with new event data
- **Automatic refresh**: Backend polls every 30 seconds
- **Persistent state**: Layer visibility preserved during updates
- **Smooth transitions**: No flickering when data changes

## Mobile Responsiveness

- **Touch support**: All controls work with touch
- **Responsive layout**: Layer panel adapts to screen size
- **Gesture support**: Pinch to zoom, swipe to pan
- **Optimized rendering**: Reduced complexity on mobile devices

## Keyboard Shortcuts (Future Enhancement)

Planned shortcuts:
- `M` - Toggle markers
- `H` - Toggle hotspots
- `T` - Toggle heatmap (T for thermal)
- `F` - Toggle fire spread
- `W` - Toggle flood zones (W for water)
- `R` - Reset view
- `A` - Focus AI input

## Troubleshooting

**Q: Heatmap not showing?**
- Ensure there are weather events with fire/flood indices
- Check layer is enabled in control panel
- Zoom in for better visibility

**Q: Fire spread circles not visible?**
- Only shows for events with fire_index > 50
- Check if any qualifying events exist
- Toggle layer off and on to refresh

**Q: Flood zones not appearing?**
- Only shows for events with flood_index > 30
- Verify flood events in the data
- Try zooming to event locations

**Q: Too many overlapping layers?**
- Disable some layers for clarity
- Try scenarios 1-3 instead of scenario 4
- Use heatmap alone for overview

**Q: AI input not responding?**
- Check backend is running (port 8000)
- Verify network connection
- Look for errors in browser console
