import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useJobPolling } from '../hooks/useJobPolling'
import { getJobMessages } from '../api/client'
import { AGENTS } from '../constants/agents'
import { CheckCircle, XCircle, Loader, Circle, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'

// ── Constants ──────────────────────────────────────────────────────────────────

const DEPT_LABEL = {
  orchestrator:  'Orchestration',
  researcher:    'Research & Data',
  synthesizer:   'Content Production',
  designer:      'Brand & Formatting',
  inspector:     'Quality Assurance',
  meta_engineer: 'Self-Evolution',
}

const DEPT_DESC = {
  orchestrator:  'Parsing prompt, building document spec and task plan',
  researcher:    'Querying knowledge base and gathering research data',
  synthesizer:   'Drafting document content from research brief',
  designer:      'Writing and executing brand formatting code',
  inspector:     'Running 2-stage QA — factual accuracy + brand compliance',
  meta_engineer: 'Writing new skill to fix recurring failure',
}

const STATUS_COLORS = {
  done:    { icon: '#44ddc1', bg: 'rgba(68,221,193,0.08)',  border: 'rgba(68,221,193,0.25)'  },
  running: { icon: '#cdbdff', bg: 'rgba(205,189,255,0.1)',  border: 'rgba(205,189,255,0.35)' },
  failed:  { icon: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.3)'  },
  pending: { icon: '#494456', bg: 'transparent',            border: 'rgba(73,68,86,0.4)'     },
}

const MSG_TYPE_STYLE = {
  success: { color: '#44ddc1', dot: '#44ddc1' },
  warning: { color: '#fbbf24', dot: '#fbbf24' },
  error:   { color: '#f87171', dot: '#f87171' },
  info:    { color: 'var(--on-surface-var)', dot: 'var(--outline)' },
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function elapsed(startedAt, finishedAt) {
  if (!startedAt) return null
  const end = finishedAt ? new Date(finishedAt) : new Date()
  const secs = Math.round((end - new Date(startedAt)) / 1000)
  return secs < 60 ? `${secs}s` : `${Math.floor(secs / 60)}m ${secs % 60}s`
}

// ── Message bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ msg }) {
  const style = MSG_TYPE_STYLE[msg.type] || MSG_TYPE_STYLE.info
  return (
    <div className="flex items-start gap-2 py-1">
      <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0" style={{ background: style.dot }} />
      <p className="text-xs leading-relaxed break-words" style={{ color: style.color }}>
        {msg.content}
      </p>
    </div>
  )
}

// ── Agent step ─────────────────────────────────────────────────────────────────

function AgentStep({ agentKey, agentData, messages, isLast, isJobActive }) {
  const agent = AGENTS.find(a => a.key === agentKey)
  const status = agentData?.status || 'pending'
  const err = agentData?.error
  const time = elapsed(agentData?.started_at, agentData?.finished_at)
  const c = STATUS_COLORS[status] || STATUS_COLORS.pending

  // Auto-expand when running, collapse when done (unless it had messages)
  const hasMessages = messages.length > 0
  const [expanded, setExpanded] = useState(false)
  const bottomRef = useRef(null)

  // Auto-expand when this agent starts running
  useEffect(() => {
    if (status === 'running') setExpanded(true)
  }, [status])

  // Auto-scroll to latest message while running
  useEffect(() => {
    if (status === 'running' && expanded) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [messages.length, status, expanded])

  const StatusIcon = () => {
    if (status === 'done')    return <CheckCircle size={16} color={c.icon} strokeWidth={2} />
    if (status === 'running') return <Loader size={16} color={c.icon} strokeWidth={2} className="animate-spin" />
    if (status === 'failed')  return <XCircle size={16} color={c.icon} strokeWidth={2} />
    return <Circle size={16} color={c.icon} strokeWidth={1.5} />
  }

  return (
    <div className="flex gap-4">
      {/* Connector line */}
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
          style={{ background: c.bg, border: `1px solid ${c.border}` }}>
          <StatusIcon />
        </div>
        {!isLast && (
          <div className="w-px flex-1 mt-1"
            style={{
              background: status === 'done' ? 'rgba(68,221,193,0.3)' : 'rgba(73,68,86,0.3)',
              minHeight: '2rem',
            }} />
        )}
      </div>

      {/* Content */}
      <div className="flex flex-col gap-1 pb-6 flex-1 min-w-0">

        {/* Header row */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <agent.Icon size={13} strokeWidth={1.75} style={{ color: c.icon }} />
            <span className="text-sm font-semibold"
              style={{ color: status === 'pending' ? 'var(--outline)' : 'var(--on-surface)' }}>
              {agent.label}
            </span>
            <span className="text-xs px-2 py-0.5 rounded"
              style={{ background: c.bg, color: c.icon, border: `1px solid ${c.border}` }}>
              {DEPT_LABEL[agentKey]}
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {time && (
              <span className="text-xs" style={{ color: 'var(--outline)' }}>{time}</span>
            )}
            {hasMessages && (
              <button
                onClick={() => setExpanded(v => !v)}
                className="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded transition-all"
                style={{ color: 'var(--outline)', background: 'var(--surface-highest)' }}>
                {expanded
                  ? <ChevronUp size={11} strokeWidth={2} />
                  : <ChevronDown size={11} strokeWidth={2} />}
                {messages.length}
              </button>
            )}
          </div>
        </div>

        {/* Static description (only when pending or no messages) */}
        {(!hasMessages || status === 'pending') && (
          <p className="text-xs" style={{ color: status === 'pending' ? 'var(--outline-var)' : 'var(--on-surface-var)' }}>
            {DEPT_DESC[agentKey]}
          </p>
        )}

        {/* Live message feed */}
        {hasMessages && expanded && (
          <div className="mt-1 rounded-lg px-3 py-2 flex flex-col"
            style={{
              background: 'var(--surface-highest)',
              border: `1px solid ${c.border}`,
              maxHeight: '220px',
              overflowY: 'auto',
            }}>
            {messages.map((msg, i) => (
              <MessageBubble key={msg.id ?? i} msg={msg} />
            ))}
            {/* Typing indicator while running */}
            {status === 'running' && (
              <div className="flex items-center gap-1.5 pt-1">
                <span className="w-1 h-1 rounded-full animate-bounce" style={{ background: c.icon, animationDelay: '0ms' }} />
                <span className="w-1 h-1 rounded-full animate-bounce" style={{ background: c.icon, animationDelay: '150ms' }} />
                <span className="w-1 h-1 rounded-full animate-bounce" style={{ background: c.icon, animationDelay: '300ms' }} />
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Error detail */}
        {err && (
          <div className="flex items-start gap-2 mt-1 px-3 py-2 rounded-lg text-xs"
            style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.25)', color: '#f87171' }}>
            <AlertTriangle size={12} strokeWidth={2} className="shrink-0 mt-0.5" />
            <span className="break-all">{err}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function ActivePipeline() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { job, error } = useJobPolling(jobId, 1500)

  const isJobActive = job?.status === 'processing' || job?.status === 'queued'

  // Poll job messages while active, slow down when done
  const { data: msgData } = useQuery({
    queryKey: ['jobMessages', jobId],
    queryFn: () => getJobMessages(jobId),
    enabled: !!jobId,
    refetchInterval: isJobActive ? 1000 : 3000,
  })

  const allMessages = msgData?.messages || []

  // Group messages by agent key
  const messagesByAgent = {}
  for (const msg of allMessages) {
    if (!messagesByAgent[msg.agent]) messagesByAgent[msg.agent] = []
    messagesByAgent[msg.agent].push(msg)
  }

  if (!jobId) return (
    <div className="p-12 text-center" style={{ color: 'var(--on-surface-var)' }}>
      No active job.{' '}
      <button onClick={() => navigate('/')} className="underline" style={{ color: 'var(--primary)' }}>
        Start one
      </button>
    </div>
  )

  const agentKeys = ['orchestrator', 'researcher', 'synthesizer', 'designer', 'inspector', 'meta_engineer']
  const agents = job?.agents || {}

  const completedCount = Object.values(agents).filter(a => a.status === 'done').length
  const totalCount = agentKeys.length
  const progressPct = totalCount ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto py-10 px-6">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight"
            style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
            Pipeline
          </h2>
          <p className="text-xs mt-1 font-mono" style={{ color: 'var(--on-surface-var)' }}>
            {jobId?.slice(0, 8)}
          </p>
        </div>

        {/* Status badge */}
        {job && (
          <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
            style={{
              background: job.status === 'completed' ? 'rgba(68,221,193,0.15)' :
                          job.status === 'failed'    ? 'rgba(248,113,113,0.15)' :
                                                       'rgba(205,189,255,0.12)',
              color: job.status === 'completed' ? '#44ddc1' :
                     job.status === 'failed'    ? '#f87171' : '#cdbdff',
            }}>
            {job.status}
          </span>
        )}
      </div>

      {/* Progress bar */}
      {job && job.status === 'processing' && (
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between text-xs" style={{ color: 'var(--on-surface-var)' }}>
            <span>{completedCount} of {totalCount} agents complete</span>
            <span>{progressPct}%</span>
          </div>
          <div className="h-1 rounded-full overflow-hidden" style={{ background: 'var(--surface-highest)' }}>
            <div className="h-full rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%`, background: 'var(--primary)' }} />
          </div>
        </div>
      )}

      {/* QA retry / evolution badges */}
      {job && (job.qa_retry_count > 0 || job.evolution_triggered) && (
        <div className="flex gap-2">
          {job.qa_retry_count > 0 && (
            <span className="text-xs px-2 py-1 rounded"
              style={{ background: 'rgba(251,191,36,0.1)', color: '#fbbf24', border: '1px solid rgba(251,191,36,0.2)' }}>
              QA retries: {job.qa_retry_count}
            </span>
          )}
          {job.evolution_triggered && (
            <span className="text-xs px-2 py-1 rounded"
              style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid rgba(248,113,113,0.2)' }}>
              🧬 Evolution triggered
            </span>
          )}
        </div>
      )}

      {/* Agent steps with live messages */}
      <div className="flex flex-col mt-2">
        {agentKeys.map((key, i) => (
          <AgentStep
            key={key}
            agentKey={key}
            agentData={agents[key]}
            messages={messagesByAgent[key] || []}
            isLast={i === agentKeys.length - 1}
            isJobActive={isJobActive}
          />
        ))}
      </div>

      {/* Top-level error */}
      {(error || (job?.status === 'failed' && job?.error && !Object.values(agents).some(a => a.error))) && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-xl text-sm"
          style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.25)', color: '#f87171' }}>
          <AlertTriangle size={14} strokeWidth={2} className="shrink-0 mt-0.5" />
          <span>{error || job?.error}</span>
        </div>
      )}

      {/* Connecting... */}
      {!job && !error && (
        <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>
          Connecting to pipeline...
        </p>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        {job?.status === 'completed' && (
          <button onClick={() => navigate('/review')}
            className="px-6 py-2.5 rounded-xl text-sm font-semibold transition-all"
            style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
            View Document →
          </button>
        )}
        <button onClick={() => navigate('/')}
          className="px-6 py-2.5 rounded-xl text-sm transition-all"
          style={{ background: 'var(--surface-high)', color: 'var(--on-surface-var)', border: '1px solid var(--outline-var)' }}>
          ← New Document
        </button>
      </div>
    </div>
  )
}
