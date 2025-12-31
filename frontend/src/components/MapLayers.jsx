import React from 'react'
import { Circle, Polygon, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.heat'

// Log if leaflet.heat is loaded
console.log('MapLayers.jsx loaded - L.heatLayer available?', typeof L.heatLayer)

// Heatmap Layer Component
export function HeatmapLayer({ points, intensity = 25, radius = 25 }) {
  const map = useMap()

  React.useEffect(() => {
    if (!points || points.length === 0) {
      console.log('HeatmapLayer: No points provided')
      return
    }

    console.log('HeatmapLayer: Rendering with', points.length, 'points')
    console.log('L.heatLayer available?', typeof L.heatLayer)

    // Check if heatLayer is available
    if (typeof L.heatLayer !== 'function') {
      console.error('leaflet.heat not loaded! L.heatLayer is not a function')
      return
    }

    // Convert points to [lat, lng, intensity] format
    const heatData = points.map(point => [
      point.lat,
      point.lon,
      point.intensity || 1
    ])

    console.log('Heatmap data:', heatData.slice(0, 3))

    // Create heatmap layer
    const heat = L.heatLayer(heatData, {
      radius,
      blur: 15,
      maxZoom: 17,
      max: intensity,
      gradient: {
        0.0: '#0000ff',  // Blue (low)
        0.25: '#00ffff', // Cyan
        0.5: '#00ff00',  // Green
        0.75: '#ffff00', // Yellow
        1.0: '#ff0000'   // Red (high)
      }
    })

    heat.addTo(map)
    console.log('Heatmap layer added to map')

    return () => {
      map.removeLayer(heat)
      console.log('Heatmap layer removed from map')
    }
  }, [map, points, intensity, radius])

  return null
}

// Flood Zone Visualization
export function FloodZone({ bounds, severity, depth, location }) {
  const getFloodColor = (severity) => {
    switch (severity) {
      case 'critical': return '#0044cc'
      case 'high': return '#0066ff'
      case 'moderate': return '#4488ff'
      case 'low': return '#88aaff'
      default: return '#aaccff'
    }
  }

  const getSeverityLabel = (severity) => {
    return severity.charAt(0).toUpperCase() + severity.slice(1)
  }

  return (
    <Polygon
      positions={bounds}
      pathOptions={{
        color: getFloodColor(severity),
        fillColor: getFloodColor(severity),
        fillOpacity: 0.4,
        weight: 2,
        opacity: 0.8,
        dashArray: severity === 'critical' ? '10, 5' : null
      }}
    >
      <Popup>
        <div style={{ minWidth: '200px' }}>
          <h3 style={{ margin: '0 0 8px 0', color: '#0066ff' }}>Flood Zone</h3>
          {location && <p style={{ margin: '4px 0', fontWeight: 'bold' }}>{location}</p>}
          <p style={{ margin: '4px 0' }}>
            <strong>Severity:</strong> <span style={{ color: getFloodColor(severity) }}>{getSeverityLabel(severity)}</span>
          </p>
          <p style={{ margin: '4px 0' }}>
            <strong>Flood Index:</strong> {depth}
          </p>
          <p style={{ margin: '8px 0 0 0', fontSize: '0.85em', color: '#666' }}>
            {severity === 'critical' && '⚠️ Immediate evacuation recommended'}
            {severity === 'high' && '⚠️ Avoid travel in this area'}
            {severity === 'moderate' && 'Exercise caution'}
            {severity === 'low' && 'Monitor conditions'}
          </p>
        </div>
      </Popup>
    </Polygon>
  )
}

// Fire Spread Visualization (expanding circles)
export function FireSpread({ center, radius, intensity, timestamp, location }) {
  const getFireColor = (intensity) => {
    if (intensity >= 70) return '#ff0000' // Critical
    if (intensity >= 50) return '#ff4400' // High
    if (intensity >= 30) return '#ff8800' // Moderate
    return '#ffaa00' // Low
  }

  const getSeverityLabel = (intensity) => {
    if (intensity >= 70) return 'Critical'
    if (intensity >= 50) return 'High'
    if (intensity >= 30) return 'Moderate'
    return 'Low'
  }

  // Calculate opacity based on age
  const age = Date.now() - new Date(timestamp).getTime()
  const maxAge = 30 * 60 * 1000 // 30 minutes
  const opacity = Math.max(0.2, 1 - (age / maxAge))

  // Convert radius from meters to km for display
  const radiusKm = (radius / 1000).toFixed(1)

  return (
    <>
      {/* Main fire circle */}
      <Circle
        center={[center.lat, center.lon]}
        radius={radius}
        pathOptions={{
          color: getFireColor(intensity),
          fillColor: getFireColor(intensity),
          fillOpacity: opacity * 0.3,
          weight: 2,
          opacity: opacity
        }}
        className="fire-pulse"
      >
        <Popup>
          <div style={{ minWidth: '200px' }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#ff4400' }}>Fire Risk Area</h3>
            {location && <p style={{ margin: '4px 0', fontWeight: 'bold' }}>{location}</p>}
            <p style={{ margin: '4px 0' }}>
              <strong>Risk Level:</strong> <span style={{ color: getFireColor(intensity) }}>{getSeverityLabel(intensity)}</span>
            </p>
            <p style={{ margin: '4px 0' }}>
              <strong>Fire Index:</strong> {intensity}
            </p>
            <p style={{ margin: '4px 0' }}>
              <strong>Affected Radius:</strong> ~{radiusKm} km
            </p>
            <p style={{ margin: '8px 0 0 0', fontSize: '0.85em', color: '#666' }}>
              {intensity >= 70 && '🔥 Extreme fire danger - evacuate immediately'}
              {intensity >= 50 && intensity < 70 && '🔥 High fire danger - prepare to evacuate'}
              {intensity >= 30 && intensity < 50 && '⚠️ Moderate fire risk - stay alert'}
              {intensity < 30 && 'Monitor fire conditions'}
            </p>
          </div>
        </Popup>
      </Circle>

      {/* Outer spread prediction circle */}
      <Circle
        center={[center.lat, center.lon]}
        radius={radius * 1.5}
        pathOptions={{
          color: getFireColor(intensity),
          fillColor: 'transparent',
          fillOpacity: 0,
          weight: 1,
          opacity: opacity * 0.5,
          dashArray: '5, 10'
        }}
      />
    </>
  )
}

// Wind Direction Indicator
export function WindIndicator({ position, direction, speed }) {
  // Convert wind direction to angle
  const angle = direction

  return (
    <div
      style={{
        position: 'absolute',
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: `rotate(${angle}deg)`,
        transformOrigin: 'center',
        width: '40px',
        height: '40px',
        pointerEvents: 'none'
      }}
    >
      <svg width="40" height="40" viewBox="0 0 40 40">
        <path
          d="M20 5 L25 20 L20 18 L15 20 Z"
          fill={speed > 30 ? '#ff4444' : '#ffffff'}
          stroke="#000"
          strokeWidth="1"
        />
        <text x="20" y="35" fontSize="8" fill="#ffffff" textAnchor="middle">
          {speed}mph
        </text>
      </svg>
    </div>
  )
}

// Risk Contour Lines
export function RiskContours({ contours }) {
  return (
    <>
      {contours.map((contour, idx) => (
        <Polygon
          key={idx}
          positions={contour.points}
          pathOptions={{
            color: contour.color || '#ff4400',
            fillColor: 'transparent',
            weight: 2,
            opacity: 0.6,
            dashArray: '10, 5'
          }}
        />
      ))}
    </>
  )
}
