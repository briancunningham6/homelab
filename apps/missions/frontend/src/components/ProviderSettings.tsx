import { useState, useEffect } from 'react'
import '../styles/ProviderSettings.css'

interface Provider {
  id: string
  name: string
  display_name: string
  default_model: string | null
  is_enabled: boolean
  has_api_key: boolean
}

export const ProviderSettings: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingProvider, setEditingProvider] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [defaultModel, setDefaultModel] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/providers/')
      if (!response.ok) throw new Error('Failed to load providers')
      const data = await response.json()
      setProviders(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (provider: Provider) => {
    setEditingProvider(provider.id)
    setApiKey('')
    setDefaultModel(provider.default_model || '')
    setError(null)
  }

  const handleSave = async (providerId: string) => {
    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`/api/providers/${providerId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          default_model: defaultModel || null,
        }),
      })

      if (!response.ok) throw new Error('Failed to save provider')

      await loadProviders()
      setEditingProvider(null)
      setApiKey('')
      setDefaultModel('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save provider')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setEditingProvider(null)
    setApiKey('')
    setDefaultModel('')
    setError(null)
  }

  const handleRemoveKey = async (providerId: string) => {
    if (!confirm('Remove API key? You will need to add it again to use this provider.')) {
      return
    }

    try {
      const response = await fetch(`/api/providers/${providerId}/api-key`, {
        method: 'DELETE',
      })

      if (!response.ok) throw new Error('Failed to remove API key')
      await loadProviders()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove API key')
    }
  }

  if (loading) {
    return (
      <div className="provider-settings">
        <div className="loading">Loading providers...</div>
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
        {providers.map((provider) => (
          <div key={provider.id} className="provider-card">
            <div className="provider-header">
              <div className="provider-info">
                <h3>{provider.display_name}</h3>
                <span className="provider-name">{provider.name}</span>
              </div>
              <div className="provider-status">
                {provider.has_api_key ? (
                  <span className="status-badge configured">Configured</span>
                ) : (
                  <span className="status-badge not-configured">Not Configured</span>
                )}
              </div>
            </div>

            {editingProvider === provider.id ? (
              <div className="provider-edit-form">
                <div className="form-group">
                  <label htmlFor={`api-key-${provider.id}`}>API Key *</label>
                  <input
                    type="password"
                    id={`api-key-${provider.id}`}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key"
                  />
                  <small className="help-text">
                    {provider.name === 'claude'
                      ? 'Get your API key from https://console.anthropic.com/'
                      : 'Get your API key from https://platform.openai.com/'}
                  </small>
                </div>

                <div className="form-group">
                  <label htmlFor={`model-${provider.id}`}>Default Model (optional)</label>
                  <input
                    type="text"
                    id={`model-${provider.id}`}
                    value={defaultModel}
                    onChange={(e) => setDefaultModel(e.target.value)}
                    placeholder={
                      provider.name === 'claude'
                        ? 'e.g., claude-sonnet-4-20250514'
                        : 'e.g., gpt-4-turbo-preview'
                    }
                  />
                  <small className="help-text">Leave empty to use the default model</small>
                </div>

                <div className="form-actions">
                  <button
                    className="btn btn-secondary"
                    onClick={handleCancel}
                    disabled={saving}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSave(provider.id)}
                    disabled={saving || !apiKey.trim()}
                  >
                    {saving ? 'Saving...' : 'Save API Key'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="provider-actions">
                {provider.has_api_key ? (
                  <>
                    <div className="provider-details">
                      <div className="detail-item">
                        <strong>Default Model:</strong>
                        <span>{provider.default_model || 'Not set'}</span>
                      </div>
                    </div>
                    <div className="action-buttons">
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleEdit(provider)}
                      >
                        Update Settings
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleRemoveKey(provider.id)}
                      >
                        Remove API Key
                      </button>
                    </div>
                  </>
                ) : (
                  <button
                    className="btn btn-primary"
                    onClick={() => handleEdit(provider)}
                  >
                    Configure API Key
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="provider-help">
        <h4>About LLM Providers</h4>
        <ul>
          <li>
            <strong>API Keys:</strong> Your API keys are encrypted at rest using Fernet
            encryption
          </li>
          <li>
            <strong>Models:</strong> Leave the default model empty to use the provider's
            recommended model
          </li>
          <li>
            <strong>Costs:</strong> You are billed directly by the provider based on token
            usage
          </li>
          <li>
            <strong>Per-Mission:</strong> You can assign different providers to different
            missions
          </li>
        </ul>
      </div>
    </div>
  )
}
