import { Link, useLocation } from 'react-router-dom'
import '../styles/Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : ''
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <Link to="/">
              <h1>Missions</h1>
            </Link>
          </div>
          <nav className="nav">
            <Link to="/" className={isActive('/')}>
              Dashboard
            </Link>
            <Link to="/missions/new" className={isActive('/missions/new')}>
              New Mission
            </Link>
            <Link to="/capture" className={`nav-capture ${isActive('/capture')}`}>
              Quick Capture
            </Link>
            <Link to="/settings" className={isActive('/settings')}>
              Settings
            </Link>
          </nav>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
      <footer className="footer">
        <p>Missions - Persistent AI Agent Management</p>
      </footer>
    </div>
  )
}
