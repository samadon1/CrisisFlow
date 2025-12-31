import React, { useState, useEffect } from 'react'
import Map from './components/Map'
import AlertPanel from './components/AlertPanel'
import StatsPanel from './components/StatsPanel'
import Legend from './components/Legend'
import PredictionPanel from './components/PredictionPanel'
import useEvents from './hooks/useEvents'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function App() {
  const { events, hotspots, stats, loading, error, refreshData } = useEvents()
  const [alert, setAlert] = useState(null)
  const [alertLoading, setAlertLoading] = useState(false)
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true)
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true)
  const [viewLocation, setViewLocation] = useState(null)
  const [cycling, setCycling] = useState(false)

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(refreshData, 10000)
    return () => clearInterval(interval)
  }, [])

  // Cycle cache when events reach maximum
  const cycleCache = async () => {
    setCycling(true)
    try {
      const response = await fetch(`${API_BASE}/cache/cycle?keep_percentage=0.1`, {
        method: 'POST'
      })
      if (response.ok) {
        // Refresh data after cycling
        setTimeout(() => refreshData(), 500)
      }
    } catch (err) {
      console.error('Error cycling cache:', err)
    } finally {
      setCycling(false)
    }
  }

  // Check if we need to auto-cycle (when events reach 280+)
  useEffect(() => {
    const totalEvents = (events?.weather?.length || 0) + (events?.social?.length || 0)
    if (totalEvents >= 580) {  // Close to 300 each
      console.log('Auto-cycling cache due to high event count:', totalEvents)
      cycleCache()
    }
  }, [events])

  const generateAlert = async () => {
    setAlertLoading(true)
    try {
      const response = await fetch(`${API_BASE}/alert/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ include_recommendations: true })
      })
      const data = await response.json()
      setAlert(data)
    } catch (err) {
      console.error('Error generating alert:', err)
    } finally {
      setAlertLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>CrisisFlow</h1>
          <span className="tagline">Real-time Disaster Intelligence Platform</span>
        </div>
        <div className="header-status">
          {((events?.weather?.length || 0) >= 250 || (events?.social?.length || 0) >= 250) && (
            <button
              className="cycle-button"
              onClick={cycleCache}
              disabled={cycling}
              title="Reset event cache to simulate fresh crisis data"
              style={{
                padding: '6px 12px',
                marginRight: '10px',
                backgroundColor: cycling ? '#666' : '#ff6b6b',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.75rem',
                cursor: cycling ? 'wait' : 'pointer',
                fontWeight: '600'
              }}
            >
              {cycling ? '⟳ CYCLING...' : '🔄 RESET DATA'}
            </button>
          )}
          <span className={`status-indicator ${loading ? 'loading' : 'live'}`}>
            {loading ? '⟳ UPDATING' : '● LIVE'}
          </span>
          {error && <span className="error-badge">Connection Error</span>}
        </div>
      </header>

      <main className="main-content">
        {leftSidebarOpen && (
          <aside className="sidebar sidebar-left">
            <StatsPanel stats={stats} events={events} onViewLocation={setViewLocation} />
            <PredictionPanel />
          </aside>
        )}

        <button
          className={`sidebar-toggle sidebar-toggle-left ${leftSidebarOpen ? 'open' : 'closed'}`}
          onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          title={leftSidebarOpen ? 'Hide Data Panel' : 'Show Data Panel'}
        >
          {leftSidebarOpen ? '◀' : '▶'}
        </button>

        <div className="map-section">
          <Map
            events={events}
            hotspots={hotspots}
            loading={loading}
            viewLocation={viewLocation}
          />
          <Legend />
        </div>

        <button
          className={`sidebar-toggle sidebar-toggle-right ${rightSidebarOpen ? 'open' : 'closed'}`}
          onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
          title={rightSidebarOpen ? 'Hide AI Panel' : 'Show AI Panel'}
        >
          {rightSidebarOpen ? '▶' : '◀'}
        </button>

        {rightSidebarOpen && (
          <aside className="sidebar sidebar-right">
            <AlertPanel
              alert={alert}
              loading={alertLoading}
              onGenerateAlert={generateAlert}
              events={events}
              stats={stats}
            />
          </aside>
        )}
      </main>

      <footer className="footer">
        <p>Built for emergency responders worldwide • Data from Tomorrow.io & Confluent</p>
      </footer>
    </div>
  )
}

export default App