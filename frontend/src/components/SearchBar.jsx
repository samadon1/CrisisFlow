import React, { useState } from 'react'

function SearchBar({ onLocationSelect }) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)

  // Debounced geocoding search using Nominatim (OpenStreetMap)
  const handleSearch = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 3) {
      setSuggestions([])
      return
    }

    setLoading(true)
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=5`
      )
      const data = await response.json()
      setSuggestions(data)
    } catch (error) {
      console.error('Geocoding error:', error)
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }

  // Debounce mechanism
  const debounce = (func, delay) => {
    let timeoutId
    return (...args) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => func(...args), delay)
    }
  }

  const debouncedSearch = debounce(handleSearch, 500)

  const handleInputChange = (e) => {
    const value = e.target.value
    setQuery(value)
    debouncedSearch(value)
  }

  const handleSelectLocation = (location) => {
    const lat = parseFloat(location.lat)
    const lon = parseFloat(location.lon)
    onLocationSelect(lat, lon, location.display_name)
    setQuery(location.display_name)
    setSuggestions([])
  }

  return (
    <div style={{
      position: 'absolute',
      top: '10px',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 1000,
      width: '320px',
      maxWidth: '90vw'
    }}>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder="Search location..."
          style={{
            width: '100%',
            padding: '0.5rem 0.75rem',
            background: 'rgba(13, 15, 18, 0.85)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '4px',
            fontSize: '0.7rem',
            outline: 'none',
            fontFamily: 'var(--font-mono)',
            transition: 'all 0.2s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = 'rgba(82, 148, 226, 0.4)'
          }}
          onBlur={(e) => {
            e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)'
          }}
        />
        {loading && (
          <div style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'rgba(255, 255, 255, 0.4)',
            fontSize: '0.65rem',
            fontFamily: 'var(--font-mono)'
          }}>
            ...
          </div>
        )}
      </div>

      {/* Suggestions dropdown */}
      {suggestions.length > 0 && (
        <div style={{
          marginTop: '4px',
          width: '100%',
          background: 'rgba(13, 15, 18, 0.95)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '4px',
          overflow: 'hidden',
          backdropFilter: 'blur(8px)'
        }}>
          {suggestions.map((suggestion, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectLocation(suggestion)}
              style={{
                padding: '0.5rem 0.75rem',
                cursor: 'pointer',
                borderBottom: idx < suggestions.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                transition: 'background 0.15s ease',
                fontSize: '0.65rem',
                color: 'rgba(255, 255, 255, 0.8)',
                fontFamily: 'var(--font-mono)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'rgba(82, 148, 226, 0.15)'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
              }}
            >
              {suggestion.display_name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SearchBar
