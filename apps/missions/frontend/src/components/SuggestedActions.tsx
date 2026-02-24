import { useSuggestedActions, useUpdateSuggestedAction } from '../hooks/useMissions'
import type { SuggestedAction } from '../types'
import '../styles/SuggestedActions.css'
import { useState } from 'react'

interface SuggestedActionsProps {
  missionId: string
}

const SuggestedActions = ({ missionId }: SuggestedActionsProps) => {
  const { data: actions, isLoading } = useSuggestedActions(missionId, 'pending')
  const updateAction = useUpdateSuggestedAction()
  const [showHistory, setShowHistory] = useState(false)

  const handleAccept = async (action: SuggestedAction) => {
    await updateAction.mutateAsync({
      missionId,
      actionId: action.id,
      data: { status: 'accepted' },
    })
  }

  const handleDefer = async (action: SuggestedAction) => {
    await updateAction.mutateAsync({
      missionId,
      actionId: action.id,
      data: { status: 'deferred' },
    })
  }

  const handleDismiss = async (action: SuggestedAction) => {
    await updateAction.mutateAsync({
      missionId,
      actionId: action.id,
      data: { status: 'dismissed' },
    })
  }

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'user_action':
        return '👤'
      case 'agent_action':
        return '🤖'
      case 'info_request':
        return '📋'
      default:
        return '❓'
    }
  }

  const getPriorityClass = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'priority-high'
      case 'medium':
        return 'priority-medium'
      case 'low':
        return 'priority-low'
      default:
        return ''
    }
  }

  if (isLoading) {
    return <div className="suggested-actions-loading">Loading suggestions...</div>
  }

  // Show history view if toggled
  if (showHistory) {
    return <SuggestedActionsHistory missionId={missionId} onClose={() => setShowHistory(false)} />
  }

  return (
    <div className="suggested-actions-container">
      <div className="suggested-actions-header">
        <h3 className="suggested-actions-title">Suggested Actions</h3>
        <button
          className="btn btn-history"
          onClick={() => setShowHistory(true)}
          title="View accepted actions history"
        >
          📋 History
        </button>
      </div>

      {(!actions || actions.length === 0) ? (
        <div className="suggested-actions-placeholder">
          <div className="placeholder-icon">💡</div>
          <p className="placeholder-text">No suggestions yet</p>
          <p className="placeholder-subtext">
            Continue chatting with your agent to get actionable suggestions for your mission goals.
          </p>
        </div>
      ) : (
        <div className="suggested-actions-list">
        {actions.map((action) => (
          <div key={action.id} className="suggested-action-card">
            <div className="action-header">
              <span className="action-icon">{getActionIcon(action.type)}</span>
              <span className={`action-priority ${getPriorityClass(action.priority)}`}>
                {action.priority.toUpperCase()}
              </span>
            </div>
            <h4 className="action-title">{action.title}</h4>
            <p className="action-description">{action.description}</p>
            {action.reasoning && (
              <div className="action-reasoning">
                <strong>Why:</strong> {action.reasoning}
              </div>
            )}
            {action.related_goal && (
              <div className="action-goal">
                <strong>Related to:</strong> {action.related_goal}
              </div>
            )}
            <div className="action-buttons">
              <button
                className="btn btn-accept"
                onClick={() => handleAccept(action)}
                disabled={updateAction.isPending}
              >
                ✓ Accept
              </button>
              <button
                className="btn btn-defer"
                onClick={() => handleDefer(action)}
                disabled={updateAction.isPending}
              >
                ⏰ Defer
              </button>
              <button
                className="btn btn-dismiss"
                onClick={() => handleDismiss(action)}
                disabled={updateAction.isPending}
              >
                ✕ Dismiss
              </button>
            </div>
          </div>
        ))}
        </div>
      )}
    </div>
  )
}

// History component for viewing accepted actions
interface SuggestedActionsHistoryProps {
  missionId: string
  onClose: () => void
}

const SuggestedActionsHistory = ({ missionId, onClose }: SuggestedActionsHistoryProps) => {
  const { data: acceptedActions, isLoading } = useSuggestedActions(missionId, 'accepted')

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'user_action':
        return '👤'
      case 'agent_action':
        return '🤖'
      case 'info_request':
        return '📋'
      default:
        return '❓'
    }
  }

  return (
    <div className="suggested-actions-container">
      <div className="suggested-actions-header">
        <h3 className="suggested-actions-title">Accepted Actions History</h3>
        <button
          className="btn btn-back"
          onClick={onClose}
          title="Back to pending suggestions"
        >
          ← Back
        </button>
      </div>

      {isLoading ? (
        <div className="suggested-actions-loading">Loading history...</div>
      ) : (!acceptedActions || acceptedActions.length === 0) ? (
        <div className="suggested-actions-placeholder">
          <div className="placeholder-icon">📝</div>
          <p className="placeholder-text">No accepted actions yet</p>
          <p className="placeholder-subtext">
            Actions you accept will appear here with timestamps.
          </p>
        </div>
      ) : (
        <div className="suggested-actions-list">
          {acceptedActions.map((action) => (
            <div key={action.id} className="suggested-action-card history-card">
              <div className="action-header">
                <span className="action-icon">{getActionIcon(action.type)}</span>
                <span className="action-accepted-date">
                  ✓ Accepted: {action.accepted_at ? formatDate(action.accepted_at) : 'Unknown'}
                </span>
              </div>
              <h4 className="action-title">{action.title}</h4>
              <p className="action-description">{action.description}</p>
              {action.reasoning && (
                <div className="action-reasoning">
                  <strong>Why:</strong> {action.reasoning}
                </div>
              )}
              {action.related_goal && (
                <div className="action-goal">
                  <strong>Related to:</strong> {action.related_goal}
                </div>
              )}
              {action.completed_at && (
                <div className="action-completed">
                  <strong>✓ Completed:</strong> {formatDate(action.completed_at)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SuggestedActions
