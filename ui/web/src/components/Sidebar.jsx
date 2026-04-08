import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Zap, GitBranch, FileText, MessageSquare,
  Wrench, Database, BarChart2, Settings,
  PanelLeftClose, PanelLeftOpen,
} from 'lucide-react'

const NAV = [
  { to: '/',          icon: Zap,           label: 'Workspace'  },
  { to: '/pipeline',  icon: GitBranch,     label: 'Pipeline'   },
  { to: '/review',    icon: FileText,      label: 'Review'     },
  { to: '/chat',      icon: MessageSquare, label: 'Agent Chat' },
  { to: '/skills',    icon: Wrench,        label: 'Skills'     },
  { to: '/data-room', icon: Database,      label: 'Data Room'  },
  { to: '/analytics', icon: BarChart2,     label: 'Analytics'  },
  { to: '/settings',  icon: Settings,      label: 'Settings'   },
]

export default function Sidebar() {
  const [expanded, setExpanded] = useState(false)

  return (
    <aside
      className="flex flex-col shrink-0 h-screen sticky top-0 transition-all duration-200 overflow-hidden"
      style={{
        width: expanded ? '13rem' : '3.5rem',
        background: 'var(--surface-low)',
        borderRight: '1px solid var(--outline-var)',
      }}
    >
      {/* Logo + toggle */}
      <div className="flex items-center justify-between px-3 py-4 shrink-0">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <span className="text-sm font-bold shrink-0 leading-none" style={{ color: 'var(--primary)' }}>AP</span>
          {expanded && (
            <span className="text-sm font-semibold whitespace-nowrap" style={{ color: 'var(--on-surface)' }}>
              AgentPress
            </span>
          )}
        </div>
        <button
          onClick={() => setExpanded(v => !v)}
          className="shrink-0 p-1 rounded-md transition-all opacity-40 hover:opacity-100"
          style={{ color: 'var(--on-surface)' }}
          title={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          {expanded
            ? <PanelLeftClose size={15} strokeWidth={1.75} />
            : <PanelLeftOpen  size={15} strokeWidth={1.75} />
          }
        </button>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 px-2 flex-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-2 py-2.5 rounded-lg text-sm transition-all whitespace-nowrap ${
                isActive ? 'font-medium' : 'opacity-50 hover:opacity-90'
              }`
            }
            style={({ isActive }) => ({
              background: isActive ? 'rgba(205,189,255,0.1)' : 'transparent',
              color: isActive ? 'var(--primary)' : 'var(--on-surface)',
            })}
          >
            <Icon size={16} strokeWidth={1.75} className="shrink-0" />
            {expanded && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Version */}
      <div className="px-3 py-4">
        {expanded
          ? <span className="text-xs opacity-25" style={{ color: 'var(--on-surface-var)' }}>v1.0.0</span>
          : <span className="text-[10px] opacity-20" style={{ color: 'var(--on-surface-var)' }}>v1</span>
        }
      </div>
    </aside>
  )
}
