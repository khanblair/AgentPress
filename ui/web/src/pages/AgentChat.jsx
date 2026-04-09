import { useState, useEffect, useRef, useCallback } from 'react'
import { getChatMessages, sendChatMessage } from '../api/client'
import { Send } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const AGENT_META = {
  orchestrator:  { label: 'Orchestrator',  color: '#cdbdff', emoji: '🧠', desc: 'Plans specs & coordinates' },
  researcher:    { label: 'Researcher',    color: '#44ddc1', emoji: '🔍', desc: 'Gathers data & web search' },
  synthesizer:   { label: 'Synthesizer',  color: '#93c5fd', emoji: '✍️',  desc: 'Writes document content'  },
  designer:      { label: 'Designer',     color: '#f9a8d4', emoji: '🎨', desc: 'Builds formatted files'    },
  inspector:     { label: 'Inspector',    color: '#fbbf24', emoji: '🔬', desc: 'QA & brand compliance'     },
  meta_engineer: { label: 'Meta-Engineer',color: '#f87171', emoji: '🧬', desc: 'Writes new skills'         },
  system:        { label: 'System',       color: '#948da2', emoji: '⚙️', desc: '' },
  user:          { label: 'You',          color: '#e2e8f0', emoji: '👤', desc: '' },
}

const MENTIONABLE = Object.entries(AGENT_META)
  .filter(([k]) => k !== 'user' && k !== 'system')
  .map(([key, v]) => ({ key, ...v }))

const TYPE_BG = {
  success: 'rgba(68,221,193,0.1)',
  warning: 'rgba(251,191,36,0.1)',
  error:   'rgba(248,113,113,0.1)',
  info:    null,
}

