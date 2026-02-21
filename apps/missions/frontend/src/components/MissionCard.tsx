import { Link } from 'react-router-dom'
import type { Mission } from '../types'
import '../styles/MissionCard.css'

interface MissionCardProps {
  mission: Mission
}

export const MissionCard: React.FC<MissionCardProps> = ({ mission }) => {
  const statusColor = {
    active: '#4CAF50',
    paused: '#FF9800',
    completed: '#2196F3',
    archived: '#9E9E9E',
  }[mission.status] || '#9E9E9E'

  return (
    <Link to={`/missions/${mission.id}`} className="mission-card-link">
      <div className="mission-card">
        <div className="mission-header">
          <h3 className="mission-title">{mission.name}</h3>
          <span
            className="mission-status"
            style={{ backgroundColor: statusColor }}
          >
            {mission.status}
          </span>
        </div>

        <p className="mission-description">{mission.description}</p>

        <div className="mission-goals">
          <strong>Goals:</strong>
          <p>{mission.goals}</p>
        </div>

        <div className="mission-meta">
          <div className="meta-item">
            <span className="meta-icon">📁</span>
            <span>{mission.file_count || 0} files</span>
          </div>
          <div className="meta-item">
            <span className="meta-icon">💬</span>
            <span>{mission.message_count || 0} messages</span>
          </div>
          <div className="meta-item">
            <span className="meta-icon">🔄</span>
            <span>{mission.check_interval}</span>
          </div>
        </div>

        <div className="mission-footer">
          <small>Last updated: {new Date(mission.updated_at).toLocaleDateString()}</small>
        </div>
      </div>
    </Link>
  )
}
