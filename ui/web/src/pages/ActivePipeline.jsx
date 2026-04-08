import { useParams, useNavigate } from 'react-router-dom'
import { useJobPolling } from '../hooks/useJobPolling'
import AgentChip from '../components/AgentChip'
import { AGENTS } from '../constants/agents'

export default function ActivePipeline() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { job, error } = useJobPolling(jobId)

  if (!jobId) return (
    <div className="p-12 text-center" style={{ color: 'var(--on-surface-var)' }}>
      No active job. <button onClick={() => navigate('/')} className="underline" style={{ color: 'var(--primary)' }}>Start one</button>
    </div>
  )

  return (
    <div className="flex flex-col gap-8 max-w-2xl mx-auto py-12 px-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
          Active Pipeline
        </h2>
        <p className="text-xs mt-1" style={{ color: 'var(--on-surface-var)' }}>
          Job <code>{jobId?.slice(0, 8)}</code>
        </p>
      </div>

      {/* Status badge */}
      {job && (
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
            style={{
              background: job.status === 'completed' ? 'rgba(68,221,193,0.15)' :
                          job.status === 'failed'    ? 'rgba(248,113,113,0.15)' :
                                                       'rgba(205,189,255,0.15)',
              color: job.status === 'completed' ? '#44ddc1' :
                     job.status === 'failed'    ? '#f87171' : '#cdbdff',
            }}>
            {job.status}
          </span>
          {job.qa_retry_count > 0 && (
            <span className="text-xs" style={{ color: 'var(--on-surface-var)' }}>
              QA retries: {job.qa_retry_count}
            </span>
          )}
          {job.evolution_triggered && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171' }}>
              🧬 Evolution triggered
            </span>
          )}
        </div>
      )}

      {/* Agent flow */}
      <div className="flex flex-col gap-2">
        {AGENTS.map(a => (
          <AgentChip key={a.key} agentKey={a.key}
            currentNode={job?.current_node}
            jobStatus={job?.status} />
        ))}
      </div>

      {/* Error */}
      {(error || job?.error) && (
        <p className="text-sm px-4 py-3 rounded-lg" style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid #f87171' }}>
          {error || job?.error}
        </p>
      )}

      {/* Actions */}
      {job?.status === 'completed' && (
        <button onClick={() => navigate('/review')}
          className="self-start px-6 py-2.5 rounded-xl text-sm font-semibold transition-all"
          style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
          View Document →
        </button>
      )}

      {job?.status === 'failed' && (
        <button onClick={() => navigate('/')}
          className="self-start px-6 py-2.5 rounded-xl text-sm font-semibold"
          style={{ background: 'var(--surface-high)', color: 'var(--on-surface-var)', border: '1px solid var(--outline-var)' }}>
          ← Try Again
        </button>
      )}

      {!job && !error && (
        <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Connecting to pipeline...</p>
      )}
    </div>
  )
}
