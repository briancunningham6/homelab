import { useState } from 'react'
import type { MissionCreate } from '../types'
import '../styles/MissionForm.css'

interface MissionFormProps {
  initialData?: Partial<MissionCreate>
  onSubmit: (data: MissionCreate) => void
  onCancel?: () => void
  isLoading?: boolean
  submitLabel?: string
}

export const MissionForm: React.FC<MissionFormProps> = ({
  initialData = {},
  onSubmit,
  onCancel,
  isLoading = false,
  submitLabel = 'Create Mission',
}) => {
  const [formData, setFormData] = useState<MissionCreate>({
    name: initialData.name || '',
    description: initialData.description || '',
    goals: initialData.goals || '',
    check_interval: initialData.check_interval || 'daily',
    status: initialData.status || 'active',
  })

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form className="mission-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="name">Mission Name *</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          maxLength={200}
          placeholder="e.g., Car Manager, Home Maintenance"
        />
      </div>

      <div className="form-group">
        <label htmlFor="description">Description *</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          required
          rows={4}
          placeholder="Describe what this mission is about..."
        />
      </div>

      <div className="form-group">
        <label htmlFor="goals">Goals *</label>
        <textarea
          id="goals"
          name="goals"
          value={formData.goals}
          onChange={handleChange}
          required
          rows={4}
          placeholder="What should the AI agent help you accomplish?"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="check_interval">Check Interval</label>
          <select
            id="check_interval"
            name="check_interval"
            value={formData.check_interval}
            onChange={handleChange}
          >
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="manual">Manual Only</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="status">Status</label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      <div className="form-actions">
        {onCancel && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : submitLabel}
        </button>
      </div>
    </form>
  )
}
