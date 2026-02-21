import { useParams, useNavigate, Link } from 'react-router-dom'
import { useMission, useMissionFiles, useDeleteMission } from '../hooks/useMissions'
import { FileUpload } from '../components/FileUpload'
import { Chat } from '../components/Chat'
import '../styles/MissionDetail.css'

export const MissionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: mission, isLoading: missionLoading, error: missionError } = useMission(id!)
  const { data: files, isLoading: filesLoading } = useMissionFiles(id!)
  const deleteMission = useDeleteMission()

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
        <div className="header-left">
          <Link to="/" className="back-link">← Back to Dashboard</Link>
          <h1>{mission.name}</h1>
          <span className="mission-status-badge" style={{ backgroundColor: statusColor }}>
            {mission.status}
          </span>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={handleDelete} disabled={deleteMission.isPending}>
            {deleteMission.isPending ? 'Deleting...' : 'Delete Mission'}
          </button>
        </div>
      </div>

      <div className="mission-content">
        <section className="mission-section">
          <h2>Description</h2>
          <p>{mission.description}</p>
        </section>

        <section className="mission-section">
          <h2>Goals</h2>
          <p>{mission.goals}</p>
        </section>

        <section className="mission-section">
          <h2>Settings</h2>
          <div className="settings-grid">
            <div className="setting-item">
              <strong>Check Interval:</strong>
              <span>{mission.check_interval}</span>
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
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.original_name}</span>
                  <span className="file-size">{formatBytes(file.size)}</span>
                  <span className="file-date">
                    {new Date(file.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-files">
              <p>No files uploaded yet. Add context files to help the AI agent.</p>
            </div>
          )}
        </section>

        <section className="mission-section">
          <h2>Chat with AI Agent</h2>
          <Chat missionId={id!} />
        </section>
      </div>
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
