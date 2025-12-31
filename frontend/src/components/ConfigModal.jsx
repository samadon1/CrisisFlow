import React, { useState } from 'react'
import './ConfigModal.css'

function ConfigModal({ isOpen, onClose, type, currentConfig, onSave }) {
  const [config, setConfig] = useState(currentConfig || getDefaultConfig(type))
  const [activeSection, setActiveSection] = useState(getDefaultSection(type))

  if (!isOpen) return null

  function getDefaultConfig(type) {
    switch (type) {
      case 'datasource':
        return { name: '', type: '', apiKey: '', endpoint: '', enabled: true }
      case 'location':
        return { name: '', lat: '', lon: '', radius: 50, priority: 'normal' }
      case 'social':
        return { keywords: [], hashtags: [], languages: ['en'], sentiment: 'all' }
      default:
        return {}
    }
  }

  function getDefaultSection(type) {
    return type === 'datasource' ? 'select' : 'form'
  }

  const handleSave = () => {
    onSave(config)
    onClose()
  }

  const renderDataSourceConfig = () => {
    if (activeSection === 'select') {
      const dataSources = [
        { id: '911', name: '911 Emergency Calls', icon: '🚨', type: 'emergency', description: 'Real-time 911 call data integration' },
        { id: 'noaa', name: 'NOAA Weather Alerts', icon: '🌪️', type: 'weather', description: 'National Weather Service warnings and watches' },
        { id: 'usgs', name: 'USGS Earthquake Data', icon: '🌍', type: 'seismic', description: 'Real-time earthquake monitoring' },
        { id: 'fire', name: 'Fire Department CAD', icon: '🚒', type: 'emergency', description: 'Computer-Aided Dispatch system integration' },
        { id: 'iot', name: 'IoT Sensors', icon: '📡', type: 'sensor', description: 'Environmental sensors and monitoring stations' },
        { id: 'traffic', name: 'Traffic Cameras', icon: '🚦', type: 'infrastructure', description: 'Live traffic and road condition monitoring' }
      ]

      return (
        <div className="datasource-grid">
          {dataSources.map(source => (
            <button
              key={source.id}
              className="datasource-card"
              onClick={() => {
                setConfig({ ...config, type: source.id, name: source.name })
                setActiveSection('form')
              }}
            >
              <div className="datasource-icon">{source.icon}</div>
              <div className="datasource-name">{source.name}</div>
              <div className="datasource-desc">{source.description}</div>
            </button>
          ))}
        </div>
      )
    }

    return (
      <div className="config-form">
        <button className="back-btn" onClick={() => setActiveSection('select')}>
          ← Back to Selection
        </button>

        <div className="form-group">
          <label>Data Source Name</label>
          <input
            type="text"
            value={config.name}
            onChange={(e) => setConfig({ ...config, name: e.target.value })}
            placeholder="e.g., Los Angeles 911"
          />
        </div>

        <div className="form-group">
          <label>API Endpoint</label>
          <input
            type="text"
            value={config.endpoint}
            onChange={(e) => setConfig({ ...config, endpoint: e.target.value })}
            placeholder="https://api.example.com/v1"
          />
        </div>

        <div className="form-group">
          <label>API Key (Optional)</label>
          <input
            type="password"
            value={config.apiKey}
            onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
            placeholder="Enter API key if required"
          />
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
            />
            <span>Enable immediately after saving</span>
          </label>
        </div>
      </div>
    )
  }

  const renderLocationConfig = () => (
    <div className="config-form">
      <div className="form-group">
        <label>City/Location Name</label>
        <input
          type="text"
          value={config.name}
          onChange={(e) => setConfig({ ...config, name: e.target.value })}
          placeholder="e.g., Miami, Florida"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Latitude</label>
          <input
            type="number"
            step="0.000001"
            value={config.lat}
            onChange={(e) => setConfig({ ...config, lat: e.target.value })}
            placeholder="25.7617"
          />
        </div>

        <div className="form-group">
          <label>Longitude</label>
          <input
            type="number"
            step="0.000001"
            value={config.lon}
            onChange={(e) => setConfig({ ...config, lon: e.target.value })}
            placeholder="-80.1918"
          />
        </div>
      </div>

      <div className="form-group">
        <label>Monitoring Radius (km)</label>
        <input
          type="number"
          value={config.radius}
          onChange={(e) => setConfig({ ...config, radius: parseInt(e.target.value) })}
        />
      </div>

      <div className="form-group">
        <label>Priority Level</label>
        <select
          value={config.priority}
          onChange={(e) => setConfig({ ...config, priority: e.target.value })}
        >
          <option value="critical">Critical (High density population)</option>
          <option value="high">High (Major city)</option>
          <option value="normal">Normal (Standard monitoring)</option>
          <option value="low">Low (Rural area)</option>
        </select>
      </div>
    </div>
  )

  const renderSocialConfig = () => (
    <div className="config-form">
      <div className="form-group">
        <label>Keywords (comma-separated)</label>
        <textarea
          value={(config.keywords || []).join(', ')}
          onChange={(e) => setConfig({ ...config, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) })}
          placeholder="flood, emergency, evacuation, disaster"
          rows="3"
        />
        <small>Track social media posts containing these keywords</small>
      </div>

      <div className="form-group">
        <label>Hashtags (comma-separated, without #)</label>
        <textarea
          value={(config.hashtags || []).join(', ')}
          onChange={(e) => setConfig({ ...config, hashtags: e.target.value.split(',').map(h => h.trim()).filter(Boolean) })}
          placeholder="hurricane, wildfire, earthquake, emergency"
          rows="3"
        />
        <small>Monitor these hashtags for crisis-related posts</small>
      </div>

      <div className="form-group">
        <label>Languages</label>
        <div className="checkbox-group">
          {['en', 'es', 'fr', 'de'].map(lang => (
            <label key={lang} className="checkbox-label">
              <input
                type="checkbox"
                checked={config.languages.includes(lang)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig({ ...config, languages: [...config.languages, lang] })
                  } else {
                    setConfig({ ...config, languages: config.languages.filter(l => l !== lang) })
                  }
                }}
              />
              <span>{lang.toUpperCase()}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Sentiment Filter</label>
        <select
          value={config.sentiment}
          onChange={(e) => setConfig({ ...config, sentiment: e.target.value })}
        >
          <option value="all">All Posts</option>
          <option value="negative">Negative Only (Disasters, emergencies)</option>
          <option value="urgent">Urgent Only (Help needed, SOS)</option>
        </select>
      </div>
    </div>
  )

  const getTitle = () => {
    switch (type) {
      case 'datasource':
        return activeSection === 'select' ? 'Add Data Source' : 'Configure Data Source'
      case 'location':
        return 'Add Monitoring Location'
      case 'social':
        return 'Configure Social Media Monitoring'
      default:
        return 'Configuration'
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{getTitle()}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {type === 'datasource' && renderDataSourceConfig()}
          {type === 'location' && renderLocationConfig()}
          {type === 'social' && renderSocialConfig()}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfigModal
