import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { listOutputs, getDownloadUrl, previewDocument, chatWithDoc, editDocument } from '../api/client'
import { Download, Send, FileText, Table, Presentation, File, Pencil, CheckCircle, Loader } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const EXT_ICON  = { pptx: Presentation, docx: FileText, xlsx: Table, pdf: File }
const EXT_COLOR = { pptx: '#f9a8d4', docx: 'var(--primary)', xlsx: '#44ddc1', pdf: '#fbbf24' }

// ── Helpers ────────────────────────────────────────────────────────────────────

function loadChatState(filename) {
  try {
    const raw = localStorage.getItem(`doc_chat_${filename}`)
    if (raw) return JSON.parse(raw)
  } catch {}
  return [{ role: 'assistant', content: `I've read **${filename}**. Ask me anything about it, or tell me what to change.` }]
}

function saveChatState(filename, messages) {
  try { localStorage.setItem(`doc_chat_${filename}`, JSON.stringify(messages)) } catch {}
}

function isEditSuggestion(content) {
  const l = content.toLowerCase()
  return l.includes('revised') || l.includes('updated') || l.includes('changed') ||
         l.includes('replaced') || l.includes('rewritten') || l.includes('new version') ||
         l.includes('edited') || l.includes('here is') || l.includes("here's")
}

// ── Markdown renderer ──────────────────────────────────────────────────────────

function MarkdownMsg({ content }) {
  return (
    <ReactMarkdown components={{
      p:      ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
      em:     ({ children }) => <em className="italic">{children}</em>,
      ul:     ({ children }) => <ul className="list-disc ml-4 mb-1">{children}</ul>,
      ol:     ({ children }) => <ol className="list-decimal ml-4 mb-1">{children}</ol>,
      li:     ({ children }) => <li className="mb-0.5">{children}</li>,
      code:   ({ children }) => (
        <code className="px-1 py-0.5 rounded text-xs font-mono"
          style={{ background: 'rgba(0,0,0,0.08)' }}>{children}</code>
      ),
    }}>
      {content}
    </ReactMarkdown>
  )
}

// ── Rich text (DOCX inline formatting) ────────────────────────────────────────

function RichText({ runs, text }) {
  if (!runs || runs.length === 0) return <span>{text}</span>
  return (
    <>
      {runs.map((r, i) => (
        <span key={i} style={{ fontWeight: r.bold ? 700 : 400, fontStyle: r.italic ? 'italic' : 'normal' }}>
          {r.text}
        </span>
      ))}
    </>
  )
}

// ── Document preview ───────────────────────────────────────────────────────────

