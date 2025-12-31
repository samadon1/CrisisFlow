import React from 'react'
import './MapPopup.css'

export const WeatherPopup = ({ event }) => {
  const fireIndex = event.data?.fire_index || 0
  const floodIndex = event.data?.flood_index || 0
  const primaryRisk = fireIndex > floodIndex ? 'fire' : 'flood'
  const riskLevel = event.risk_level || 'moderate'

  return (
    <div className="saas-popup">
      <div className={`popup-header risk-${riskLevel}`}>
        <div className="popup-type">{primaryRisk === 'fire' ? 'Fire Risk' : 'Flood Risk'}</div>
        <span className={`popup-badge badge-${riskLevel}`}>{riskLevel.toUpperCase()}</span>
      </div>

      <div className="popup-body">
        <div className="popup-location">
          <svg className="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
          {event.location.name || 'Unknown Location'}
        </div>

        <div className="popup-metrics">
          <div className="metric-row">
            <div className="metric">
              <span className="metric-label">Fire Index</span>
              <span className={`metric-value ${fireIndex > 70 ? 'critical' : fireIndex > 50 ? 'high' : ''}`}>
                {fireIndex}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Flood Index</span>
              <span className={`metric-value ${floodIndex > 70 ? 'critical' : floodIndex > 50 ? 'high' : ''}`}>
                {floodIndex}
              </span>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <span className="metric-label">Temperature</span>
              <span className="metric-value">{event.data?.temperature?.toFixed(1)}°C</span>
            </div>
            <div className="metric">
              <span className="metric-label">Humidity</span>
              <span className="metric-value">{event.data?.humidity?.toFixed(1)}%</span>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <span className="metric-label">Wind Speed</span>
              <span className="metric-value">{event.data?.wind_speed?.toFixed(1)} m/s</span>
            </div>
            <div className="metric">
              <span className="metric-label">Precipitation</span>
              <span className="metric-value">{event.data?.precipitation?.toFixed(1) || '0.0'} mm</span>
            </div>
          </div>
        </div>
      </div>

      <div className="popup-footer">
        <div className="popup-timestamp">
          {new Date(event.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  )
}

export const SocialPopup = ({ event }) => {
  const urgency = event.data?.urgency || 'low'
  const category = event.data?.category || 'general'
  const verified = event.data?.verified || false

  const urgencyColors = {
    critical: '#ff4444',
    high: '#ff8844',
    moderate: '#ffbb44',
    low: '#88dd88'
  }

  return (
    <div className="saas-popup">
      <div className={`popup-header risk-${urgency}`}>
        <div className="popup-type">Social Report</div>
        <div className="popup-badges">
          {verified && <span className="popup-badge badge-verified">VERIFIED</span>}
          <span className={`popup-badge badge-${urgency}`}>{urgency.toUpperCase()}</span>
        </div>
      </div>

      <div className="popup-body">
        <div className="popup-category">
          <svg className="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          </svg>
          {category.toUpperCase()}
        </div>

        <div className="popup-text">
          "{event.data?.text}"
        </div>

        {event.location.name && (
          <div className="popup-location">
            <svg className="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            {event.location.name}
          </div>
        )}
      </div>

      <div className="popup-footer">
        <div className="popup-source">
          <svg className="icon" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
          </svg>
          {event.source || 'Social Media'}
        </div>
        <div className="popup-timestamp">
          {new Date(event.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  )
}

export const HotspotPopup = ({ hotspot }) => {
  const riskLevel = hotspot.risk_level || 'moderate'

  return (
    <div className="saas-popup">
      <div className={`popup-header risk-${riskLevel}`}>
        <div className="popup-type">Risk Hotspot</div>
        <span className={`popup-badge badge-${riskLevel}`}>{riskLevel.toUpperCase()}</span>
      </div>

      <div className="popup-body">
        <div className="popup-location">
          <svg className="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          </svg>
          Grid {hotspot.grid_lat.toFixed(2)}, {hotspot.grid_lon.toFixed(2)}
        </div>

        <div className="popup-metrics">
          <div className="metric-row">
            <div className="metric">
              <span className="metric-label">Fire Index</span>
              <span className={`metric-value ${hotspot.avg_fire_index > 70 ? 'critical' : hotspot.avg_fire_index > 50 ? 'high' : ''}`}>
                {hotspot.avg_fire_index}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Flood Index</span>
              <span className={`metric-value ${hotspot.avg_flood_index > 70 ? 'critical' : hotspot.avg_flood_index > 50 ? 'high' : ''}`}>
                {hotspot.avg_flood_index}
              </span>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric">
              <span className="metric-label">Weather Events</span>
              <span className="metric-value">{hotspot.event_count}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Social Reports</span>
              <span className="metric-value">{hotspot.social_count}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="popup-footer">
        <div className="popup-info">
          <svg className="icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Aggregated risk zone
        </div>
      </div>
    </div>
  )
}

export const SearchLocationPopup = ({ location }) => {
  return (
    <div className="saas-popup">
      <div className="popup-header">
        <div className="popup-type">Searched Location</div>
      </div>

      <div className="popup-body">
        <div className="popup-location">
          <svg className="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          {location.displayName}
        </div>
      </div>
    </div>
  )
}
