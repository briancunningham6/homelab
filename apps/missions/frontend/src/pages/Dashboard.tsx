import { Link } from 'react-router-dom'
import { useMissions } from '../hooks/useMissions'
import { MissionCard } from '../components/MissionCard'
import '../styles/Dashboard.css'

export const Dashboard: React.FC = () => {
  const { data: missions, isLoading, error } = useMissions()

  if (isLoading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading missions...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <h2>Error Loading Missions</h2>
          <p>{error instanceof Error ? error.message : 'Unknown error occurred'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Your Missions</h1>
        <Link to="/missions/new" className="btn btn-primary">
          + New Mission
        </Link>
      </div>

      {!missions || missions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🎯</div>
          <h2>No missions yet</h2>
          <p>Create your first mission to get started with AI-powered task management</p>
          <Link to="/missions/new" className="btn btn-primary">
            Create Your First Mission
          </Link>
        </div>
      ) : (
        <div className="missions-grid">
          {missions.map((mission) => (
            <MissionCard key={mission.id} mission={mission} />
          ))}
        </div>
      )}
    </div>
  )
}
