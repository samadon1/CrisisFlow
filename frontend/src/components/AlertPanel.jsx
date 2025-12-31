import React, { useState, useEffect } from 'react'
import './AlertPanel.css'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function AlertPanel({ alert, loading, onGenerateAlert, events, stats }) {
  const [showChat, setShowChat] = useState(false) // Toggle between overview and chat
  const [escalationWarning, setEscalationWarning] = useState(null)
  const [dispatchStatus, setDispatchStatus] = useState({}) // Track dispatch actions
  const [dispatchTimestamps, setDispatchTimestamps] = useState({}) // Track completion times
  const [chatMessages, setChatMessages] = useState([]) // Q&A chat history
  const [chatInput, setChatInput] = useState('') // Current question
  const [chatLoading, setChatLoading] = useState(false) // AI thinking
  const [activityLog, setActivityLog] = useState([]) // Activity audit trail
  const [activityLogExpanded, setActivityLogExpanded] = useState(true) // Collapsible state
  const [actionsExpanded, setActionsExpanded] = useState(true) // IMMEDIATE ACTIONS accordion (default: open)
  const [predictionsExpanded, setPredictionsExpanded] = useState(true) // PREDICTIONS accordion (default: open)

  // Auto-refresh alert every 5 minutes (but not on initial mount)
  useEffect(() => {
    // Don't auto-generate on mount - let user trigger it manually
    // This prevents the 23-second delay on page load

    // Set up auto-refresh every 5 minutes after first generation
    let interval
    if (alert) {
      interval = setInterval(() => {
        onGenerateAlert()
      }, 5 * 60 * 1000) // 5 minutes
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [alert]) // Re-run when alert changes

  // Detect escalation patterns
  useEffect(() => {
    if (!events || !events.weather || !events.social) return

    const criticalWeather = events.weather.filter(e =>
      e.risk_level === 'critical' || e.risk_level === 'high'
    ).length

    const criticalSocial = events.social.filter(e =>
      e.data?.urgency === 'critical' || e.data?.urgency === 'high'
    ).length

    if (criticalWeather >= 1 && criticalSocial >= 2) {
      setEscalationWarning({
        severity: 'critical',
        message: 'ESCALATION DETECTED',
        details: `${criticalWeather} weather risk${criticalWeather > 1 ? 's' : ''} + ${criticalSocial} critical report${criticalSocial > 1 ? 's' : ''}`
      })
    } else if (criticalWeather + criticalSocial >= 3) {
      setEscalationWarning({
        severity: 'high',
        message: 'ELEVATED RISK',
        details: `${criticalWeather + criticalSocial} high-priority signals detected`
      })
    } else {
      setEscalationWarning(null)
    }
  }, [events])

  // Add activity to log
  const logActivity = (type, description, details = null) => {
    const activity = {
      id: Date.now(),
      timestamp: new Date(),
      type, // 'dispatch', 'evacuation', 'report', 'chat'
      description,
      details
    }
    setActivityLog(prev => [activity, ...prev]) // Newest first
  }

  // Wrapper for generating alert with logging
  const handleGenerateAlert = async () => {
    await onGenerateAlert()
    // Log after generation completes
    setTimeout(() => {
      logActivity('report', 'AI situation report generated', { source: 'Gemini AI' })
    }, 500)
  }

  // Handle resource dispatch action
  const handleDispatch = async (resource) => {
    setDispatchStatus(prev => ({ ...prev, [resource.resource]: 'dispatching' }))

    try {
      // In production, this would call your dispatch API
      // await fetch('/api/dispatch/resource', { method: 'POST', body: JSON.stringify(resource) })

      console.log('[DISPATCH]', resource)

      // Simulate dispatch notification
      setTimeout(() => {
        setDispatchStatus(prev => ({ ...prev, [resource.resource]: 'dispatched' }))

        // Log activity
        logActivity(
          'dispatch',
          `${resource.resource} (${resource.quantity}x) dispatched to ${resource.deployment_location}`,
          { priority: resource.priority, reason: resource.reason }
        )

        // Show notification (you could use a toast library)
        alert(`✅ ${resource.resource} (x${resource.quantity}) dispatched to ${resource.deployment_location}`)

        // Reset after 3 seconds
        setTimeout(() => {
          setDispatchStatus(prev => ({ ...prev, [resource.resource]: null }))
        }, 3000)
      }, 1000)
    } catch (error) {
      console.error('Dispatch error:', error)
      setDispatchStatus(prev => ({ ...prev, [resource.resource]: 'error' }))
    }
  }

  // Handle evacuation notification
  const handleEvacuationAlert = async (zone) => {
    setDispatchStatus(prev => ({ ...prev, [zone.location]: 'notifying' }))

    try {
      // In production: POST /api/notifications/evacuation
      console.log('[EVACUATION ALERT]', zone)

      setTimeout(() => {
        setDispatchStatus(prev => ({ ...prev, [zone.location]: 'notified' }))

        // Log activity
        logActivity(
          'evacuation',
          `Evacuation alert sent to ${zone.location} (${zone.estimated_population.toLocaleString()} residents)`,
          { priority: zone.priority, threat: zone.primary_threat, radius: zone.radius_miles }
        )

        alert(`📢 Evacuation alert sent to ${zone.estimated_population} residents in ${zone.location}`)

        setTimeout(() => {
          setDispatchStatus(prev => ({ ...prev, [zone.location]: null }))
        }, 3000)
      }, 1000)
    } catch (error) {
      console.error('Notification error:', error)
      setDispatchStatus(prev => ({ ...prev, [zone.location]: 'error' }))
    }
  }

  // Handle AI Q&A - switches to chat view and sends message
  const handleAskQuestion = async (e) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const question = chatInput.trim()
    setChatInput('')

    // Switch to chat view
    setShowChat(true)

    // Add user message
    const userMessage = { role: 'user', content: question, timestamp: new Date() }
    setChatMessages(prev => [...prev, userMessage])

    setChatLoading(true)

    try {
      // In production: POST /api/ai/chat
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          context: {
            alert,
            events,
            stats
          }
        })
      })

      const data = await response.json()

      const aiMessage = {
        role: 'assistant',
        content: data.answer || 'I understand your question. Based on current conditions, I recommend monitoring the situation closely.',
        timestamp: new Date()
      }

      setChatMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat error:', error)

      // Fallback response
      const aiMessage = {
        role: 'assistant',
        content: 'I apologize, but I\'m having trouble processing your question right now. Please try the "GENERATE REPORT" button for comprehensive analysis, or rephrase your question.',
        timestamp: new Date()
      }

      setChatMessages(prev => [...prev, aiMessage])
    } finally {
      setChatLoading(false)
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // Fetch real predictions data
  const [realPredictions, setRealPredictions] = useState(null)

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await fetch(`${API_BASE}/predictions`)
        if (response.ok) {
          const data = await response.json()
          setRealPredictions(data)
        }
      } catch (error) {
        console.error('Error fetching predictions:', error)
      }
    }

    fetchPredictions()
    const interval = setInterval(fetchPredictions, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [])

  // Use real predictions if available, fallback to AI-generated
  const predictions = realPredictions?.predictions?.slice(0, 3).map(p => ({
    timeframe: `${p.time_horizon} minutes`,
    event: `${p.crisis_type} crisis ${p.severity === 'critical' ? 'escalation' : 'development'}`,
    probability: Math.round(p.probability),
    severity: p.severity
  })) || alert?.predictions || []

  const resourceDispatch = alert?.resource_dispatch || []
  const evacuationZones = alert?.evacuation_zones || []

  return (
    <div className="panel alert-panel">
      <div className="panel-header">
        <h2 className="panel-title">OPERATIONS CENTER</h2>
      </div>

      {/* Resource Status Bar - Enterprise Grade */}
      {!showChat && (
        <div className="resource-status-bar">
          <div className="resource-status-item">
            <div className="resource-info">
              <span className="resource-label">Fire & Rescue</span>
              <div className="resource-availability">
                <div className="resource-bar">
                  {(() => {
                    const criticalCount = (stats?.weather?.by_risk?.critical || 0) + (stats?.social?.by_urgency?.critical || 0)
                    const available = Math.max(0, 10 - Math.min(10, Math.floor(criticalCount / 2)))
                    return <div className="resource-bar-fill" style={{width: `${available * 10}%`}}></div>
                  })()}
                </div>
                <span className="resource-count">
                  {(() => {
                    const criticalCount = (stats?.weather?.by_risk?.critical || 0) + (stats?.social?.by_urgency?.critical || 0)
                    return Math.max(0, 10 - Math.min(10, Math.floor(criticalCount / 2)))
                  })()}/10
                </span>
              </div>
            </div>
          </div>
          <div className="resource-status-item">
            <div className="resource-info">
              <span className="resource-label">Medical</span>
              <div className="resource-availability">
                <div className="resource-bar">
                  {(() => {
                    const highCount = (stats?.weather?.by_risk?.high || 0) + (stats?.social?.by_urgency?.high || 0)
                    const available = Math.max(0, 7 - Math.min(7, Math.floor(highCount / 3)))
                    return <div className="resource-bar-fill" style={{width: `${available * 14.3}%`}}></div>
                  })()}
                </div>
                <span className="resource-count">
                  {(() => {
                    const highCount = (stats?.weather?.by_risk?.high || 0) + (stats?.social?.by_urgency?.high || 0)
                    return Math.max(0, 7 - Math.min(7, Math.floor(highCount / 3)))
                  })()}/7
                </span>
              </div>
            </div>
          </div>
          <div className="resource-status-item">
            <div className="resource-info">
              <span className="resource-label">Engineering</span>
              <div className="resource-availability">
                <div className="resource-bar">
                  {(() => {
                    const moderateCount = (stats?.weather?.by_risk?.moderate || 0) + (stats?.social?.by_urgency?.medium || 0)
                    const available = Math.max(0, 10 - Math.min(10, Math.floor(moderateCount / 4)))
                    return <div className="resource-bar-fill" style={{width: `${available * 10}%`}}></div>
                  })()}
                </div>
                <span className="resource-count">
                  {(() => {
                    const moderateCount = (stats?.weather?.by_risk?.moderate || 0) + (stats?.social?.by_urgency?.medium || 0)
                    return Math.max(0, 10 - Math.min(10, Math.floor(moderateCount / 4)))
                  })()}/10
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Escalation Warning */}
      {escalationWarning && (
        <div className={`ai-escalation ${escalationWarning.severity}`}>
          <div className="escalation-header">
            <span className="escalation-badge">{escalationWarning.message}</span>
            <span className="escalation-details">{escalationWarning.details}</span>
          </div>
        </div>
      )}

      {/* Conditional Content - Overview or Chat */}
      <div className="ai-content" style={{ marginBottom: !showChat ? '60px' : '0' }}>
        {!showChat ? (
          /* OVERVIEW VIEW */
          <div className="ai-overview">
            <div className="ai-section">
              <h3>SITUATION ANALYSIS</h3>
              <button
                className="btn-generate"
                onClick={handleGenerateAlert}
                disabled={loading}
              >
                {loading ? 'ANALYZING...' : 'GENERATE REPORT'}
              </button>
            </div>

            {loading && <div className="ai-loading">Processing real-time data...</div>}

            {!loading && alert && (
              <>
                <div className="ai-report">
                  <p>{alert.situation_report}</p>
                  <div className="report-meta">
                    <span className="timestamp">Updated: {formatTimestamp(alert.generated_at)}</span>
                  </div>
                </div>

                {alert.risk_summary && (
                  <div className="risk-grid">
                    <div className={`risk-cell ${alert.risk_summary.fire}`}>
                      <span className="risk-label">FIRE</span>
                      <span className="risk-value">{alert.risk_summary.fire.toUpperCase()}</span>
                    </div>
                    <div className={`risk-cell ${alert.risk_summary.flood}`}>
                      <span className="risk-label">FLOOD</span>
                      <span className="risk-value">{alert.risk_summary.flood.toUpperCase()}</span>
                    </div>
                    <div className={`risk-cell ${alert.risk_summary.overall}`}>
                      <span className="risk-label">OVERALL</span>
                      <span className="risk-value">{alert.risk_summary.overall.toUpperCase()}</span>
                    </div>
                  </div>
                )}

                {/* Response Progress Tracker */}
                {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                  <>
                    {(() => {
                      // Calculate progress
                      const totalActions = alert.recommended_actions.slice(0, 3).length
                      const completedActions = alert.recommended_actions.slice(0, 3).filter((action, idx) => {
                        const actionKey = `action-${idx}`
                        const status = dispatchStatus[actionKey]
                        return status === 'dispatched' || status === 'notified'
                      }).length
                      const inProgressActions = alert.recommended_actions.slice(0, 3).filter((action, idx) => {
                        const actionKey = `action-${idx}`
                        const status = dispatchStatus[actionKey]
                        return status === 'dispatching' || status === 'notifying'
                      }).length
                      const progressPercentage = Math.round((completedActions / totalActions) * 100)

                      return (
                        <div className="response-progress">
                          <div className="response-progress-header">
                            <h4>RESPONSE PROGRESS</h4>
                            <span className="response-progress-percentage">{progressPercentage}%</span>
                          </div>
                          <div className="response-progress-bar">
                            <div
                              className="response-progress-fill"
                              style={{width: `${progressPercentage}%`}}
                            ></div>
                          </div>
                          <div className="response-progress-stats">
                            <span className="progress-stat completed">✓ {completedActions} Completed</span>
                            {inProgressActions > 0 && (
                              <span className="progress-stat in-progress">⏳ {inProgressActions} In Progress</span>
                            )}
                            <span className="progress-stat pending">○ {totalActions - completedActions - inProgressActions} Pending</span>
                          </div>
                        </div>
                      )
                    })()}
                  </>
                )}

                {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                  <div className="ai-actions">
                    <div
                      className="accordion-header"
                      onClick={() => setActionsExpanded(!actionsExpanded)}
                    >
                      <h4>IMMEDIATE ACTIONS</h4>
                      <span className="accordion-chevron">{actionsExpanded ? '▼' : '▶'}</span>
                    </div>
                    {actionsExpanded && alert.recommended_actions.slice(0, 3).map((action, idx) => {
                      const priority = String(action.priority || 'moderate').toLowerCase()
                      const actionKey = `action-${idx}`
                      const status = dispatchStatus[actionKey]

                      // Determine action type based on content
                      const isEvacuation = action.action.toLowerCase().includes('evacuat')
                      const isDispatch = action.action.toLowerCase().includes('deploy') ||
                                        action.action.toLowerCase().includes('dispatch') ||
                                        action.action.toLowerCase().includes('mobilize')

                      return (
                        <div key={idx} className={`action-item priority-${priority}`}>
                          <span className="action-priority">{String(action.priority || 'MODERATE').toUpperCase()}</span>
                          <div className="action-content">
                            <div className="action-title">{action.action}</div>
                            <div className="action-reason">{action.reason}</div>
                          </div>

                          {/* Action button - changes based on type */}
                          {(isEvacuation || isDispatch) && (
                            <div className="action-button-wrapper">
                              <button
                                className={`action-dispatch-btn ${status || ''}`}
                                onClick={() => {
                                  if (isEvacuation && evacuationZones.length > 0) {
                                    setDispatchStatus(prev => ({ ...prev, [actionKey]: 'notifying' }))
                                    handleEvacuationAlert(evacuationZones[0])
                                    // Update to completed state and set timestamp
                                    setTimeout(() => {
                                      setDispatchStatus(prev => ({ ...prev, [actionKey]: 'notified' }))
                                      setDispatchTimestamps(prev => ({ ...prev, [actionKey]: new Date() }))
                                    }, 1000)
                                  } else if (isDispatch && resourceDispatch.length > 0) {
                                    setDispatchStatus(prev => ({ ...prev, [actionKey]: 'dispatching' }))
                                    handleDispatch(resourceDispatch[0])
                                    // Update to completed state and set timestamp
                                    setTimeout(() => {
                                      setDispatchStatus(prev => ({ ...prev, [actionKey]: 'dispatched' }))
                                      setDispatchTimestamps(prev => ({ ...prev, [actionKey]: new Date() }))
                                    }, 1000)
                                  }
                                }}
                                disabled={status === 'dispatching' || status === 'dispatched' ||
                                         status === 'notifying' || status === 'notified'}
                              >
                                {(status === 'dispatching' || status === 'notifying') && 'EXECUTING...'}
                                {(status === 'dispatched' || status === 'notified') && '✓ COMPLETED'}
                                {!status && (isEvacuation ? 'SEND ALERT' : 'DISPATCH NOW')}
                              </button>
                              {dispatchTimestamps[actionKey] && (
                                <span className="action-timestamp">
                                  Completed at {formatTimestamp(dispatchTimestamps[actionKey])}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Predictions Timeline - Integrated into OVERVIEW */}
                {predictions && predictions.length > 0 && (
                  <div className="ai-predictions-inline">
                    <div
                      className="accordion-header"
                      onClick={() => setPredictionsExpanded(!predictionsExpanded)}
                    >
                      <h4>PREDICTED TIMELINE (NEXT 6 HOURS)</h4>
                      <span className="accordion-chevron">{predictionsExpanded ? '▼' : '▶'}</span>
                    </div>
                    {predictionsExpanded && (
                      <div className="prediction-timeline">
                        {predictions.map((prediction, idx) => (
                          <div key={idx} className={`timeline-item ${prediction.severity}`}>
                            <span className="timeline-time">{prediction.timeframe}</span>
                            <span className="timeline-event">{prediction.event}</span>
                            <span className="timeline-prob">{prediction.probability}%</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {!loading && !alert && (
              <div className="ai-prompt">
                <p>Click "GENERATE REPORT" to analyze current conditions</p>
              </div>
            )}
          </div>
        ) : (
          /* CHAT VIEW */
          <div className="ai-chat">
            <div className="chat-header-with-back">
              <button className="back-to-overview-btn" onClick={() => setShowChat(false)}>
                ← Back to Overview
              </button>
              <h3>CRISISFLOW AI ASSISTANT</h3>
            </div>

            <div className="chat-messages-only">
              {chatMessages.length === 0 ? (
                <div className="chat-welcome">
                  <p>💬 Ask me anything about the current crisis situation using the input below:</p>
                  <div className="chat-suggestions">
                    <button onClick={() => setChatInput('What areas are at highest risk right now?')}>
                      What areas are at highest risk?
                    </button>
                    <button onClick={() => setChatInput('How many resources do we need?')}>
                      How many resources needed?
                    </button>
                    <button onClick={() => setChatInput('Should we evacuate any areas?')}>
                      Should we evacuate?
                    </button>
                    <button onClick={() => setChatInput('What will happen in the next 2 hours?')}>
                      Next 2 hours prediction?
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`chat-message ${msg.role}`}>
                      <div className="message-header">
                        <span className="message-role">
                          {msg.role === 'user' ? '👤 YOU' : '🤖 CRISISFLOW AI'}
                        </span>
                        <span className="message-time">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="message-content">{msg.content}</div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="chat-message assistant">
                      <div className="message-header">
                        <span className="message-role">🤖 CRISISFLOW AI</span>
                      </div>
                      <div className="message-content typing">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Activity Log - Collapsible audit trail */}
      {!showChat && (
        <div className="activity-log-container">
          <div className="activity-log-header" onClick={() => setActivityLogExpanded(!activityLogExpanded)}>
            <h4>ACTIVITY LOG</h4>
            <button className="activity-log-toggle">
              {activityLogExpanded ? '▼' : '▲'}
            </button>
          </div>

          {activityLogExpanded && (
            <div className="activity-log-content">
              {activityLog.length === 0 ? (
                <div className="activity-log-empty">
                  No activities logged yet. Actions will appear here.
                </div>
              ) : (
                <div className="activity-log-list">
                  {activityLog.slice(0, 10).map((activity) => (
                    <div key={activity.id} className={`activity-log-item activity-${activity.type}`}>
                      <span className="activity-time">{formatTimestamp(activity.timestamp)}</span>
                      <span className={`activity-type-badge ${activity.type}`}>
                        {activity.type.toUpperCase()}
                      </span>
                      <span className="activity-description">{activity.description}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Floating Q&A Input - Visible only on overview, hidden on chat */}
      {!showChat && (
        <div className="global-chat-input">
          <form onSubmit={handleAskQuestion}>
            <div className="global-input-container">
              <input
                type="text"
                className="global-ai-input"
                placeholder="Ask CrisisFlow AI anything..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
              />
              <button
                type="submit"
                className="global-send-btn"
                disabled={!chatInput.trim() || chatLoading}
              >
                {chatLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default AlertPanel
