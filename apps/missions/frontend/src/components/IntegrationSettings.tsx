import { useState, useEffect } from 'react'
import '../styles/ProviderSettings.css'

interface Integration {
  key: string
  display_name: string
  description: string
  has_value: boolean
}

export const IntegrationSettings: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadIntegrations()
  }, [])

  const loadIntegrations = async () => {
    try {
      const response = await fetch('/api/integrations/')
      if (!response.ok) throw new Error('Failed to load integrations')
      setIntegrations(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (integration: Integration) => {
    setEditingKey(integration.key)
    setApiKey('')
    setError(null)
  }

  const handleSave = async (key: string) => {
    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`/api/integrations/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      })

      if (!response.ok) throw new Error('Failed to save API key')

      await loadIntegrations()
      setEditingKey(null)
      setApiKey('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setEditingKey(null)
    setApiKey('')
    setError(null)
  }

  const handleRemove = async (key: string) => {
    if (!confirm('Remove API key? Web search will stop working until a new key is added.')) return

    try {
      const response = await fetch(`/api/integrations/${key}/key`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Failed to remove API key')
      await loadIntegrations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove API key')
    }
  }

  if (loading) {
    return (
      <div className="provider-settings">
        <div className="loading">Loading integrations...</div>
      </div>
    )
  }

  return (
    <div className="provider-settings">
      {error && (
        <div className="provider-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="providers-list">
        {integrations.map((integration) => (
          <div key={integration.key} className="provider-card">
            <div className="provider-header">
              <div className="provider-info">
                <h3>{integration.display_name}</h3>
                <span className="provider-name">{integration.key}</span>
              </div>
              <div className="provider-status">
                {integration.has_value ? (
                  <span className="status-badge configured">Configured</span>
                ) : (
                  <span className="status-badge not-configured">Not Configured</span>
                )}
              </div>
            </div>

            <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#666' }}>
              {integration.description}
            </p>

            {editingKey === integration.key ? (
              <div className="provider-edit-form">
                <div className="form-group">
                  <label htmlFor={`api-key-${integration.key}`}>API Key *</label>
                  <input
                    type="password"
                    id={`api-key-${integration.key}`}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key"
                    autoFocus
                  />
                </div>

                <div className="form-actions">
                  <button className="btn btn-secondary" onClick={handleCancel} disabled={saving}>
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSave(integration.key)}
                    disabled={saving || !apiKey.trim()}
                  >
                    {saving ? 'Saving...' : 'Save API Key'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="provider-actions">
                <div className="action-buttons">
                  {integration.has_value ? (
                    <>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleEdit(integration)}
                      >
                        Update Key
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleRemove(integration.key)}
                      >
                        Remove Key
                      </button>
                    </>
                  ) : (
                    <button className="btn btn-primary" onClick={() => handleEdit(integration)}>
                      Configure API Key
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="provider-help">
        <h4>About External Services</h4>
        <ul>
          <li>
            <strong>Tavily:</strong> Enables agents to search the web for up-to-date information
            during missions
          </li>
          <li>
            <strong>API Keys:</strong> Stored encrypted at rest, never exposed after saving
          </li>
        </ul>
      </div>
    </div>
  )
}
