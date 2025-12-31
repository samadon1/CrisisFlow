import React, { useState, useEffect, useRef } from 'react'
import './BreakingUpdates.css'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function BreakingUpdates({ events, onViewLocation }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const [highlights, setHighlights] = useState([])
  const [weatherAlerts, setWeatherAlerts] = useState([])

  // Fetch weather alerts from API
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(`${API_BASE}/alerts`)
        if (response.ok) {
          const data = await response.json()
          setWeatherAlerts(data.alerts || [])
        }
      } catch (error) {
        console.error('Error fetching weather alerts:', error)
      }
    }

    fetchAlerts()
    // Refresh alerts every 5 minutes
    const interval = setInterval(fetchAlerts, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  // Combine and prioritize events (critical/high first)
  useEffect(() => {
    if (!events) return

    const combined = []

    // Add weather alerts (highest priority)
    weatherAlerts.forEach(alert => {
      combined.push({
        id: `alert-${alert.alert_id}`,
        type: 'ALERT',
        timestamp: new Date(alert.onset),
        location: alert.location.name,
        coordinates: { lat: alert.location.lat, lon: alert.location.lon },
        severity: alert.severity?.toUpperCase() || 'MODERATE',
        priority: alert.severity === 'high' || alert.severity === 'critical' ? 0 : 1,
        alertType: alert.type?.toUpperCase(),
        headline: alert.headline,
        description: alert.description,
        expires: new Date(alert.expires)
      })
    })

    // Add weather events
    if (events.weather) {
      events.weather.forEach(event => {
        combined.push({
          id: `weather-${event.event_id}`,
          type: 'WEATHER',
          timestamp: new Date(event.timestamp),
          location: event.location.name || `${event.location.lat.toFixed(2)}, ${event.location.lon.toFixed(2)}`,
          coordinates: { lat: event.location.lat, lon: event.location.lon },
          riskLevel: event.risk_level?.toUpperCase() || 'LOW',
          priority: event.risk_level === 'critical' ? 1 : event.risk_level === 'high' ? 2 : 3,
          data: event.data,
          primaryRisk: (event.data?.fire_index || 0) > (event.data?.flood_index || 0) ? 'FIRE' : 'FLOOD',
          severity: event.data?.fire_index || event.data?.flood_index || 0,
          headline: `${event.risk_level?.toUpperCase()} ${(event.data?.fire_index || 0) > (event.data?.flood_index || 0) ? 'FIRE' : 'FLOOD'} RISK in ${event.location.name || 'Unknown Location'}`
        })
      })
    }

    // Add social events
    if (events.social) {
      events.social.forEach(event => {
        combined.push({
          id: `social-${event.event_id}`,
          type: 'SOCIAL',
          timestamp: new Date(event.timestamp),
          location: `${event.location.lat.toFixed(2)}, ${event.location.lon.toFixed(2)}`,
          coordinates: { lat: event.location.lat, lon: event.location.lon },
          urgency: event.data?.urgency?.toUpperCase() || 'MEDIUM',
          priority: event.data?.urgency === 'critical' ? 1 : event.data?.urgency === 'high' ? 2 : 3,
          category: event.data?.category?.toUpperCase(),
          text: event.data?.text,
          verified: event.data?.verified,
          headline: `${event.data?.urgency?.toUpperCase()} ${event.data?.category?.toUpperCase()} REPORT`
        })
      })
    }

    // Sort by priority (critical first), then timestamp (newest first)
    combined.sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority
      return b.timestamp - a.timestamp
    })

    // Take top 10 most important
    setHighlights(combined.slice(0, 10))
  }, [events, weatherAlerts])

  // Auto-cycle through highlights
  useEffect(() => {
    if (isPaused || highlights.length === 0) return

    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % highlights.length)
    }, 4000) // 4 seconds per update

    return () => clearInterval(interval)
  }, [isPaused, highlights.length])

  const handleNext = () => {
    setCurrentIndex(prev => (prev + 1) % highlights.length)
  }

  const handlePrev = () => {
    setCurrentIndex(prev => (prev - 1 + highlights.length) % highlights.length)
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRiskClass = (event) => {
    if (event.type === 'ALERT') {
      return event.severity?.toLowerCase() || 'moderate'
    }
    const level = event.type === 'WEATHER' ? event.riskLevel : event.urgency
    return level?.toLowerCase() || 'low'
  }

  if (highlights.length === 0) {
    return (
      <div className="breaking-updates">
        <div className="breaking-header">
          <span className="breaking-badge">LIVE</span>
          <span className="breaking-title">WAITING FOR UPDATES...</span>
        </div>
      </div>
    )
  }

  const current = highlights[currentIndex]

  return (
    <div className={`breaking-updates ${getRiskClass(current)}`}>
      <div className="breaking-header">
        <span className="breaking-badge">BREAKING</span>
        <span className="breaking-title">{current.headline}</span>
        <span className="breaking-time">{formatTime(current.timestamp)}</span>
      </div>

      <div className="breaking-content">
        {current.type === 'ALERT' ? (
          <>
            <div className="breaking-message">
              <span className="message-label">LOCATION</span>
              <span className="message-text">{current.location}</span>
              <span className="message-divider">|</span>
              <span className="message-label">TYPE</span>
              <span className="message-text">{current.alertType}</span>
              <span className="message-divider">|</span>
              <span className="message-label">SEVERITY</span>
              <span className={`message-verified ${current.severity.toLowerCase()}`}>{current.severity}</span>
            </div>
            <div className="breaking-message-content">{current.description}</div>
          </>
        ) : current.type === 'WEATHER' ? (
          <div className="breaking-metrics">
            <span className="metric-item">
              <span className="metric-label">LOCATION</span>
              <span className="metric-value">{current.location}</span>
            </span>
            <span className="metric-item">
              <span className="metric-label">SEVERITY</span>
              <span className="metric-value">{current.severity}</span>
            </span>
            <span className="metric-item">
              <span className="metric-label">TEMP</span>
              <span className="metric-value">{current.data.temperature?.toFixed(1)}°C</span>
            </span>
            <span className="metric-item">
              <span className="metric-label">WIND</span>
              <span className="metric-value">{current.data.wind_speed?.toFixed(1)} m/s</span>
            </span>
            <span className="metric-item">
              <span className="metric-label">HUMIDITY</span>
              <span className="metric-value">{current.data.humidity?.toFixed(0)}%</span>
            </span>
          </div>
        ) : (
          <>
            <div className="breaking-message">
              <span className="message-label">LOCATION</span>
              <span className="message-text">{current.location}</span>
              <span className="message-divider">|</span>
              <span className="message-label">CATEGORY</span>
              <span className="message-text">{current.category}</span>
              {current.verified && (
                <>
                  <span className="message-divider">|</span>
                  <span className="message-verified">VERIFIED</span>
                </>
              )}
            </div>
            <div className="breaking-message-content">{current.text}</div>
          </>
        )}
      </div>

      <div className="breaking-controls">
        <button className="control-btn" onClick={handlePrev}>PREV</button>
        <button className="control-btn" onClick={() => setIsPaused(!isPaused)}>
          {isPaused ? 'PLAY' : 'PAUSE'}
        </button>
        <button className="control-btn" onClick={handleNext}>NEXT</button>
        <span className="control-counter">
          {currentIndex + 1} / {highlights.length}
        </span>
        {onViewLocation && current.coordinates && (
          <button
            className="view-map-btn"
            onClick={() => onViewLocation(current.coordinates)}
          >
            VIEW
          </button>
        )}
      </div>
    </div>
  )
}

export default BreakingUpdates
