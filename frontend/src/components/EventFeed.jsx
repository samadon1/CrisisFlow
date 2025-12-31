import React, { useEffect, useRef, useState } from 'react'
import './EventFeed.css'

function EventFeed({ events, onViewLocation }) {
  const feedRef = useRef(null)
  const [displayedEvents, setDisplayedEvents] = useState([])
  const [allEvents, setAllEvents] = useState([])
  const previousEventsRef = useRef([])

  // Combine and sort all events by timestamp
  useEffect(() => {
    if (!events) return

    const combined = []

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
          data: event.data,
          primaryRisk: (event.data?.fire_index || 0) > (event.data?.flood_index || 0) ? 'FIRE' : 'FLOOD',
          severity: event.data?.fire_index || event.data?.flood_index || 0
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
          category: event.data?.category?.toUpperCase(),
          text: event.data?.text,
          verified: event.data?.verified
        })
      })
    }

    // Sort by timestamp (newest first)
    combined.sort((a, b) => b.timestamp - a.timestamp)

    setAllEvents(combined)
  }, [events])

  // Stream events one at a time
  useEffect(() => {
    if (allEvents.length === 0) {
      setDisplayedEvents([])
      return
    }

    // Find new events that aren't in previous list
    const previousIds = new Set(previousEventsRef.current.map(e => e.id))
    const newEvents = allEvents.filter(e => !previousIds.has(e.id))

    if (newEvents.length > 0) {
      // Stream new events one at a time
      let index = 0
      const streamInterval = setInterval(() => {
        if (index < newEvents.length) {
          setDisplayedEvents(prev => [newEvents[index], ...prev].slice(0, 100))
          index++
        } else {
          clearInterval(streamInterval)
        }
      }, 150) // 150ms between each event (typing effect)

      return () => clearInterval(streamInterval)
    } else {
      // No new events, just set all
      setDisplayedEvents(allEvents.slice(0, 100))
    }

    previousEventsRef.current = allEvents
  }, [allEvents])

  // Auto-scroll to top when new events appear
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0
    }
  }, [displayedEvents])

  const formatTimestamp = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getRiskColor = (event) => {
    if (!event) return 'risk-low'
    const level = event.type === 'WEATHER' ? event.riskLevel : event.urgency
    switch (level) {
      case 'CRITICAL': return 'risk-critical'
      case 'HIGH': return 'risk-high'
      case 'MODERATE':
      case 'MEDIUM': return 'risk-moderate'
      default: return 'risk-low'
    }
  }

  return (
    <div className="event-feed-container">
      <div className="event-feed-header">
        <span className="feed-title">LIVE FEED</span>
        <span className="feed-count">{displayedEvents.length}</span>
      </div>

      <div className="event-feed" ref={feedRef}>
        {displayedEvents.length === 0 ? (
          <div className="feed-empty">
            <span className="feed-waiting">WAITING FOR INCOMING DATA...</span>
          </div>
        ) : (
          <div className="event-stream">
            {displayedEvents.filter(event => event != null).map((event, index) => (
              <div
                key={`${event.id}-${index}`}
                className={`stream-entry ${getRiskColor(event)} ${index === 0 ? 'stream-new' : ''}`}
              >
                {/* Main line */}
                <div className="stream-line">
                  <span className="stream-timestamp">{formatTimestamp(event.timestamp)}</span>
                  <span className="stream-type">{event.type}</span>
                  <span className="stream-location">{event.location}</span>

                  {event.type === 'WEATHER' ? (
                    <>
                      <span className={`stream-badge ${getRiskColor(event)}`}>
                        {event.riskLevel}
                      </span>
                      <span className="stream-data">
                        {event.primaryRisk}:{event.severity}
                      </span>
                    </>
                  ) : (
                    <>
                      <span className={`stream-badge ${getRiskColor(event)}`}>
                        {event.urgency}
                      </span>
                      <span className="stream-data">
                        {event.category}
                        {event.verified && ' [VERIFIED]'}
                      </span>
                    </>
                  )}
                </div>

                {/* Details line */}
                <div className="stream-details-row">
                  {event.type === 'WEATHER' ? (
                    <div className="stream-details">
                      TEMP:{event.data.temperature?.toFixed(1)}°C |
                      HUMIDITY:{event.data.humidity?.toFixed(1)}% |
                      WIND:{event.data.wind_speed?.toFixed(1)}m/s |
                      FIRE_IDX:{event.data.fire_index} |
                      FLOOD_IDX:{event.data.flood_index}
                    </div>
                  ) : event.text ? (
                    <div className="stream-details">
                      MSG: {event.text}
                    </div>
                  ) : null}

                  {onViewLocation && event.coordinates && (
                    <button
                      className="stream-view-btn"
                      onClick={() => onViewLocation(event.coordinates)}
                      title="View on map"
                    >
                      VIEW
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default EventFeed
