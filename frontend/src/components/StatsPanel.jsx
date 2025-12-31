import React, { useState } from 'react'
import EventFeed from './EventFeed'
import BreakingUpdates from './BreakingUpdates'
import ConfigModal from './ConfigModal'
import './StatsPanel.css'

function StatsPanel({ stats, events, onViewLocation }) {
  const [selectedView, setSelectedView] = useState(null) // null = overview, 'weather', 'social', 'critical', etc.
  const [modalOpen, setModalOpen] = useState(false)
  const [modalType, setModalType] = useState(null)

  if (!stats) {
    return (
      <div className="panel stats-panel">
        <div className="panel-header">
          <h2 className="panel-title">Live Statistics</h2>
        </div>
        <div className="empty-state">
          <p>Loading statistics...</p>
        </div>
      </div>
    )
  }

  const getRiskClass = (level) => {
    if (level >= 10) return 'critical'
    if (level >= 5) return 'high'
    if (level >= 2) return 'moderate'
    return 'low'
  }

  // Handle back to overview
  const handleBack = () => {
    setSelectedView(null)
  }

  // Handle configuration save
  const handleConfigSave = (config) => {
    console.log('Configuration saved:', modalType, config)
    // In production, send to backend: POST /api/config/{modalType}
    alert(`✓ ${modalType} configuration saved! This will be active in the next data refresh.`)
  }

  // Open configuration modal
  const openConfigModal = (type) => {
    setModalType(type)
    setModalOpen(true)
  }

  // Filter events based on selected view
  const getFilteredEvents = () => {
    if (!events) return { weather: [], social: [] }

    switch (selectedView) {
      case 'weather':
        return { weather: events.weather || [], social: [] }
      case 'social':
        return { weather: [], social: events.social || [] }
      case 'critical':
        return {
          weather: (events.weather || []).filter(e => e.risk_level === 'critical'),
          social: (events.social || []).filter(e => e.data?.urgency === 'critical')
        }
      case 'high':
        return {
          weather: (events.weather || []).filter(e => e.risk_level === 'high'),
          social: (events.social || []).filter(e => e.data?.urgency === 'high')
        }
      default:
        return events
    }
  }

  // Render drill-down view
  if (selectedView) {
    const filteredEvents = getFilteredEvents()
    const viewTitles = {
      weather: 'Weather Events',
      social: 'Social Reports',
      critical: 'Critical Risks',
      high: 'High Risks'
    }

    return (
      <div className="panel stats-panel stats-detail-view">
        <div className="panel-header">
          <button className="back-button" onClick={handleBack}>
            ← Back
          </button>
          <h2 className="panel-title">{viewTitles[selectedView]}</h2>
        </div>
        <EventFeed events={filteredEvents} onViewLocation={onViewLocation} />
      </div>
    )
  }

  // Use actual event counts instead of cached stats for consistency
  const actualWeatherCount = events?.weather?.length || 0
  const actualSocialCount = events?.social?.length || 0
  const actualCriticalWeatherCount = (events?.weather || []).filter(e => e.risk_level === 'critical').length
  const actualCriticalSocialCount = (events?.social || []).filter(e => e.data?.urgency === 'critical').length
  const actualHighWeatherCount = (events?.weather || []).filter(e => e.risk_level === 'high').length
  const actualHighSocialCount = (events?.social || []).filter(e => e.data?.urgency === 'high').length

  // Data sources configuration
  const dataSources = [
    { name: 'Tomorrow.io', type: 'Weather API', status: 'active', events: actualWeatherCount },
    { name: 'Confluent Cloud', type: 'Stream Processing', status: 'active', events: actualWeatherCount + actualSocialCount },
    { name: 'Social Signals', type: 'Crisis Reports', status: 'active', events: actualSocialCount },
    { name: '911 Emergency', type: 'Emergency Calls', status: 'inactive', events: 0 },
    { name: 'NOAA Alerts', type: 'Weather Service', status: 'inactive', events: 0 },
  ]

  // Render overview with clickable stat cards
  return (
    <div className="panel stats-panel">
      <div className="panel-header">
        <h2 className="panel-title">Live Statistics</h2>
      </div>

      {/* Breaking Updates Card */}
      <BreakingUpdates events={events} onViewLocation={onViewLocation} />

      <div className="stat-grid">
        {/* Weather Stats - Clickable */}
        <button
          className={`stat-card stat-card-clickable ${getRiskClass(actualWeatherCount)}`}
          onClick={() => setSelectedView('weather')}
        >
          <div className="stat-label">Weather Events</div>
          <div className={`stat-value ${getRiskClass(actualWeatherCount)}`}>
            {actualWeatherCount}
          </div>
          <div className="stat-action">View Details →</div>
        </button>

        {/* Social Stats - Clickable */}
        <button
          className={`stat-card stat-card-clickable ${getRiskClass(actualSocialCount)}`}
          onClick={() => setSelectedView('social')}
        >
          <div className="stat-label">Social Reports</div>
          <div className={`stat-value ${getRiskClass(actualSocialCount)}`}>
            {actualSocialCount}
          </div>
          <div className="stat-action">View Details →</div>
        </button>

        {/* Critical Risks - Clickable */}
        <button
          className="stat-card stat-card-clickable critical"
          onClick={() => setSelectedView('critical')}
        >
          <div className="stat-label">Critical Risks</div>
          <div className="stat-value critical">
            {actualCriticalWeatherCount + actualCriticalSocialCount}
          </div>
          <div className="stat-action">View Details →</div>
        </button>

        {/* High Risks - Clickable */}
        <button
          className="stat-card stat-card-clickable high"
          onClick={() => setSelectedView('high')}
        >
          <div className="stat-label">High Risks</div>
          <div className="stat-value high">
            {actualHighWeatherCount + actualHighSocialCount}
          </div>
          <div className="stat-action">View Details →</div>
        </button>
      </div>

      {/* Quick Summary */}
      <div className="stat-summary">
        <div className="summary-item">
          <span className="summary-label">Total Events</span>
          <span className="summary-value">
            {actualWeatherCount + actualSocialCount}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Last Update</span>
          <span className="summary-value">
            {new Date(stats.cache_time).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Data Sources / Connectors */}
      <div className="data-sources-section">
        <div className="section-header">
          <h3>DATA SOURCES</h3>
          <button className="btn-add-source" onClick={() => openConfigModal('datasource')}>+ ADD</button>
        </div>
        <div className="sources-list">
          {dataSources.map((source, idx) => (
            <div key={idx} className={`source-item ${source.status}`}>
              <div className="source-info">
                <span className={`source-status ${source.status}`}></span>
                <div className="source-name">{source.name}</div>
                <div className="source-type">{source.type}</div>
              </div>
              <div className="source-stats">
                {source.status === 'active' ? (
                  <span className="source-count">{source.events}</span>
                ) : (
                  <span className="source-inactive">OFFLINE</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration Modal */}
      <ConfigModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        type={modalType}
        onSave={handleConfigSave}
      />
    </div>
  )
}

export default StatsPanel
