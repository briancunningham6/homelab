import { useParams, useNavigate, Link } from 'react-router-dom'
import { useState, useRef } from 'react'
import { useMission, useMissionFiles, useDeleteMission, useDeleteFile, useUpdateMission, useSuggestedActions } from '../hooks/useMissions'
import { FileUpload } from '../components/FileUpload'
import { Chat, type ChatHandle } from '../components/Chat'
import SuggestedActions from '../components/SuggestedActions'
import { MissionNotes } from '../components/MissionNotes'
import { MissionTasks } from '../components/MissionTasks'
import '../styles/MissionDetail.css'

type TabType = 'overview' | 'agent' | 'notes' | 'tasks'

export const MissionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    goals: '',
    check_interval: '',
    status: '',
  })

  const chatRef = useRef<ChatHandle>(null)

  const { data: mission, isLoading: missionLoading, error: missionError } = useMission(id!)
  const { data: files, isLoading: filesLoading } = useMissionFiles(id!)
  const { data: pendingActions } = useSuggestedActions(id!, 'pending')
  const deleteMission = useDeleteMission()
  const deleteFile = useDeleteFile()
  const updateMission = useUpdateMission()

  const hasPendingSuggestions = pendingActions && pendingActions.length > 0
  const [notifState, setNotifState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

  const [imagePreview, setImagePreview] = useState<{ url: string; name: string } | null>(null)

  const [showSuggestions, setShowSuggestions] = useState(true)
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetSelections, setResetSelections] = useState({
    messages: false,
    suggested_actions: false,
    tasks: false,
    notes: false,
  })
  const [isResetting, setIsResetting] = useState(false)

  const resetLabels: Record<keyof typeof resetSelections, string> = {
    messages: 'Chat messages',
    suggested_actions: 'Suggested actions',
    tasks: 'Tasks',
    notes: 'Notes',
  }

  const handleOpenReset = () => {
    setResetSelections({ messages: false, suggested_actions: false, tasks: false, notes: false })
    setShowResetModal(true)
  }

  const handleConfirmReset = async () => {
    const noneSelected = !Object.values(resetSelections).some(Boolean)
    if (noneSelected) return

    setIsResetting(true)
    try {
      const response = await fetch(`/api/missions/${id}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resetSelections),
      })
      if (!response.ok) throw new Error('Reset failed')
      setShowResetModal(false)
      // Reload the page to reflect cleared data
      window.location.reload()
    } catch {
      alert('Failed to reset mission data. Please try again.')
    } finally {
      setIsResetting(false)
    }
  }

  const handleTestNotification = async () => {
    setNotifState('sending')
    try {
      const res = await fetch('/api/notifications/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_id: id, title: `Mission: ${mission?.name}`, message: 'Notifications are working.' }),
      })
      setNotifState(res.ok ? 'sent' : 'error')
    } catch {
      setNotifState('error')
    }
    setTimeout(() => setNotifState('idle'), 3000)
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this mission? This cannot be undone.')) {
      return
    }

    try {
      await deleteMission.mutateAsync(id!)
      navigate('/')
    } catch (error) {
      console.error('Failed to delete mission:', error)
      alert('Failed to delete mission. Please try again.')
    }
  }

  const handleDeleteFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Delete ${fileName}?`)) {
      return
    }

    try {
      await deleteFile.mutateAsync({ missionId: id!, fileId })
    } catch (error) {
      console.error('Failed to delete file:', error)
      alert('Failed to delete file. Please try again.')
    }
  }

  const handleViewFile = (fileId: string, mimeType?: string, name?: string) => {
    const url = `/api/missions/${id}/files/${fileId}`
    if (mimeType?.startsWith('image/')) {
      setImagePreview({ url, name: name ?? 'Image' })
    } else {
      window.open(url, '_blank')
    }
  }

  const handleEdit = () => {
    if (mission) {
      setEditForm({
        name: mission.name,
        description: mission.description,
        goals: mission.goals,
        check_interval: mission.check_interval,
        status: mission.status,
      })
      setIsEditing(true)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
  }

  const handleSaveEdit = async () => {
    try {
      await updateMission.mutateAsync({
        id: id!,
        data: editForm,
      })
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update mission:', error)
      alert('Failed to update mission. Please try again.')
    }
  }

  const handleFormChange = (field: string, value: string) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  if (missionLoading) {
    return (
      <div className="mission-detail">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading mission...</p>
        </div>
      </div>
    )
  }

  if (missionError || !mission) {
    return (
      <div className="mission-detail">
        <div className="error">
          <h2>Mission Not Found</h2>
          <p>The mission you're looking for doesn't exist or has been deleted.</p>
          <Link to="/" className="btn btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    )
  }

  const statusColor = {
    active: '#4CAF50',
    paused: '#FF9800',
    completed: '#2196F3',
    archived: '#9E9E9E',
  }[mission.status] || '#9E9E9E'

  return (
    <div className="mission-detail">
      <div className="page-header">
        <div className="header-top">
          <Link to="/" className="back-link">← Dashboard</Link>
          <div className="header-actions">
            {isEditing ? (
              <>
                <button className="btn btn-primary btn-small" onClick={handleSaveEdit} disabled={updateMission.isPending}>
                  {updateMission.isPending ? 'Saving...' : 'Save'}
                </button>
                <button className="btn btn-reset btn-small" onClick={handleOpenReset}>
                  Reset data
                </button>
                <button className="btn btn-secondary btn-small" onClick={handleCancelEdit}>
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn btn-secondary btn-small"
                  onClick={handleTestNotification}
                  disabled={notifState === 'sending'}
                  title="Send a test notification to your phone"
                >
                  {notifState === 'sending' ? '…' : notifState === 'sent' ? '✓ Sent' : notifState === 'error' ? '✗ Failed' : '🔔'}
                </button>
                <button className="btn btn-primary btn-small" onClick={handleEdit}>
                  Edit
                </button>
                <button className="btn btn-secondary btn-small" onClick={handleDelete} disabled={deleteMission.isPending}>
                  {deleteMission.isPending ? 'Deleting...' : 'Delete'}
                </button>
              </>
            )}
          </div>
        </div>
        <div className="header-main">
          {isEditing ? (
            <input
              type="text"
              className="mission-name-input"
              value={editForm.name}
              onChange={(e) => handleFormChange('name', e.target.value)}
            />
          ) : (
            <h1>{mission.name}</h1>
          )}
          {isEditing ? (
            <select
              className="status-select"
              value={editForm.status}
              onChange={(e) => handleFormChange('status', e.target.value)}
            >
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          ) : (
            <span className="mission-status-badge" style={{ backgroundColor: statusColor }}>
              {mission.status}
            </span>
          )}
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'agent' ? 'active' : ''}`}
          onClick={() => setActiveTab('agent')}
        >
          Agent
          {hasPendingSuggestions && <span className="suggestion-indicator"></span>}
        </button>
        <button
          className={`tab ${activeTab === 'notes' ? 'active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          Notes
        </button>
        <button
          className={`tab ${activeTab === 'tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          Tasks
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <section className="mission-section">
              <h2>Description</h2>
              {isEditing ? (
                <textarea
                  className="edit-textarea"
                  value={editForm.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  rows={4}
                />
              ) : (
                <p>{mission.description}</p>
              )}
            </section>

            <section className="mission-section">
              <h2>Goals</h2>
              {isEditing ? (
                <textarea
                  className="edit-textarea"
                  value={editForm.goals}
                  onChange={(e) => handleFormChange('goals', e.target.value)}
                  rows={4}
                />
              ) : (
                <p>{mission.goals}</p>
              )}
            </section>

            <section className="mission-section">
              <h2>Settings</h2>
              <div className="settings-grid">
                <div className="setting-item">
                  <strong>Check Interval:</strong>
                  {isEditing ? (
                    <select
                      className="setting-select"
                      value={editForm.check_interval}
                      onChange={(e) => handleFormChange('check_interval', e.target.value)}
                    >
                      <option value="hourly">Hourly</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="manual">Manual</option>
                    </select>
                  ) : (
                    <span>{mission.check_interval}</span>
                  )}
                </div>
                <div className="setting-item">
                  <strong>Created:</strong>
                  <span>{new Date(mission.created_at).toLocaleDateString()}</span>
                </div>
                <div className="setting-item">
                  <strong>Last Updated:</strong>
                  <span>{new Date(mission.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </section>

            <section className="mission-section">
              <h2>Context Files ({files?.length || 0})</h2>
              <FileUpload missionId={id!} />

              {filesLoading ? (
                <div className="files-loading">Loading files...</div>
              ) : files && files.length > 0 ? (
                <div className="files-list">
                  {files.map((file) => (
                    <div key={file.id} className="file-item">
                      <span className="file-icon">{file.mime_type?.startsWith('image/') ? '🖼️' : '📄'}</span>
                      <button
                        className="file-name-button"
                        onClick={() => handleViewFile(file.id, file.mime_type, file.original_name)}
                        title={file.mime_type?.startsWith('image/') ? 'Click to preview' : 'Click to download'}
                      >
                        {file.original_name}
                      </button>
                      <span className="file-size">{formatBytes(file.size)}</span>
                      <span className="file-date">
                        {new Date(file.uploaded_at).toLocaleDateString()}
                      </span>
                      <button
                        className="btn btn-small btn-danger"
                        onClick={() => handleDeleteFile(file.id, file.original_name)}
                        disabled={deleteFile.isPending}
                        title="Delete file"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-files">
                  <p>No files uploaded yet. Add context files to help the AI agent.</p>
                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="notes-tab">
            <MissionNotes missionId={id!} initialNotes={mission.notes} />
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="tasks-tab">
            <MissionTasks missionId={id!} />
          </div>
        )}

        {activeTab === 'agent' && (
          <div className={`agent-tab-layout ${showSuggestions ? '' : 'suggestions-hidden'}`}>
            <div className="agent-chat-section">
              <Chat ref={chatRef} missionId={id!} />
            </div>
            {showSuggestions ? (
              <div className="agent-suggestions-section">
                <SuggestedActions
                  missionId={id!}
                  onSendToChat={(msg) => chatRef.current?.sendMessage(msg)}
                  onCollapse={() => setShowSuggestions(false)}
                />
              </div>
            ) : (
              <button
                className="suggestions-show-btn"
                onClick={() => setShowSuggestions(true)}
                title="Show Suggested Actions"
              >
                💡
              </button>
            )}
          </div>
        )}
      </div>

      {imagePreview && (
        <div className="image-preview-overlay" onClick={() => setImagePreview(null)}>
          <button className="image-preview-close" onClick={() => setImagePreview(null)}>✕</button>
          <img
            className="image-preview-img"
            src={imagePreview.url}
            alt={imagePreview.name}
            onClick={(e) => e.stopPropagation()}
          />
          <div className="image-preview-name" onClick={(e) => e.stopPropagation()}>
            {imagePreview.name}
            <a
              href={imagePreview.url}
              download={imagePreview.name}
              className="image-preview-download"
              onClick={(e) => e.stopPropagation()}
            >
              Download
            </a>
          </div>
        </div>
      )}

      {showResetModal && (
        <div className="reset-modal-overlay" onClick={() => !isResetting && setShowResetModal(false)}>
          <div className="reset-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="reset-modal-title">Reset mission data</h3>
            <p className="reset-modal-description">
              Select what to permanently clear. This cannot be undone.
            </p>

            <div className="reset-checkboxes">
              {(Object.keys(resetSelections) as Array<keyof typeof resetSelections>).map((key) => (
                <label key={key} className="reset-checkbox-row">
                  <input
                    type="checkbox"
                    checked={resetSelections[key]}
                    onChange={(e) =>
                      setResetSelections((prev) => ({ ...prev, [key]: e.target.checked }))
                    }
                    disabled={isResetting}
                  />
                  <span>{resetLabels[key]}</span>
                </label>
              ))}
            </div>

            <div className="reset-modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowResetModal(false)}
                disabled={isResetting}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleConfirmReset}
                disabled={isResetting || !Object.values(resetSelections).some(Boolean)}
              >
                {isResetting ? 'Clearing...' : 'Clear selected'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
