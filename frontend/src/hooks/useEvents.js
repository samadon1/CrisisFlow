import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function useEvents() {
  const [events, setEvents] = useState({ weather: [], social: [] })
  const [hotspots, setHotspots] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch events, hotspots, and stats in parallel
      // Request 300 events to show more data
      const [eventsRes, hotspotsRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/events?limit=300`),
        axios.get(`${API_BASE}/hotspots`),
        axios.get(`${API_BASE}/stats`)
      ])

      setEvents(eventsRes.data)
      setHotspots(hotspotsRes.data.hotspots || [])
      setStats(statsRes.data)
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Return data and controls
  return {
    events,
    hotspots,
    stats,
    loading,
    error,
    refreshData: fetchData
  }
}

export default useEvents