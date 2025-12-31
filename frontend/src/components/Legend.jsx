import React from 'react'

function Legend() {
  return (
    <div className="map-legend" style={{
      position: 'absolute',
      bottom: '10px',
      left: '10px',
      background: 'rgba(13, 15, 18, 0.85)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '4px',
      padding: '0.5rem 0.75rem',
      color: 'white',
      zIndex: 2000,
      backdropFilter: 'blur(8px)',
      fontSize: '0.7rem',
      fontFamily: 'var(--font-mono)'
    }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        {/* Marker types */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#ff4444'
            }}></span>
            <span style={{ fontSize: '0.65rem', color: 'rgba(255, 255, 255, 0.6)' }}>Fire</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#4488ff'
            }}></span>
            <span style={{ fontSize: '0.65rem', color: 'rgba(255, 255, 255, 0.6)' }}>Flood</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#ff8844'
            }}></span>
            <span style={{ fontSize: '0.65rem', color: 'rgba(255, 255, 255, 0.6)' }}>Social</span>
          </div>
        </div>

        {/* Divider */}
        <div style={{ width: '1px', height: '16px', background: 'rgba(255, 255, 255, 0.1)' }}></div>

        {/* Risk levels */}
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <span style={{
            padding: '0.125rem 0.375rem',
            borderRadius: '2px',
            background: 'rgba(255, 0, 0, 0.15)',
            border: '1px solid rgba(255, 0, 0, 0.3)',
            fontSize: '0.6rem',
            color: '#ff5555'
          }}>CRIT</span>
          <span style={{
            padding: '0.125rem 0.375rem',
            borderRadius: '2px',
            background: 'rgba(255, 102, 0, 0.15)',
            border: '1px solid rgba(255, 102, 0, 0.3)',
            fontSize: '0.6rem',
            color: '#ff8844'
          }}>HIGH</span>
          <span style={{
            padding: '0.125rem 0.375rem',
            borderRadius: '2px',
            background: 'rgba(255, 170, 0, 0.15)',
            border: '1px solid rgba(255, 170, 0, 0.3)',
            fontSize: '0.6rem',
            color: '#ffaa44'
          }}>MOD</span>
          <span style={{
            padding: '0.125rem 0.375rem',
            borderRadius: '2px',
            background: 'rgba(0, 170, 0, 0.15)',
            border: '1px solid rgba(0, 170, 0, 0.3)',
            fontSize: '0.6rem',
            color: '#55cc55'
          }}>LOW</span>
        </div>
      </div>
    </div>
  )
}

export default Legend