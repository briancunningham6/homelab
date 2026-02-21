import { useNavigate } from 'react-router-dom'
import { useCreateMission } from '../hooks/useMissions'
import { MissionForm } from '../components/MissionForm'
import type { MissionCreate } from '../types'
import '../styles/MissionCreate.css'

export const MissionCreate: React.FC = () => {
  const navigate = useNavigate()
  const createMission = useCreateMission()

  const handleSubmit = async (data: MissionCreate) => {
    try {
      const newMission = await createMission.mutateAsync(data)
      navigate(`/missions/${newMission.id}`)
    } catch (error) {
      console.error('Failed to create mission:', error)
      alert('Failed to create mission. Please try again.')
    }
  }

  const handleCancel = () => {
    navigate('/')
  }

  return (
    <div className="mission-create">
      <div className="page-header">
        <h1>Create New Mission</h1>
        <p>Define a goal-oriented task for your AI agent to work on</p>
      </div>

      <div className="form-container">
        <MissionForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={createMission.isPending}
          submitLabel="Create Mission"
        />
      </div>

      <div className="help-text">
        <h3>What makes a good mission?</h3>
        <ul>
          <li><strong>Specific goals:</strong> Clearly define what you want to accomplish</li>
          <li><strong>Context files:</strong> Upload relevant documents after creating the mission</li>
          <li><strong>Ongoing tasks:</strong> Missions can run indefinitely, checking for updates</li>
          <li><strong>Examples:</strong> Car maintenance tracking, financial planning, home projects</li>
        </ul>
      </div>
    </div>
  )
}
