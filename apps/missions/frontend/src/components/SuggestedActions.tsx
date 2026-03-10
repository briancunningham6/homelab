import { useSuggestedActions, useUpdateSuggestedAction } from '../hooks/useMissions'
import type { SuggestedAction } from '../types'
import '../styles/SuggestedActions.css'
import { useState, useRef, useEffect } from 'react'

interface SuggestedActionsProps {
  missionId: string
  onSendToChat?: (message: string) => void
  onCollapse?: () => void
}

const SuggestedActions = ({ missionId, onSendToChat, onCollapse }: SuggestedActionsProps) => {
  const { data: actions, isLoading } = useSuggestedActions(missionId, 'pending')
  const updateAction = useUpdateSuggestedAction()
  const [showHistory, setShowHistory] = useState(false)
  const [expandedActionId, setExpandedActionId] = useState<string | null>(null)
  const [responseText, setResponseText] = useState('')
  const responseTextareaRef = useRef<HTMLTextAreaElement>(null)

  // Focus textarea when a card expands
  useEffect(() => {
    if (expandedActionId) {
      setTimeout(() => responseTextareaRef.current?.focus(), 50)
    }
  }, [expandedActionId])

  const getResponsePlaceholder = (type: string) => {
    switch (type) {
      case 'info_request':
        return 'Provide the requested information...'
      case 'agent_action':
        return 'Any specific instructions for the agent? (optional)'
      default:
        return 'Add any details about how you\'re handling this... (optional)'
    }
  }

  const buildChatMessage = (action: SuggestedAction, response: string): string => {
    const base = `I've accepted the suggestion: "${action.title}"`
    return response.trim() ? `${base}\n\n${response.trim()}` : base
  }

  const handleAcceptClick = (action: SuggestedAction) => {
    setExpandedActionId(action.id)
    setResponseText('')
  }

  const handleSubmitWithResponse = async (action: SuggestedAction) => {
    await updateAction.mutateAsync({
      missionId,
      actionId: action.id,
      data: { status: 'accepted' },
    })
    onSendToChat?.(buildChatMessage(action, responseText))
    setExpandedActionId(null)
    setResponseText('')
  }

  const handleSkipAndAccept = async (action: SuggestedAction) => {
    await updateAction.mutateAsync({
      missionId,
      actionId: action.id,
      data: { status: 'accepted' },
    })
    setExpandedActionId(null)
    setResponseText('')
  }

  const handleCancelExpand = () => {
    setExpandedActionId(null)
    setResponseText('')
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
        <h3 className="suggested-actions-title">Suggestions</h3>
        <div className="suggested-actions-header-btns">
          <button
            className="btn btn-history"
            onClick={() => setShowHistory(true)}
            title="View accepted actions history"
          >
            📋
          </button>
          {onCollapse && (
            <button
              className="btn btn-collapse-suggestions"
              onClick={onCollapse}
              title="Hide Suggested Actions"
            >
              ✕
            </button>
          )}
        </div>
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
            {action.creates_task && (
              <div className="action-creates-task" title={action.task_due_date ? `Accepting will create a task due ${action.task_due_date}` : 'Accepting will add this to your task list'}>
                📋 Creates task{action.task_due_date ? ` · due ${action.task_due_date}` : ''}
              </div>
            )}
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

            {expandedActionId === action.id ? (
              <div className="action-response-form">
                <label className="action-response-label">
                  {action.type === 'info_request'
                    ? 'Your response:'
                    : 'Add a comment (optional):'}
                </label>
                <textarea
                  ref={responseTextareaRef}
                  className="action-response-textarea"
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  placeholder={getResponsePlaceholder(action.type)}
                  rows={3}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      e.preventDefault()
                      handleSubmitWithResponse(action)
                    }
                    if (e.key === 'Escape') handleCancelExpand()
                  }}
                />
                <div className="action-response-buttons">
                  <button
                    className="btn btn-cancel-response"
                    onClick={handleCancelExpand}
                    disabled={updateAction.isPending}
                  >
                    Cancel
                  </button>
                  {action.type !== 'info_request' && (
                    <button
                      className="btn btn-skip-accept"
                      onClick={() => handleSkipAndAccept(action)}
                      disabled={updateAction.isPending}
                    >
                      Accept only
                    </button>
                  )}
                  <button
                    className="btn btn-submit-response"
                    onClick={() => handleSubmitWithResponse(action)}
                    disabled={updateAction.isPending || (action.type === 'info_request' && !responseText.trim())}
                  >
                    {updateAction.isPending ? 'Sending...' : 'Accept & send to chat'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="action-buttons">
                <button
                  className="btn btn-accept"
                  onClick={() => handleAcceptClick(action)}
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
            )}
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
