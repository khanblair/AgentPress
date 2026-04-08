import { useEffect, useRef } from 'react'
import { useLogStream } from '../hooks/useLogStream'

export default function AgentChat() {
  const lines = useLogStream(300)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  return (
    <div className="flex flex-col h-full py-8 px-8 max-w-4xl mx-auto gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
            Agent Swarm Chat
          </h2>
          <p className="text-xs mt-1" style={{ color: 'var(--on-surface-var)' }}>Live stream from agent_execution.log</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#44ddc1' }} />
          <span className="text-xs" style={{ color: '#44ddc1' }}>Live</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-2 rounded-xl p-4 min-h-0"
        style={{ background: 'var(--surface-low)', border: '1px solid var(--outline-var)', maxHeight: 'calc(100vh - 200px)' }}>
        {lines.length === 0 && (
          <p className="text-sm text-center py-8 animate-pulse" style={{ color: 'var(--on-surface-var)' }}>
            Waiting for agent activity...
          </p>
        )}
        {lines.map((entry, i) => (
          <div key={i} className="flex items-start gap-3 text-sm">
            <span className="text-xs shrink-0 mt-0.5 font-mono" style={{ color: 'var(--outline)' }}>{entry.ts}</span>
            <span className="shrink-0 px-2 py-0.5 rounded text-xs font-semibold"
              style={{ background: `${entry.agent.color}20`, color: entry.agent.color }}>
              {entry.agent.label}
            </span>
            <span style={{ color: 'var(--on-surface-var)' }}>{entry.raw}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
