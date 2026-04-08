import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getKnowledge, updateKnowledge } from '../api/client'
import { RotateCcw } from 'lucide-react'
import api from '../api/client'

function KnowledgeEditor({ title, fileKey, initialContent }) {
  const [content, setContent] = useState(initialContent)
  const qc = useQueryClient()
  const mutation = useMutation({
    mutationFn: () => updateKnowledge(fileKey, content),
    onSuccess: () => qc.invalidateQueries(['knowledge']),
  })

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>{title}</p>
        <button onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="px-4 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-40 transition-all"
          style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
          {mutation.isPending ? 'Saving...' : 'Save'}
        </button>
      </div>
      <textarea rows={14} value={content} onChange={e => setContent(e.target.value)}
        className="resize-none rounded-xl px-4 py-3 text-sm font-mono outline-none"
        style={{ background: 'var(--surface-highest)', color: 'var(--on-surface)', border: '1px solid var(--outline-var)' }} />
      {mutation.isSuccess && (
        <p className="text-xs" style={{ color: '#44ddc1' }}>✓ Saved successfully</p>
      )}
    </div>
  )
}

function RestartPanel() {
  const [status, setStatus] = useState('idle') // idle | restarting | back_up | failed

  const handleRestart = async () => {
    if (!window.confirm('Restart the backend server? Active jobs will be lost.')) return
    setStatus('restarting')
    try {
      await api.post('/api/v1/restart')
    } catch (_) {
      // Expected — server closes connection mid-restart
    }

    // Poll /health until backend is back
    const start = Date.now()
    const poll = async () => {
      if (Date.now() - start > 30000) { setStatus('failed'); return }
      try {
        await api.get('/health', { baseURL: 'http://localhost:8000' })
        setStatus('back_up')
        // Reload the frontend after a short delay
        setTimeout(() => window.location.reload(), 800)
      } catch (_) {
        setTimeout(poll, 1000)
      }
    }
    setTimeout(poll, 1500)
  }

  return (
    <div className="flex flex-col gap-3 px-5 py-4 rounded-xl"
      style={{ background: 'var(--surface-high)', border: '1px solid var(--outline-var)' }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>Restart Servers</p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--on-surface-var)' }}>
            Restarts the backend process and reloads the frontend. Active jobs will be lost.
          </p>
        </div>
        <button
          onClick={handleRestart}
          disabled={status === 'restarting'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold disabled:opacity-40 transition-all"
          style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid #f87171' }}>
          <RotateCcw size={13} strokeWidth={2} className={status === 'restarting' ? 'animate-spin' : ''} />
          {status === 'restarting' ? 'Restarting...' : 'Restart'}
        </button>
      </div>

      {status === 'restarting' && (
        <p className="text-xs animate-pulse" style={{ color: '#fbbf24' }}>
          Waiting for backend to come back up...
        </p>
      )}
      {status === 'back_up' && (
        <p className="text-xs" style={{ color: '#44ddc1' }}>✓ Back up — reloading...</p>
      )}
      {status === 'failed' && (
        <p className="text-xs" style={{ color: '#f87171' }}>
          Backend did not respond within 30s. Check your terminal.
        </p>
      )}
    </div>
  )
}

export default function Settings() {
  const { data, isLoading } = useQuery({ queryKey: ['knowledge'], queryFn: getKnowledge })

  return (
    <div className="flex flex-col gap-10 py-10 px-8 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
        Settings
      </h2>

      {/* Knowledge base editors */}
      {isLoading ? (
        <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading knowledge base...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <KnowledgeEditor title="brand.md — Visual & Tone Rules" fileKey="brand" initialContent={data?.brand || ''} />
          <KnowledgeEditor title="user.md — User Preferences"     fileKey="user"  initialContent={data?.user  || ''} />
        </div>
      )}

      {/* Model in use */}
      <div className="flex flex-col gap-3" style={{ borderTop: '1px solid var(--outline-var)', paddingTop: '2rem' }}>
        <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>Active Model</p>
        <p className="text-xs" style={{ color: 'var(--on-surface-var)' }}>All agents share a single model configured via .env</p>
        <div className="flex items-center justify-between px-4 py-2.5 rounded-lg"
          style={{ background: 'var(--surface-high)', border: '1px solid var(--outline-var)' }}>
          <span className="text-sm" style={{ color: 'var(--on-surface-var)' }}>MODEL</span>
          <code className="text-xs" style={{ color: 'var(--primary)' }}>google/gemini-3-flash-preview</code>
        </div>
      </div>

      {/* Restart */}
      <div style={{ borderTop: '1px solid var(--outline-var)', paddingTop: '2rem' }}>
        <RestartPanel />
      </div>
    </div>
  )
}
