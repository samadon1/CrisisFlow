import React, { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Rectangle, useMap } from 'react-leaflet'
import { renderToStaticMarkup } from 'react-dom/server'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import SearchBar from './SearchBar'
import { WeatherPopup, SocialPopup, HotspotPopup, SearchLocationPopup } from './MapPopup'
import { HeatmapLayer, FloodZone, FireSpread } from './MapLayers'
import './MapPopup.css'

// Fix for default markers in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Component to handle map updates
function MapUpdater({ events, hotspots, userHasInteracted, onResetView }) {
  const map = useMap()
  const hasInitiallyZoomed = useRef(false)

  useEffect(() => {
    // Disabled auto-fit on initial load - use default center/zoom instead
    // Only auto-fit when user explicitly resets view
    hasInitiallyZoomed.current = true
  }, [hotspots, map, userHasInteracted])

  // Reset view when requested
  useEffect(() => {
    if (onResetView && hotspots && hotspots.length > 0) {
      const bounds = hotspots.map(h => [h.grid_lat, h.grid_lon])
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] })
      }
    }
  }, [onResetView, hotspots, map])

  return null
}

function Map({ events, hotspots, loading, viewLocation }) {
  const mapRef = useRef()
  const [userHasInteracted, setUserHasInteracted] = useState(false)
  const [resetViewTrigger, setResetViewTrigger] = useState(0)
  const [searchMarker, setSearchMarker] = useState(null)
  const [visibleLayers, setVisibleLayers] = useState({
    heatmap: false,
    fireSpread: false,
    floodZones: false,
    markers: true,
    hotspots: true
  })
  const [layersExpanded, setLayersExpanded] = useState(false)
  const [legendExpanded, setLegendExpanded] = useState(false)

  // Default center on US
  const defaultCenter = [39.8283, -98.5795]
  const defaultZoom = 5

  // Handle map interaction events
  const handleMapInteraction = () => {
    if (!userHasInteracted) {
      setUserHasInteracted(true)
    }
  }

  // Reset view function
  const handleResetView = () => {
    setUserHasInteracted(false)
    setResetViewTrigger(prev => prev + 1)
    setSearchMarker(null)
  }

  // Handle search location selection
  const handleLocationSelect = (lat, lon, displayName) => {
    setSearchMarker({ lat, lon, displayName })
    setUserHasInteracted(true)

    // Fly to the selected location
    if (mapRef.current) {
      mapRef.current.flyTo([lat, lon], 12, {
        duration: 1.5
      })
    }
  }

  // Handle external view location requests (from BreakingUpdates)
  useEffect(() => {
    if (viewLocation && mapRef.current) {
      const { lat, lon } = viewLocation
      setSearchMarker({ lat, lon, displayName: 'Event Location' })
      setUserHasInteracted(true)
      mapRef.current.flyTo([lat, lon], 12, {
        duration: 1.5
      })
    }
  }, [viewLocation])


  // Get risk color
  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return '#ff0000'
      case 'high': return '#ff6600'
      case 'moderate': return '#ffaa00'
      case 'low': return '#00aa00'
      default: return '#666666'
    }
  }

  // Get marker size based on index value (increased for better visibility)
  const getMarkerSize = (index) => {
    if (index >= 70) return 22  // Critical - very large
    if (index >= 50) return 18  // High - large
    if (index >= 30) return 14  // Moderate - medium
    return 11  // Low - small but visible
  }

  // Check if marker should pulse (critical or high risk)
  const shouldPulse = (riskLevel) => {
    return riskLevel === 'critical' || riskLevel === 'high'
  }

  // Toggle layer visibility
  const toggleLayer = (layerName) => {
    setVisibleLayers(prev => {
      const newState = {
        ...prev,
        [layerName]: !prev[layerName]
      }
      console.log(`Layer ${layerName} toggled:`, newState[layerName])
      return newState
    })
  }

  // Prepare heatmap data from weather events
  const getHeatmapData = () => {
    if (!events?.weather) {
      console.log('getHeatmapData: No weather events')
      return []
    }
    const data = events.weather.map(event => ({
      lat: event.location.lat,
      lon: event.location.lon,
      intensity: Math.max(event.data?.fire_index || 0, event.data?.flood_index || 0) / 100
    }))
    console.log('getHeatmapData:', data.length, 'points')
    return data
  }

  // Get fire events for FireSpread visualization
  const getFireEvents = () => {
    if (!events?.weather) {
      console.log('getFireEvents: No weather events')
      return []
    }
    const fireEvents = events.weather.filter(e => (e.data?.fire_index || 0) > 20)
    console.log('getFireEvents:', fireEvents.length, 'fire events (fire_index > 20)')
    return fireEvents
  }

  // Get flood zones from weather events - use circles instead of polygons for more organic look
  const getFloodZones = () => {
    if (!events?.weather) {
      console.log('getFloodZones: No weather events')
      return []
    }
    const zones = events.weather
      .filter(e => (e.data?.flood_index || 0) > 20) // Only show significant flood risk
      .map(event => {
        const floodIndex = event.data.flood_index
        // Calculate radius based on flood severity (more realistic)
        // Low (20-40): 2-4km
        // Moderate (40-60): 4-7km
        // High (60-80): 7-10km
        // Critical (80-100): 10-15km
        const baseRadius = 2000 // 2km base
        const scaledRadius = baseRadius + (floodIndex / 100) * 13000 // Scale up to 15km max

        return {
          center: event.location,
          location: event.location?.name,
          severity: floodIndex >= 70 ? 'critical' :
                    floodIndex >= 50 ? 'high' :
                    floodIndex >= 30 ? 'moderate' : 'low',
          depth: floodIndex,
          radius: scaledRadius
        }
      })
    console.log('getFloodZones:', zones.length, 'flood zones (flood_index > 20)')
    return zones
  }

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      <SearchBar onLocationSelect={handleLocationSelect} />

      <MapContainer
        ref={mapRef}
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        className="crisis-map"
        whenReady={(map) => {
          map.target.on('dragstart', handleMapInteraction)
          map.target.on('zoomstart', handleMapInteraction)
          map.target.on('click', handleMapInteraction)
        }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          opacity={0.8}
        />

        <MapUpdater
          events={events}
          hotspots={hotspots}
          userHasInteracted={userHasInteracted}
          onResetView={resetViewTrigger}
        />

        {/* Heatmap Layer */}
        {visibleLayers.heatmap && (
          <HeatmapLayer
            points={getHeatmapData()}
            intensity={1}
            radius={25}
          />
        )}

        {/* Fire Spread Visualization */}
        {visibleLayers.fireSpread && getFireEvents().map((event, idx) => {
          // Calculate radius based on fire index (more realistic scaling)
          // Low risk (20-40): 500m-1km radius
          // Medium risk (40-60): 1-2km radius
          // High risk (60-100): 2-5km radius
          const fireIndex = event.data?.fire_index || 0
          const baseRadius = 500 // 500 meters minimum
          const scaledRadius = baseRadius + (fireIndex / 100) * 4500 // Scale up to 5km max

          return (
            <FireSpread
              key={`fire-${event.event_id || idx}`}
              center={event.location}
              radius={scaledRadius}
              intensity={fireIndex}
              timestamp={event.timestamp}
              location={event.location?.name}
            />
          )
        })}

        {/* Flood Zones Visualization */}
        {visibleLayers.floodZones && getFloodZones().map((zone, idx) => {
          const lat = zone.center.lat
          const lon = zone.center.lon
          const offset = 0.05 // approximately 5.5km (smaller, more realistic flood zone)
          // Create proper rectangle bounds (clockwise from SW corner)
          const bounds = [
            [lat - offset, lon - offset], // Southwest
            [lat - offset, lon + offset], // Southeast
            [lat + offset, lon + offset], // Northeast
            [lat + offset, lon - offset]  // Northwest
          ]
          return (
            <FloodZone
              key={`flood-${idx}`}
              bounds={bounds}
              severity={zone.severity}
              depth={zone.depth}
              location={zone.location}
            />
          )
        })}

        {/* Search location marker */}
        {searchMarker && (
          <Marker position={[searchMarker.lat, searchMarker.lon]}>
            <Popup>
              <div dangerouslySetInnerHTML={{ __html: renderToStaticMarkup(<SearchLocationPopup location={searchMarker} />) }} />
            </Popup>
          </Marker>
        )}

        {/* Render hotspot grid cells */}
        {visibleLayers.hotspots && hotspots && hotspots.map((hotspot, idx) => {
          const bounds = [
            [hotspot.grid_lat - 0.25, hotspot.grid_lon - 0.25],
            [hotspot.grid_lat + 0.25, hotspot.grid_lon + 0.25]
          ]
          return (
            <Rectangle
              key={`hotspot-${idx}`}
              bounds={bounds}
              pathOptions={{
                color: getRiskColor(hotspot.risk_level),
                weight: 2,
                opacity: 0.6,
                fillOpacity: 0.2,
                fillColor: getRiskColor(hotspot.risk_level)
              }}
            >
              <Popup>
                <div dangerouslySetInnerHTML={{ __html: renderToStaticMarkup(<HotspotPopup hotspot={hotspot} />) }} />
              </Popup>
            </Rectangle>
          )
        })}

        {/* Render weather events */}
        {visibleLayers.markers && events && events.weather && events.weather.map((event, idx) => {
          const fireIndex = event.data?.fire_index || 0
          const floodIndex = event.data?.flood_index || 0
          const primaryRisk = fireIndex > floodIndex ? 'fire' : 'flood'
          const primaryIndex = Math.max(fireIndex, floodIndex)

          // Get color based on risk level and type
          const getWeatherMarkerColor = () => {
            if (primaryRisk === 'fire') {
              if (primaryIndex >= 70) return '#ff0000' // Critical fire
              if (primaryIndex >= 50) return '#ff4400' // High fire
              if (primaryIndex >= 30) return '#ff8800' // Moderate fire
              return '#ffaa00' // Low fire
            } else {
              if (primaryIndex >= 70) return '#0044cc' // Critical flood
              if (primaryIndex >= 50) return '#0066ff' // High flood
              if (primaryIndex >= 30) return '#4488ff' // Moderate flood
              return '#88aaff' // Low flood
            }
          }

          return (
            <CircleMarker
              key={`weather-${event.event_id || idx}`}
              center={[event.location.lat, event.location.lon]}
              radius={getMarkerSize(primaryIndex)}
              pathOptions={{
                fillColor: getWeatherMarkerColor(),
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
              }}
            >
              <Popup>
                <div dangerouslySetInnerHTML={{ __html: renderToStaticMarkup(<WeatherPopup event={event} />) }} />
              </Popup>
            </CircleMarker>
          )
        })}

        {/* Render social events */}
        {visibleLayers.markers && events && events.social && events.social.map((event, idx) => {
          const urgencyColors = {
            'critical': '#ff0000',
            'high': '#ff6600',
            'medium': '#ffaa00',
            'low': '#00aa00'
          }

          const urgencySizes = {
            'critical': 14,  // Increased for visibility
            'high': 11,
            'medium': 9,
            'low': 7
          }

          const urgency = event.data?.urgency || 'low'

          return (
            <CircleMarker
              key={`social-${event.event_id || idx}`}
              center={[event.location.lat, event.location.lon]}
              radius={urgencySizes[urgency] || 6}
              pathOptions={{
                fillColor: urgencyColors[urgency] || '#ff8844',
                color: '#fff',
                weight: urgency === 'critical' ? 2 : 1,
                opacity: 1,
                fillOpacity: urgency === 'critical' || urgency === 'high' ? 0.8 : 0.6
              }}
            >
              <Popup>
                <div dangerouslySetInnerHTML={{ __html: renderToStaticMarkup(<SocialPopup event={event} />) }} />
              </Popup>
            </CircleMarker>
          )
        })}

      </MapContainer>

      {/* Layer Control Panel */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.85)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '8px',
        padding: '12px',
        zIndex: 2000,
        minWidth: '180px'
      }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            marginBottom: layersExpanded ? '8px' : '0'
          }}
          onClick={() => setLayersExpanded(!layersExpanded)}
        >
          <div style={{
            color: 'white',
            fontSize: '0.75rem',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            opacity: 0.7
          }}>
            Map Layers
          </div>
          <span style={{ color: 'white', fontSize: '0.7rem', opacity: 0.7 }}>
            {layersExpanded ? '▼' : '▶'}
          </span>
        </div>
        {layersExpanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            color: 'white',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <input
              type="checkbox"
              checked={visibleLayers.markers}
              onChange={() => toggleLayer('markers')}
              style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Event Markers
          </label>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            color: 'white',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <input
              type="checkbox"
              checked={visibleLayers.hotspots}
              onChange={() => toggleLayer('hotspots')}
              style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Risk Hotspots
          </label>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            color: '#ff4444',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <input
              type="checkbox"
              checked={visibleLayers.heatmap}
              onChange={() => toggleLayer('heatmap')}
              style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Heatmap
          </label>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            color: '#ff8800',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <input
              type="checkbox"
              checked={visibleLayers.fireSpread}
              onChange={() => toggleLayer('fireSpread')}
              style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Fire Spread
          </label>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            color: '#4488ff',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <input
              type="checkbox"
              checked={visibleLayers.floodZones}
              onChange={() => toggleLayer('floodZones')}
              style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Flood Zones
          </label>
        </div>
        )}
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '70px',
        left: '10px',
        background: 'rgba(0, 0, 0, 0.85)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '8px',
        padding: '12px',
        zIndex: 1000,
        minWidth: '200px',
        maxWidth: '250px'
      }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            marginBottom: legendExpanded ? '10px' : '0'
          }}
          onClick={() => setLegendExpanded(!legendExpanded)}
        >
          <div style={{
            color: 'white',
            fontSize: '0.75rem',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            opacity: 0.7
          }}>
            Legend
          </div>
          <span style={{ color: 'white', fontSize: '0.7rem', opacity: 0.7 }}>
            {legendExpanded ? '▼' : '▶'}
          </span>
        </div>

        {legendExpanded && (
        <>
        {/* Weather Events */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{ color: 'white', fontSize: '0.7rem', marginBottom: '4px', opacity: 0.8 }}>
            Weather Events (Fire)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#ff0000', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Critical (70-100)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: '#ff4400', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>High (50-69)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '11px', height: '11px', borderRadius: '50%', background: '#ff8800', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Moderate (30-49)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ffaa00', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Low (&lt;30)</span>
            </div>
          </div>
        </div>

        {/* Social Events */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{ color: 'white', fontSize: '0.7rem', marginBottom: '4px', opacity: 0.8 }}>
            Social Reports
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff0000', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Critical</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff6600', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>High</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffaa00', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Medium</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#00aa00', border: '1px solid #fff' }}></div>
              <span style={{ color: 'white', fontSize: '0.7rem' }}>Low</span>
            </div>
          </div>
        </div>

        {/* Layer Descriptions */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: '8px', marginTop: '8px' }}>
          <div style={{ color: 'white', fontSize: '0.65rem', opacity: 0.6, lineHeight: '1.4' }}>
            <strong>Hotspots:</strong> 55km grid aggregation<br/>
            <strong>Fire/Flood Zones:</strong> Risk area estimates
          </div>
        </div>
        </>
        )}
      </div>

      {/* Loading overlay */}
      {loading && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          zIndex: 1000
        }}>
          Loading data...
        </div>
      )}
    </div>
  )
}

export default Map