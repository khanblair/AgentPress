import { useState, useEffect, useRef } from 'react'

// Detect which agent emitted the log line
const AGENT_PREFIXES = [
  { key: 'orchestrator', label: 'Orchestrator', color: '#cdbdff' },
  { key: 'researcher',   label: 'Researcher',   color: '#44ddc1' },
  { key: 'synthesizer',  label: 'Synthesizer',  color: '#45d8ed' },
  { key: 'designer',     label: 'Designer',     color: '#f9a8d4' },
  { key: 'inspector',    label: 'Inspector',    color: '#fbbf24' },
  { key: 'meta_engineer',label: 'Meta-Engineer',color: '#f87171' },
]

function parseLogLine(raw) {
  const agent = AGENT_PREFIXES.find(a => raw.toLowerCase().includes(a.key)) || {
    key: 'system', label: 'System', color: '#948da2',
  }
  return { raw, agent, ts: new Date().toLocaleTimeString() }
}

export function useLogStream(maxLines = 200) {
  const [lines, setLines] = useState([])
  const esRef = useRef(null)

  useEffect(() => {
    esRef.current = new EventSource('/api/v1/logs/stream')

    esRef.current.onmessage = (e) => {
      try {
        const { line } = JSON.parse(e.data)
        setLines(prev => {
          const next = [...prev, parseLogLine(line)]
          return next.length > maxLines ? next.slice(-maxLines) : next
        })
      } catch (_) {}
    }

    esRef.current.onerror = () => esRef.current?.close()

    return () => esRef.current?.close()
  }, [maxLines])

  return lines
}
