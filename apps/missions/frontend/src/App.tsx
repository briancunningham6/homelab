import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { MissionDetail } from './pages/MissionDetail'
import { MissionCreate } from './pages/MissionCreate'
import { Settings } from './pages/Settings'
import { NotFound } from './pages/NotFound'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/missions/new" element={<MissionCreate />} />
        <Route path="/missions/:id" element={<MissionDetail />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  )
}

export default App