function DocPreview({ filename }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['preview', filename],
    queryFn: () => previewDocument(filename),
    enabled: !!filename,
    staleTime: 0,
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading preview...</p>
    </div>
  )
  if (error) return <p className="text-sm p-6" style={{ color: '#f87171' }}>Preview failed: {error.message}</p>
  if (!data) return null

  const { extension, content } = data

  if (extension === 'docx') return (
    <div className="overflow-y-auto h-full">
      <div className="max-w-2xl mx-auto py-10 px-12" style={{ background: '#fff', minHeight: '100%', color: '#1a1a1a' }}>
        {content.map((block, i) => {
          if (block.type === 'h1') return (
            <h1 key={i} className="text-2xl font-bold mt-8 mb-3 first:mt-0"
              style={{ color: '#1A1A2E', fontFamily: 'Calibri, Arial, sans-serif', borderBottom: '2px solid #E94560', paddingBottom: '6px' }}>
              <RichText runs={block.runs} text={block.text} />
            </h1>
          )
          if (block.type === 'h2') return (
            <h2 key={i} className="text-xl font-bold mt-6 mb-2"
              style={{ color: '#E94560', fontFamily: 'Calibri, Arial, sans-serif' }}>
              <RichText runs={block.runs} text={block.text} />
            </h2>
          )
          if (block.type === 'h3') return (
            <h3 key={i} className="text-base font-semibold mt-4 mb-1"
              style={{ color: '#1A1A2E', fontFamily: 'Calibri, Arial, sans-serif' }}>
              <RichText runs={block.runs} text={block.text} />
            </h3>
          )
          if (block.type === 'bullet') return (
            <div key={i} className="flex gap-2 my-1 ml-4">
              <span style={{ color: '#E94560', flexShrink: 0 }}>•</span>
              <p className="text-sm leading-relaxed" style={{ fontFamily: 'Calibri, Arial, sans-serif', color: '#333' }}>
                <RichText runs={block.runs} text={block.text} />
              </p>
            </div>
          )
          return (
            <p key={i} className="text-sm leading-relaxed my-2"
              style={{ fontFamily: 'Calibri, Arial, sans-serif', color: '#333' }}>
              <RichText runs={block.runs} text={block.text} />
            </p>
          )
        })}
        <p className="text-xs mt-12 text-center" style={{ color: '#aaa', borderTop: '1px solid #eee', paddingTop: '12px' }}>
          CONFIDENTIAL - AgentPress Internal
        </p>
      </div>
    </div>
  )

  if (extension === 'pptx') return (
    <div className="overflow-y-auto h-full" style={{ background: '#f0f0f0' }}>
      <div className="max-w-3xl mx-auto py-8 px-6 flex flex-col gap-6">
        {content.map((slide) => {
          const allParas = (slide.shapes || []).flatMap(s => s.paragraphs || [])
          const title   = allParas[0]
          const bullets = allParas.slice(1).filter(p => p.text.trim())
          return (
            <div key={slide.index} className="rounded-xl overflow-hidden"
              style={{ background: '#fff', boxShadow: '0 2px 12px rgba(0,0,0,0.12)' }}>
              <div className="flex items-center gap-3 px-6 py-4"
                style={{ background: '#1A1A2E', borderBottom: '3px solid #E94560' }}>
                <span className="text-xs font-bold px-2 py-0.5 rounded"
                  style={{ background: '#E94560', color: '#fff' }}>{slide.index}</span>
                <h3 className="text-base font-bold"
                  style={{ color: '#EAEAEA', fontFamily: 'Calibri, Arial, sans-serif' }}>
                  {title?.text || `Slide ${slide.index}`}
                </h3>
              </div>
              {bullets.length > 0 && (
                <div className="px-6 py-5 flex flex-col gap-2.5">
                  {bullets.map((para, pi) => (
                    <div key={pi} className="flex gap-3 items-start"
                      style={{ paddingLeft: para.level > 0 ? `${para.level * 20}px` : '0' }}>
                      <span className="mt-2 shrink-0 w-1.5 h-1.5 rounded-full" style={{ background: '#E94560' }} />
                      <p className="text-sm leading-relaxed" style={{ color: '#333', fontFamily: 'Calibri, Arial, sans-serif' }}>
                        {para.text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
        <p className="text-xs text-center pb-4" style={{ color: '#aaa' }}>CONFIDENTIAL - AgentPress Internal</p>
      </div>
    </div>
  )

  if (extension === 'xlsx') return (
    <div className="overflow-y-auto h-full p-5 flex flex-col gap-8" style={{ background: 'var(--surface)' }}>
      {content.map((sheet) => (
        <div key={sheet.name}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
              style={{ background: '#1A1A2E', color: '#EAEAEA' }}>SHEET</span>
            <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>{sheet.name}</p>
          </div>
          <div className="overflow-x-auto rounded-xl"
            style={{ border: '1px solid var(--outline-var)', boxShadow: '0 1px 6px rgba(0,0,0,0.06)' }}>
            <table className="w-full text-xs border-collapse" style={{ fontFamily: 'Calibri, Arial, sans-serif' }}>
              <tbody>
                {sheet.rows.map((row, ri) => {
                  const isSectionRow = row.filter(c => c && c.trim()).length === 1 && ri > 0
                  const isColHeader  = !isSectionRow && ri > 0 && row.length > 1 &&
                    sheet.rows[ri - 1]?.filter(c => c && c.trim()).length === 1
                  if (ri === 0) return (
                    <tr key={ri} style={{ background: '#1A1A2E' }}>
                      <td colSpan={Math.max(...sheet.rows.map(r => r.length))}
                        className="px-4 py-2.5 text-sm font-bold" style={{ color: '#EAEAEA' }}>
                        {row.find(c => c && c.trim()) || ''}
                      </td>
                    </tr>
                  )
                  if (isSectionRow) return (
                    <tr key={ri} style={{ background: '#1A1A2E' }}>
                      <td colSpan={Math.max(...sheet.rows.map(r => r.length))}
                        className="px-4 py-2 text-xs font-bold uppercase tracking-wide" style={{ color: '#EAEAEA' }}>
                        {row.find(c => c && c.trim())}
                      </td>
                    </tr>
                  )
                  if (isColHeader) return (
                    <tr key={ri} style={{ background: '#E94560' }}>
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-3 py-2 font-semibold text-center"
                          style={{ color: '#fff', borderRight: ci < row.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none', whiteSpace: 'nowrap' }}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  )
                  return (
                    <tr key={ri} style={{ background: ri % 2 === 0 ? '#F5F5F8' : '#FFFFFF' }}
                      className="hover:brightness-95 transition-all">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-3 py-2"
                          style={{ color: ci === 0 ? '#1A1A2E' : '#444', fontWeight: ci === 0 ? 600 : 400,
                            borderRight: ci < row.length - 1 ? '1px solid #E8E8EC' : 'none',
                            borderBottom: '1px solid #E8E8EC', maxWidth: '280px', whiteSpace: 'normal', wordBreak: 'break-word' }}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
      <p className="text-xs text-center pb-2" style={{ color: '#aaa' }}>CONFIDENTIAL — AgentPress Internal</p>
    </div>
  )

  if (extension === 'pdf') return (
    <div className="overflow-y-auto h-full">
      <div className="max-w-2xl mx-auto py-10 px-12" style={{ background: '#fff', minHeight: '100%', color: '#1a1a1a' }}>
        {content.map((block, i) => {
          if (block.type === 'page_break') return (
            <div key={i} className="flex items-center gap-3 my-6">
              <div className="flex-1 h-px" style={{ background: '#e5e7eb' }} />
              <span className="text-[10px] uppercase tracking-widest px-2" style={{ color: '#bbb' }}>{block.text}</span>
              <div className="flex-1 h-px" style={{ background: '#e5e7eb' }} />
            </div>
          )
          if (block.type === 'h1') return (
            <h1 key={i} className="text-2xl font-bold mt-8 mb-3 first:mt-0"
              style={{ color: '#1A1A2E', fontFamily: 'Calibri, Arial, sans-serif', borderBottom: '2px solid #E94560', paddingBottom: '6px' }}>
              {block.text}
            </h1>
          )
          if (block.type === 'h2') return (
            <h2 key={i} className="text-xl font-bold mt-6 mb-2"
              style={{ color: '#E94560', fontFamily: 'Calibri, Arial, sans-serif' }}>
              {block.text}
            </h2>
          )
          if (block.type === 'bullet') return (
            <div key={i} className="flex gap-2 my-1 ml-4">
              <span style={{ color: '#E94560', flexShrink: 0 }}>•</span>
              <p className="text-sm leading-relaxed" style={{ fontFamily: 'Calibri, Arial, sans-serif', color: '#333' }}>
                {block.text}
              </p>
            </div>
          )
          return (
            <p key={i} className="text-sm leading-relaxed my-2"
              style={{ fontFamily: 'Calibri, Arial, sans-serif', color: '#333' }}>
              {block.text}
            </p>
          )
        })}
        <p className="text-xs mt-12 text-center" style={{ color: '#aaa', borderTop: '1px solid #eee', paddingTop: '12px' }}>
          CONFIDENTIAL - AgentPress Internal
        </p>
      </div>
    </div>
  )

  return <p className="p-4 text-sm" style={{ color: 'var(--on-surface-var)' }}>Preview not available.</p>
}

// ── Document chat — receives state from parent, never owns it ─────────────────

function DocChat({ filename, messages, onMessages, queryClient }) {
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [applyingIdx, setApplyingIdx] = useState(null)  // index being applied
  const [applyStatus, setApplyStatus] = useState({})    // { [idx]: 'applying'|'done'|'error' }
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const send = async () => {
    if (!input.trim() || loading) return
    const instruction = input.trim()
    const userMsg = { role: 'user', content: instruction }
    onMessages(prev => {
      const next = [...prev, userMsg]
      saveChatState(filename, next)
      return next
    })
    setInput('')
    setLoading(true)
    try {
      const history = messages.slice(-6)
      const { reply } = await chatWithDoc(filename, instruction, history)
      onMessages(prev => {
        const next = [...prev, { role: 'assistant', content: reply, instruction }]
        saveChatState(filename, next)
        return next
      })
    } catch {
      onMessages(prev => {
        const next = [...prev, { role: 'assistant', content: 'Something went wrong. Try again.' }]
        saveChatState(filename, next)
        return next
      })
    } finally {
      setLoading(false)
    }
  }

  const applyEdit = useCallback(async (msgIdx) => {
    const msg = messages[msgIdx]
    const instruction = msg.instruction || messages[msgIdx - 1]?.content || msg.content
    setApplyingIdx(msgIdx)
    setApplyStatus(s => ({ ...s, [msgIdx]: 'applying' }))
    try {
      await editDocument(filename, instruction)
      setApplyStatus(s => ({ ...s, [msgIdx]: 'done' }))
      // Invalidate preview — no remount needed
      queryClient.invalidateQueries({ queryKey: ['preview', filename] })
      onMessages(prev => {
        const next = [...prev, {
          role: 'assistant',
          content: `✅ Edit applied to **${filename}**. Preview refreshed.`,
        }]
        saveChatState(filename, next)
        return next
      })
    } catch (e) {
      setApplyStatus(s => ({ ...s, [msgIdx]: 'error' }))
      onMessages(prev => {
        const next = [...prev, {
          role: 'assistant',
          content: `❌ Edit failed: ${e.response?.data?.detail || e.message}`,
        }]
        saveChatState(filename, next)
        return next
      })
    } finally {
      setApplyingIdx(null)
    }
  }, [filename, messages, queryClient, onMessages])

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 p-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed"
              style={{
                background: msg.role === 'user' ? 'var(--primary-container)' : '#fff',
                color:      msg.role === 'user' ? 'var(--primary)' : '#333',
                border:     `1px solid ${msg.role === 'user' ? 'var(--primary)' : '#e5e7eb'}`,
              }}>
              <MarkdownMsg content={msg.content} />
            </div>

            {/* Apply Edit button — shown on assistant messages that look like edits */}
            {msg.role === 'assistant' && i > 0 && isEditSuggestion(msg.content) && (
              <button
                onClick={() => applyEdit(i)}
                disabled={applyingIdx !== null}
                className="flex items-center gap-1.5 mt-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all disabled:opacity-50"
                style={{
                  background: applyStatus[i] === 'done' ? 'rgba(68,221,193,0.15)' : 'var(--primary-container)',
                  color:      applyStatus[i] === 'done' ? '#44ddc1' : 'var(--primary)',
                  border:     `1px solid ${applyStatus[i] === 'done' ? '#44ddc1' : 'var(--primary)'}`,
                }}>
                {applyStatus[i] === 'applying' ? <><Loader size={11} className="animate-spin" /> Applying...</> :
                 applyStatus[i] === 'done'     ? <><CheckCircle size={11} /> Applied</> :
                                                 <><Pencil size={11} /> Apply Edit to File</>}
              </button>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="px-3 py-2 rounded-xl text-sm animate-pulse"
              style={{ background: 'var(--surface-highest)', color: 'var(--on-surface-var)', border: '1px solid var(--outline-var)' }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 p-3 shrink-0" style={{ borderTop: '1px solid var(--outline-var)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask about the doc or request edits..."
          className="flex-1 px-3 py-2 rounded-lg text-sm outline-none"
          style={{ background: 'var(--surface-highest)', color: 'var(--on-surface)', border: '1px solid var(--outline-var)' }}
        />
        <button onClick={send} disabled={loading || !input.trim()}
          className="p-2 rounded-lg disabled:opacity-40 transition-all"
          style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
          <Send size={14} strokeWidth={2} />
        </button>
      </div>
    </div>
  )
}

// ── Drag-to-resize handle ──────────────────────────────────────────────────────

const CHAT_MIN = 240
const CHAT_MAX = 720
const CHAT_DEFAULT = 320

function useResizable(defaultWidth) {
  const [width, setWidth] = useState(() => {
    try { return parseInt(localStorage.getItem('chat_panel_width') || defaultWidth, 10) } catch { return defaultWidth }
  })
  const dragging = useRef(false)
  const startX   = useRef(0)
  const startW   = useRef(0)

  const onMouseDown = useCallback((e) => {
    e.preventDefault()
    dragging.current = true
    startX.current   = e.clientX
    startW.current   = width

    const onMove = (ev) => {
      if (!dragging.current) return
      // Handle is on the LEFT edge of the chat panel — dragging left = wider
      const delta = startX.current - ev.clientX
      const next  = Math.min(CHAT_MAX, Math.max(CHAT_MIN, startW.current + delta))
      setWidth(next)
    }
    const onUp = () => {
      dragging.current = false
      setWidth(w => { try { localStorage.setItem('chat_panel_width', w) } catch {} return w })
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [width])

  return { width, onMouseDown }
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function DocumentReview() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['outputs'],
    queryFn: listOutputs,
    refetchInterval: 8000,
  })

  const [selected, setSelected]     = useState(null)
  const [chatsByFile, setChatsByFile] = useState({})
  const { width: chatWidth, onMouseDown: onHandleMouseDown } = useResizable(CHAT_DEFAULT)

  useEffect(() => {
    if (data?.files?.length && !selected) setSelected(data.files[0])
  }, [data])

  useEffect(() => {
    if (!selected) return
    setChatsByFile(prev => {
      if (prev[selected.name]) return prev
      return { ...prev, [selected.name]: loadChatState(selected.name) }
    })
  }, [selected?.name])

  const handleMessages = useCallback((filename, updater) => {
    setChatsByFile(prev => ({
      ...prev,
      [filename]: typeof updater === 'function' ? updater(prev[filename] || []) : updater,
    }))
  }, [])

  const currentMessages = selected ? (chatsByFile[selected.name] || loadChatState(selected.name)) : []

  return (
    <div className="flex h-screen overflow-hidden">

      {/* Left panel — file list */}
      <div className="flex flex-col w-64 shrink-0 overflow-y-auto"
        style={{ borderRight: '1px solid var(--outline-var)', background: 'var(--surface-low)' }}>
        <div className="px-4 py-4 shrink-0" style={{ borderBottom: '1px solid var(--outline-var)' }}>
          <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>Documents</p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--on-surface-var)' }}>{data?.total || 0} files</p>
        </div>
        <div className="flex flex-col gap-1 p-2">
          {isLoading && <p className="text-xs p-2 animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading...</p>}
          {data?.files?.map(f => {
            const Icon     = EXT_ICON[f.extension] || File
            const color    = EXT_COLOR[f.extension] || 'var(--on-surface-var)'
            const isActive = selected?.name === f.name
            const hasChat  = !!(chatsByFile[f.name]?.length > 1)
            return (
              <button key={f.name} onClick={() => setSelected(f)}
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left transition-all w-full"
                style={{
                  background: isActive ? 'rgba(205,189,255,0.1)' : 'transparent',
                  border: `1px solid ${isActive ? 'var(--primary)' : 'transparent'}`,
                }}>
                <Icon size={14} strokeWidth={1.75} style={{ color, flexShrink: 0 }} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium truncate"
                    style={{ color: isActive ? 'var(--primary)' : 'var(--on-surface)' }}>
                    {f.name}
                  </p>
                  <p className="text-[10px]" style={{ color: 'var(--outline)' }}>
                    {(f.size_bytes / 1024).toFixed(1)} KB
                    {hasChat && <span className="ml-1.5" style={{ color: 'var(--primary)' }}>· chat</span>}
                  </p>
                </div>
              </button>
            )
          })}
          {data?.files?.length === 0 && (
            <p className="text-xs p-2" style={{ color: 'var(--on-surface-var)' }}>No documents yet.</p>
          )}
        </div>
      </div>

      {/* Center panel — document preview (takes remaining space) */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {selected ? (
          <>
            <div className="flex items-center justify-between px-5 py-3 shrink-0"
              style={{ borderBottom: '1px solid var(--outline-var)', background: 'var(--surface-low)' }}>
              <div className="flex items-center gap-2">
                <span className="text-xs px-2 py-0.5 rounded font-mono uppercase"
                  style={{ background: 'var(--surface-highest)', color: EXT_COLOR[selected.extension] || 'var(--on-surface-var)' }}>
                  {selected.extension}
                </span>
                <p className="text-sm font-medium" style={{ color: 'var(--on-surface)' }}>{selected.name}</p>
              </div>
              <a href={getDownloadUrl(selected.name)} download
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
                <Download size={12} strokeWidth={2} />
                Download
              </a>
            </div>
            <div className="flex-1 overflow-hidden" style={{ background: 'var(--surface)' }}>
              <DocPreview filename={selected.name} />
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full flex-col gap-3"
            style={{ color: 'var(--on-surface-var)' }}>
            <FileText size={40} strokeWidth={1} style={{ opacity: 0.2 }} />
            <p className="text-sm">Select a document to preview</p>
          </div>
        )}
      </div>

      {/* Drag handle */}
      <div
        onMouseDown={onHandleMouseDown}
        className="shrink-0 flex items-center justify-center group"
        style={{
          width: '6px',
          cursor: 'col-resize',
          background: 'var(--outline-var)',
          transition: 'background 0.15s',
          zIndex: 10,
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--primary)'}
        onMouseLeave={e => e.currentTarget.style.background = 'var(--outline-var)'}
        title="Drag to resize chat panel"
      >
        {/* Grip dots */}
        <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {[0,1,2].map(i => (
            <div key={i} className="w-1 h-1 rounded-full" style={{ background: 'var(--primary)' }} />
          ))}
        </div>
      </div>

      {/* Right panel — chat (resizable width) */}
      <div className="flex flex-col shrink-0 overflow-hidden"
        style={{ width: chatWidth, borderLeft: 'none', background: 'var(--surface-low)' }}>
        <div className="px-4 py-3 shrink-0" style={{ borderBottom: '1px solid var(--outline-var)' }}>
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>Document Chat</p>
            <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(205,189,255,0.12)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
              <Pencil size={9} strokeWidth={2} /> Edits files
            </span>
          </div>
          <p className="text-xs mt-0.5" style={{ color: 'var(--on-surface-var)' }}>
            Ask questions or say "change X to Y" to edit
          </p>
        </div>
        {selected ? (
          <DocChat
            key={selected.name}
            filename={selected.name}
            messages={currentMessages}
            onMessages={(updater) => handleMessages(selected.name, updater)}
            queryClient={queryClient}
          />
        ) : (
          <p className="text-xs p-4" style={{ color: 'var(--on-surface-var)' }}>
            Select a document to start chatting.
          </p>
        )}
      </div>

    </div>
  )
}
