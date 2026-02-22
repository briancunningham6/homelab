import { useSuggestedActions, useUpdateSuggestedAction } from '../hooks/useMissions'
import type { SuggestedAction } from '../types'
import '../styles/SuggestedActions.css'

interface SuggestedActionsProps {
  missionId: string
}

const SuggestedActions = ({ missionId }: SuggestedActionsProps) => {
  const { data: actions, isLoading } = useSuggestedActions(missionId, 'pending')
  const updateAction = useUpdateSuggestedAction()

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

  if (!actions || actions.length === 0) {
    return null
  }

  return (
    <div className="suggested-actions-container">
      <h3 className="suggested-actions-title">Suggested Actions</h3>
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
    </div>
  )
}

export default SuggestedActions
