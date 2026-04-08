import { AGENTS } from '../constants/agents'

const STATUS_STYLE = {
  done:    { bg: 'rgba(68,221,193,0.15)',  border: '#44ddc1', color: '#44ddc1' },
  active:  { bg: 'rgba(205,189,255,0.2)', border: '#cdbdff', color: '#cdbdff' },
  pending: { bg: 'transparent',           border: '#494456', color: '#948da2' },
  failed:  { bg: 'rgba(248,113,113,0.15)',border: '#f87171', color: '#f87171' },
}

function getStatus(agentKey, currentNode, jobStatus) {
  if (jobStatus === 'failed' && currentNode === agentKey) return 'failed'
  const order = AGENTS.map(a => a.key)
  const currentIdx = order.indexOf(currentNode)
  const agentIdx = order.indexOf(agentKey)
  if (currentIdx === -1) return 'pending'
  if (agentIdx < currentIdx) return 'done'
  if (agentIdx === currentIdx) return jobStatus === 'completed' ? 'done' : 'active'
  return 'pending'
}

export default function AgentChip({ agentKey, currentNode, jobStatus }) {
  const agent = AGENTS.find(a => a.key === agentKey)
  const status = getStatus(agentKey, currentNode, jobStatus)
  const style = STATUS_STYLE[status]

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-all"
      style={{ background: style.bg, borderColor: style.border, color: style.color }}>
      <agent.Icon size={14} strokeWidth={1.75} />
      <span className="font-medium">{agent.label}</span>
      {status === 'active' && (
        <span className="ml-auto w-2 h-2 rounded-full animate-pulse" style={{ background: style.color }} />
      )}
      {status === 'done' && <span className="ml-auto text-xs">✓</span>}
    </div>
  )
}
