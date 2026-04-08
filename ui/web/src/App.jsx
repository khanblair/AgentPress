import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Sidebar from './components/Sidebar'
import MainWorkspace from './pages/MainWorkspace'
import ActivePipeline from './pages/ActivePipeline'
import DocumentReview from './pages/DocumentReview'
import AgentChat from './pages/AgentChat'
import SkillLibrary from './pages/SkillLibrary'
import DataRoom from './pages/DataRoom'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

const qc = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5000 } } })

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/"                  element={<MainWorkspace />} />
              <Route path="/pipeline/:jobId"   element={<ActivePipeline />} />
              <Route path="/pipeline"          element={<ActivePipeline />} />
              <Route path="/review"            element={<DocumentReview />} />
              <Route path="/chat"              element={<AgentChat />} />
              <Route path="/skills"            element={<SkillLibrary />} />
              <Route path="/data-room"         element={<DataRoom />} />
              <Route path="/analytics"         element={<Analytics />} />
              <Route path="/settings"          element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
