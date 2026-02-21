import '../styles/Settings.css'

export const Settings: React.FC = () => {
  return (
    <div className="settings">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure LLM providers and mission preferences</p>
      </div>

      <div className="settings-content">
        <section className="settings-section">
          <h2>LLM Providers</h2>
          <div className="placeholder-notice">
            <div className="placeholder-icon">⚙️</div>
            <h3>Coming in Phase 2</h3>
            <p>
              Configure your API keys for Claude and OpenAI here. API keys will be encrypted
              and stored securely.
            </p>
            <ul className="feature-list">
              <li>Add Anthropic Claude API key</li>
              <li>Add OpenAI API key</li>
              <li>Set default provider per mission</li>
              <li>View token usage and costs</li>
            </ul>
          </div>
        </section>

        <section className="settings-section">
          <h2>Categories</h2>
          <div className="placeholder-notice">
            <div className="placeholder-icon">🏷️</div>
            <h3>Coming in Phase 6</h3>
            <p>
              Manage mission categories to organize your tasks.
            </p>
            <ul className="feature-list">
              <li>Default categories: Home, Work, Financial, Health, Learning</li>
              <li>Create custom categories</li>
              <li>Set colors and icons</li>
            </ul>
          </div>
        </section>

        <section className="settings-section">
          <h2>Notifications</h2>
          <div className="placeholder-notice">
            <div className="placeholder-icon">🔔</div>
            <h3>Coming in Phase 4</h3>
            <p>
              Configure push notifications via Ntfy for mission updates.
            </p>
            <ul className="feature-list">
              <li>Enable/disable notifications</li>
              <li>Set notification preferences per mission</li>
              <li>Configure Ntfy server settings</li>
            </ul>
          </div>
        </section>

        <section className="settings-section">
          <h2>External Services</h2>
          <div className="placeholder-notice">
            <div className="placeholder-icon">🔌</div>
            <h3>Coming in Phase 3</h3>
            <p>
              Configure external service integrations for agent tools.
            </p>
            <ul className="feature-list">
              <li>Tavily API (web search)</li>
              <li>Document parsing services</li>
              <li>Code execution sandbox settings</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  )
}
