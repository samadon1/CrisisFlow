import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function PredictionPanel() {
  const [predictions, setPredictions] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('predictions')

  useEffect(() => {
    fetchPredictions()
    const interval = setInterval(fetchPredictions, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchPredictions = async () => {
    try {
      const response = await fetch(`${API_BASE}/predictions`)
      if (response.ok) {
        const data = await response.json()
        setPredictions(data)
      }

      // Also fetch stream metrics
      const metricsResponse = await fetch(`${API_BASE}/metrics`)
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json()
        setMetrics(metricsData)
      }

      setLoading(false)
    } catch (error) {
      console.error('Error fetching predictions:', error)
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'critical': return '#ff4444'
      case 'high': return '#ff8844'
      case 'moderate': return '#ffaa44'
      case 'low': return '#44cc44'
      default: return '#666'
    }
  }

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'escalating_rapidly': return '⚠️ ↑↑'
      case 'escalating': return '↑'
      case 'stable': return '→'
      case 'decreasing': return '↓'
      default: return '?'
    }
  }

  if (loading) {
    return (
      <div className="prediction-panel">
        <div className="section-header">
          <span className="section-title">Crisis Predictions</span>
        </div>
        <div className="loading">Loading predictions...</div>
      </div>
    )
  }

  return (
    <div className="prediction-panel" style={{
      backgroundColor: 'rgba(13, 15, 18, 0.95)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '8px',
      padding: '1rem',
      marginTop: '1rem',
      fontFamily: 'var(--font-mono)',
      backdropFilter: 'blur(20px)'
    }}>
      <div className="section-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span className="section-title" style={{
          fontSize: '0.8rem',
          fontWeight: '600',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'rgba(255, 255, 255, 0.5)'
        }}>Predictive Analysis</span>

        <div className="tab-buttons" style={{
          display: 'flex',
          gap: '0.5rem'
        }}>
          <button
            onClick={() => setActiveTab('predictions')}
            style={{
              padding: '0.25rem 0.75rem',
              fontSize: '0.7rem',
              backgroundColor: activeTab === 'predictions' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              border: `1px solid ${activeTab === 'predictions' ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
              borderRadius: '4px',
              color: activeTab === 'predictions' ? '#3b82f6' : 'rgba(255, 255, 255, 0.5)',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Predictions
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            style={{
              padding: '0.25rem 0.75rem',
              fontSize: '0.7rem',
              backgroundColor: activeTab === 'analytics' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              border: `1px solid ${activeTab === 'analytics' ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
              borderRadius: '4px',
              color: activeTab === 'analytics' ? '#3b82f6' : 'rgba(255, 255, 255, 0.5)',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Stream Analytics
          </button>
        </div>
      </div>

      {activeTab === 'predictions' && predictions && (
        <div>
          {/* Current Trend */}
          <div style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '6px',
            marginBottom: '1rem'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem'
            }}>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.5)' }}>Current Trend</span>
              <span style={{ fontSize: '0.9rem' }}>
                {getTrendIcon(predictions.metrics?.trend)}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.7rem' }}>
              <div>
                <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Velocity: </span>
                <span style={{ color: '#3b82f6' }}>{predictions.metrics?.velocity || 0} events/min</span>
              </div>
              <div>
                <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Hotspots: </span>
                <span style={{ color: '#ff8844' }}>{predictions.metrics?.hotspot_count || 0}</span>
              </div>
            </div>
          </div>

          {/* Time Horizon Predictions */}
          {predictions.predictions?.map((pred, idx) => (
            <div key={idx} style={{
              padding: '0.75rem',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '6px',
              marginBottom: '0.75rem'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.5rem'
              }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '600' }}>
                  {pred.time_horizon} Minute Outlook
                </span>
                <span style={{
                  fontSize: '0.65rem',
                  padding: '0.125rem 0.5rem',
                  borderRadius: '3px',
                  backgroundColor: `${getSeverityColor(pred.severity)}22`,
                  color: getSeverityColor(pred.severity),
                  border: `1px solid ${getSeverityColor(pred.severity)}44`
                }}>
                  {pred.severity.toUpperCase()}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.65rem' }}>
                <div>
                  <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Probability: </span>
                  <span style={{ color: pred.probability > 50 ? '#ff8844' : '#44cc44' }}>
                    {pred.probability}%
                  </span>
                </div>
                <div>
                  <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Confidence: </span>
                  <span>{pred.confidence}%</span>
                </div>
                <div>
                  <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Affected Pop: </span>
                  <span>{pred.affected_population?.toLocaleString() || 0}</span>
                </div>
                <div>
                  <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Type: </span>
                  <span>{pred.crisis_type}</span>
                </div>
              </div>

              {pred.key_factors && pred.key_factors.length > 0 && (
                <div style={{
                  marginTop: '0.5rem',
                  padding: '0.5rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '4px',
                  fontSize: '0.6rem'
                }}>
                  <div style={{ color: 'rgba(255, 255, 255, 0.5)', marginBottom: '0.25rem' }}>Key Factors:</div>
                  {pred.key_factors.map((factor, i) => (
                    <div key={i} style={{ color: 'rgba(255, 255, 255, 0.7)' }}>• {factor}</div>
                  ))}
                </div>
              )}

              {pred.recommended_actions && pred.recommended_actions.length > 0 && (
                <div style={{
                  marginTop: '0.5rem',
                  padding: '0.5rem',
                  backgroundColor: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '4px',
                  fontSize: '0.6rem'
                }}>
                  <div style={{ color: '#3b82f6', marginBottom: '0.25rem' }}>Recommended Actions:</div>
                  {pred.recommended_actions.map((action, i) => (
                    <div key={i} style={{ color: 'rgba(255, 255, 255, 0.7)' }}>✓ {action}</div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Top Hotspots */}
          {predictions.hotspots && predictions.hotspots.length > 0 && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: 'rgba(255, 68, 68, 0.05)',
              border: '1px solid rgba(255, 68, 68, 0.2)',
              borderRadius: '6px',
              marginTop: '1rem'
            }}>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: '600',
                color: '#ff4444',
                marginBottom: '0.5rem'
              }}>
                Geographic Hotspots
              </div>
              {predictions.hotspots.slice(0, 3).map((hotspot, idx) => (
                <div key={idx} style={{
                  fontSize: '0.65rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.25rem 0',
                  borderBottom: idx < 2 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
                }}>
                  <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                    {hotspot.lat.toFixed(2)}°, {hotspot.lon.toFixed(2)}°
                  </span>
                  <span style={{ color: '#ff8844' }}>
                    {hotspot.event_count} events • {hotspot.primary_type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && metrics && (
        <div>
          {/* Real-time Metrics */}
          <div style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '6px',
            marginBottom: '1rem'
          }}>
            <div style={{
              fontSize: '0.75rem',
              fontWeight: '600',
              marginBottom: '0.75rem',
              color: 'rgba(255, 255, 255, 0.7)'
            }}>
              Real-time Processing Metrics
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={{ fontSize: '0.65rem' }}>
                <div style={{ color: 'rgba(255, 255, 255, 0.4)', marginBottom: '0.25rem' }}>Events/Second</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#3b82f6' }}>
                  {metrics.current?.events_per_second || 0}
                </div>
                <div style={{ fontSize: '0.6rem', color: 'rgba(255, 255, 255, 0.3)' }}>
                  Peak: {metrics.current?.peak_events_per_second || 0}
                </div>
              </div>

              <div style={{ fontSize: '0.65rem' }}>
                <div style={{ color: 'rgba(255, 255, 255, 0.4)', marginBottom: '0.25rem' }}>Latency</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#44cc44' }}>
                  {metrics.current?.processing_latency_ms || 0}ms
                </div>
                <div style={{ fontSize: '0.6rem', color: 'rgba(255, 255, 255, 0.3)' }}>
                  Avg processing time
                </div>
              </div>

              <div style={{ fontSize: '0.65rem' }}>
                <div style={{ color: 'rgba(255, 255, 255, 0.4)', marginBottom: '0.25rem' }}>Total Processed</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#ff8844' }}>
                  {(metrics.current?.total_events_processed || 0).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.6rem', color: 'rgba(255, 255, 255, 0.3)' }}>
                  Events since startup
                </div>
              </div>

              <div style={{ fontSize: '0.65rem' }}>
                <div style={{ color: 'rgba(255, 255, 255, 0.4)', marginBottom: '0.25rem' }}>Accuracy</div>
                <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#ffaa44' }}>
                  {metrics.current?.accuracy_score || 0}%
                </div>
                <div style={{ fontSize: '0.6rem', color: 'rgba(255, 255, 255, 0.3)' }}>
                  Prediction accuracy
                </div>
              </div>
            </div>

            <div style={{
              marginTop: '0.75rem',
              padding: '0.5rem',
              backgroundColor: 'rgba(59, 130, 246, 0.05)',
              borderRadius: '4px',
              fontSize: '0.65rem',
              color: '#3b82f6'
            }}>
              Predicting {metrics.current?.predictions_ahead_minutes || 30} minutes ahead
            </div>
          </div>

          {/* Streaming vs Batch Comparison */}
          <div style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(68, 204, 68, 0.05)',
            border: '1px solid rgba(68, 204, 68, 0.2)',
            borderRadius: '6px'
          }}>
            <div style={{
              fontSize: '0.7rem',
              fontWeight: '600',
              color: '#44cc44',
              marginBottom: '0.5rem'
            }}>
              Streaming Advantages
            </div>
            {metrics.performance_vs_batch && Object.entries(metrics.performance_vs_batch).map(([key, value]) => (
              <div key={key} style={{
                fontSize: '0.65rem',
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.35rem 0',
                borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
              }}>
                <span style={{ color: 'rgba(255, 255, 255, 0.5)', textTransform: 'capitalize' }}>
                  {key.replace(/_/g, ' ')}:
                </span>
                <span style={{ color: '#44cc44', fontWeight: '500' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PredictionPanel