// Render @mentions highlighted
function MentionPicker({ query, onSelect, onClose }) {
  const filtered = query
    ? MENTIONABLE.filter(a =>
        a.key.includes(query.toLowerCase()) ||
        a.label.toLowerCase().includes(query.toLowerCase())
      )
    : MENTIONABLE

  if (!filtered.length) return null

  return (
    <div className="absolute bottom-full left-0 mb-2 w-64 rounded-xl overflow-hidden z-50"
      style={{ background: 'var(--surface-highest)', border: '1px solid var(--outline-var)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}>
      <div className="px-3 py-2 text-xs" style={{ color: 'var(--outline)', borderBottom: '1px solid var(--outline-var)' }}>
        Mention an agent
      </div>
      {filtered.map((agent, i) => (
        <button key={agent.key}
          onClick={() => onSelect(agent.key)}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-all hover:opacity-100"
          style={{ background: 'transparent' }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(205,189,255,0.08)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0"
            style={{ background: `${agent.color}20`, border: `1.5px solid ${agent.color}50` }}>
            {agent.emoji}
          </div>
          <div>
            <p className="text-sm font-medium" style={{ color: agent.color }}>@{agent.key}</p>
            <p className="text-xs" style={{ color: 'var(--on-surface-var)' }}>{agent.desc}</p>
          </div>
        </button>
      ))}
    </div>
  )
}

// Render markdown + @mentions highlighted
function MsgText({ content }) {
  // Pre-process: highlight @mentions before markdown parsing
  const withMentions = content.replace(
    /(@\w+)/g,
    '<span class="mention">$1</span>'
  )
  return (
    <div className="prose-chat">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => <ul className="list-disc ml-4 mb-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal ml-4 mb-1">{children}</ol>,
          li: ({ children }) => <li className="mb-0.5">{children}</li>,
          code: ({ children }) => (
            <code className="px-1 py-0.5 rounded text-xs font-mono"
              style={{ background: 'rgba(255,255,255,0.1)' }}>{children}</code>
          ),
        }}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

function Bubble({ msg, prevMsg }) {
  const isUser = msg.agent === 'user'
  const isSame = prevMsg?.agent === msg.agent
  const meta = AGENT_META[msg.agent] || AGENT_META.system
  const time = new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const bg = TYPE_BG[msg.type] || (isUser ? 'rgba(205,189,255,0.15)' : `${meta.color}14`)
  const border = isUser ? 'rgba(205,189,255,0.3)' : `${meta.color}30`

  return (
    <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-2.5 ${isSame ? 'mt-0.5' : 'mt-5'}`}>
      {/* Avatar */}
      {!isSame ? (
        <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm"
          style={{ background: `${meta.color}20`, border: `1.5px solid ${meta.color}50` }}>
          {meta.emoji}
        </div>
      ) : (
        <div className="w-8 shrink-0" />
      )}

      <div className={`flex flex-col gap-0.5 max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        {!isSame && (
          <div className={`flex items-baseline gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
            <span className="text-xs font-semibold" style={{ color: meta.color }}>{meta.label}</span>
            <span className="text-[10px]" style={{ color: 'var(--outline)' }}>{time}</span>
          </div>
        )}
        <div className="px-3.5 py-2 rounded-2xl text-sm leading-relaxed"
          style={{
            background: bg,
            border: `1px solid ${border}`,
            color: 'var(--on-surface)',
            borderTopLeftRadius: !isUser && !isSame ? '4px' : undefined,
            borderTopRightRadius: isUser && !isSame ? '4px' : undefined,
          }}>
          <MsgText content={msg.content} />
          {msg.job_id && (
            <span className="block text-[10px] mt-1 opacity-50">
              job: {msg.job_id.slice(0, 8)}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AgentChat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [lastId, setLastId] = useState(0)
  const [mentionQuery, setMentionQuery] = useState(null) // null = closed, string = filter
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const inputWrapRef = useRef(null)
  const isInitialLoad = useRef(true)

  // Detect @mention trigger in input
  const handleInputChange = (e) => {
    const val = e.target.value
    setInput(val)

    // Find if cursor is after an @ sign
    const cursor = e.target.selectionStart
    const textBefore = val.slice(0, cursor)
    const match = textBefore.match(/@(\w*)$/)
    if (match) {
      setMentionQuery(match[1]) // could be empty string (just typed @)
    } else {
      setMentionQuery(null)
    }
  }

  const insertMention = (agentKey) => {
    const cursor = inputRef.current?.selectionStart || input.length
    const textBefore = input.slice(0, cursor)
    const textAfter = input.slice(cursor)
    // Replace the partial @query with the full @agentKey
    const replaced = textBefore.replace(/@(\w*)$/, `@${agentKey} `)
    const newVal = replaced + textAfter
    setInput(newVal)
    setMentionQuery(null)
    inputRef.current?.focus()
    // Move cursor to end of inserted mention
    setTimeout(() => {
      const pos = replaced.length
      inputRef.current?.setSelectionRange(pos, pos)
    }, 0)
  }

  // Initial load + polling — merge localStorage cache with server
  useEffect(() => {
    const load = async () => {
      try {
        // Load cached messages first for instant display
        const cached = localStorage.getItem('agent_chat_messages')
        if (cached) {
          const parsed = JSON.parse(cached)
          setMessages(parsed)
          setLastId(parsed[parsed.length - 1]?.id || 0)
        }
        // Then fetch fresh from server
        const { messages: msgs } = await getChatMessages(0)
        if (msgs.length) {
          setMessages(msgs)
          setLastId(msgs[msgs.length - 1].id)
          localStorage.setItem('agent_chat_messages', JSON.stringify(msgs))
        }
      } catch (_) {}
    }
    load()
  }, [])

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const { messages: newMsgs } = await getChatMessages(lastId)
        if (newMsgs.length) {
          setMessages(prev => {
            const updated = [...prev, ...newMsgs]
            try { localStorage.setItem('agent_chat_messages', JSON.stringify(updated.slice(-200))) } catch {}
            return updated
          })
          setLastId(newMsgs[newMsgs.length - 1].id)
        }
      } catch (_) {}
    }, 1500)
    return () => clearInterval(interval)
  }, [lastId])

  useEffect(() => {
    if (isInitialLoad.current) {
      // On initial load, jump to bottom instantly without animation
      bottomRef.current?.scrollIntoView({ behavior: 'instant' })
      isInitialLoad.current = false
    } else {
      // On new messages, smooth scroll
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length])

  const send = async () => {
    if (!input.trim() || sending) return
    const msg = input.trim()
    setInput('')
    setSending(true)
    try {
      await sendChatMessage(msg, lastId)
      // Fetch immediately after sending
      const { messages: newMsgs } = await getChatMessages(lastId)
      if (newMsgs.length) {
        setMessages(prev => {
          const updated = [...prev, ...newMsgs]
          try { localStorage.setItem('agent_chat_messages', JSON.stringify(updated.slice(-200))) } catch {}
          return updated
        })
        setLastId(newMsgs[newMsgs.length - 1].id)
      }
    } catch (_) {}
    setSending(false)
    inputRef.current?.focus()
  }

  const handleKey = (e) => {
    if (mentionQuery !== null && e.key === 'Escape') {
      setMentionQuery(null)
      return
    }
    if (e.key === 'Enter' && !e.shiftKey && mentionQuery === null) {
      e.preventDefault()
      send()
    }
  }

  // Suggestion chips
  const suggestions = [
    '@orchestrator what can you do?',
    '@researcher find info on AI trends',
    '@inspector review my last document',
  ]

  return (
    <div className="flex flex-col h-screen overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 shrink-0"
        style={{ borderBottom: '1px solid var(--outline-var)', background: 'var(--surface-low)' }}>
        <div>
          <h2 className="text-base font-bold" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
            Agent Swarm Chat
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--on-surface-var)' }}>
            All 6 agents are online — mention any with @name
          </p>
        </div>
        {/* Online indicators */}
        <div className="flex gap-1.5">
          {Object.entries(AGENT_META).filter(([k]) => k !== 'user' && k !== 'system').map(([key, meta]) => (
            <div key={key} title={meta.label}
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs"
              style={{ background: `${meta.color}18`, border: `1.5px solid ${meta.color}50` }}>
              {meta.emoji}
            </div>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.map((msg, i) => (
          <Bubble key={msg.id} msg={msg} prevMsg={messages[i - 1]} />
        ))}
        {sending && (
          <div className="flex gap-2.5 mt-5">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0"
              style={{ background: 'rgba(205,189,255,0.1)', border: '1.5px solid rgba(205,189,255,0.3)' }}>
              ⚡
            </div>
            <div className="flex items-center gap-1.5 px-4 py-2.5 rounded-2xl rounded-tl-sm"
              style={{ background: 'var(--surface-highest)', border: '1px solid var(--outline-var)' }}>
              {[0, 1, 2].map(i => (
                <span key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                  style={{ background: 'var(--primary)', animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips */}
      {messages.length <= 7 && (
        <div className="flex gap-2 px-6 pb-2 flex-wrap">
          {suggestions.map(s => (
            <button key={s} onClick={() => setInput(s)}
              className="text-xs px-3 py-1.5 rounded-full transition-all"
              style={{ background: 'var(--surface-high)', color: 'var(--on-surface-var)', border: '1px solid var(--outline-var)' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-3 px-6 py-4 shrink-0"
        style={{ borderTop: '1px solid var(--outline-var)', background: 'var(--surface-low)' }}>
        <div ref={inputWrapRef} className="flex-1 relative flex items-end gap-2 rounded-2xl px-4 py-2.5"
          style={{ background: 'var(--surface-highest)', border: '1px solid var(--outline-var)' }}>

          {/* @mention picker */}
          {mentionQuery !== null && (
            <MentionPicker
              query={mentionQuery}
              onSelect={insertMention}
              onClose={() => setMentionQuery(null)}
            />
          )}

          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKey}
            placeholder="Message the agents... type @ to mention one"
            className="flex-1 resize-none bg-transparent outline-none text-sm leading-relaxed"
            style={{ color: 'var(--on-surface)', maxHeight: '120px' }}
          />
        </div>
        <button onClick={send} disabled={sending || !input.trim()}
          className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 disabled:opacity-40 transition-all"
          style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
          <Send size={15} strokeWidth={2} />
        </button>
      </div>
    </div>
  )
}
