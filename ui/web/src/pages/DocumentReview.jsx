import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listOutputs, getDownloadUrl, submitCorrection } from '../api/client'

export default function DocumentReview() {
  const { data, isLoading } = useQuery({ queryKey: ['outputs'], queryFn: listOutputs })
  const [selected, setSelected] = useState(null)
  const [original, setOriginal] = useState('')
  const [corrected, setCorrected] = useState('')
  const [sessionId] = useState(() => crypto.randomUUID())
  const [correcting, setCorrecting] = useState(false)
  const [correctionStatus, setCorrectionStatus] = useState(null)

  const handleCorrection = async () => {
    if (!original || !corrected) return
    setCorrecting(true)
    try {
      await submitCorrection(original, corrected, sessionId)
      setCorrectionStatus('success')
    } catch {
      setCorrectionStatus('error')
    } finally {
      setCorrecting(false)
    }
  }

  return (
    <div className="flex flex-col gap-8 py-10 px-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
        Document Review
      </h2>

      {/* File list */}
      <div className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>Generated Files</p>
        {isLoading && <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading...</p>}
        {data?.files?.length === 0 && (
          <p className="text-sm" style={{ color: 'var(--on-surface-var)' }}>No files yet. Run a pipeline first.</p>
        )}
        {data?.files?.map(f => (
          <div key={f.name}
            onClick={() => setSelected(f)}
            className="flex items-center justify-between px-4 py-3 rounded-xl cursor-pointer transition-all"
            style={{
              background: selected?.name === f.name ? 'var(--surface-highest)' : 'var(--surface-high)',
              border: `1px solid ${selected?.name === f.name ? 'var(--primary)' : 'var(--outline-var)'}`,
            }}>
            <div className="flex items-center gap-3">
              <span className="text-lg">
                {f.extension === 'pptx' ? '📊' : f.extension === 'docx' ? '📝' : f.extension === 'xlsx' ? '📈' : '📄'}
              </span>
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--on-surface)' }}>{f.name}</p>
                <p className="text-xs" style={{ color: 'var(--on-surface-var)' }}>
                  {(f.size_bytes / 1024).toFixed(1)} KB · {new Date(f.modified_at).toLocaleString()}
                </p>
              </div>
            </div>
            <a href={getDownloadUrl(f.name)} download
              onClick={e => e.stopPropagation()}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
              Download
            </a>
          </div>
        ))}
      </div>

      {/* Correction panel */}
      <div className="flex flex-col gap-4 pt-4" style={{ borderTop: '1px solid var(--outline-var)' }}>
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>Evolution Engine</p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--on-surface-var)' }}>
            Paste AI output and your corrected version — Agent 6 will update brand rules automatically.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>Original AI Output</label>
            <textarea rows={8} value={original} onChange={e => setOriginal(e.target.value)}
              className="resize-none rounded-xl px-4 py-3 text-sm outline-none"
              style={{ background: 'var(--surface-highest)', color: 'var(--on-surface)', border: '1px solid var(--outline-var)' }} />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>Your Corrected Version</label>
            <textarea rows={8} value={corrected} onChange={e => setCorrected(e.target.value)}
              className="resize-none rounded-xl px-4 py-3 text-sm outline-none"
              style={{ background: 'var(--surface-highest)', color: 'var(--on-surface)', border: '1px solid var(--outline-var)' }} />
          </div>
        </div>

        {correctionStatus === 'success' && (
          <p className="text-sm px-4 py-2 rounded-lg" style={{ background: 'rgba(68,221,193,0.1)', color: '#44ddc1', border: '1px solid #44ddc1' }}>
            🧬 Meta-Engineer updated brand rules successfully.
          </p>
        )}
        {correctionStatus === 'error' && (
          <p className="text-sm px-4 py-2 rounded-lg" style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid #f87171' }}>
            Failed to submit correction.
          </p>
        )}

        <button onClick={handleCorrection} disabled={correcting || !original || !corrected}
          className="self-start px-6 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 transition-all"
          style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
          {correcting ? 'Processing...' : '🧬 Submit Correction'}
        </button>
      </div>
    </div>
  )
}
