import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { generateDocument } from '../api/client'

const FORMATS = ['docx', 'pptx', 'xlsx', 'pdf']

const TEMPLATES = [
  {
    category: 'Presentations',
    items: [
      {
        label: 'Investor Deck',
        format: 'pptx',
        prompt: 'Create a 10-slide Series A investor deck for a B2B SaaS startup. Include problem statement, solution, market size (TAM/SAM/SOM), business model, traction metrics, competitive landscape, team, and funding ask.',
      },
      {
        label: 'Product Roadmap',
        format: 'pptx',
        prompt: 'Create a 6-slide product roadmap presentation for Q3–Q4. Include current state, strategic priorities, feature releases by quarter, dependencies, success metrics, and a visual timeline.',
      },
      {
        label: 'Quarterly Business Review',
        format: 'pptx',
        prompt: 'Create an 8-slide QBR presentation covering Q2 performance. Include executive summary, KPI scorecard, revenue vs target, key wins, missed targets with root cause, customer highlights, and Q3 outlook.',
      },
    ],
  },
  {
    category: 'Reports',
    items: [
      {
        label: 'Market Research Report',
        format: 'docx',
        prompt: 'Write a comprehensive market research report on the AI document automation industry. Cover market size, growth drivers, key players, customer segments, pricing trends, and a 3-year forecast.',
      },
      {
        label: 'Competitive Analysis',
        format: 'docx',
        prompt: 'Write a competitive analysis report comparing the top 5 AI writing tools. Evaluate each on features, pricing, target audience, strengths, weaknesses, and market positioning. Include a comparison matrix.',
      },
      {
        label: 'Executive Summary',
        format: 'docx',
        prompt: 'Write a 2-page executive summary for a new enterprise AI platform launch. Cover the business opportunity, proposed solution, go-to-market strategy, financial projections, and key risks.',
      },
    ],
  },
  {
    category: 'Data & Spreadsheets',
    items: [
      {
        label: 'Financial Model',
        format: 'xlsx',
        prompt: 'Create a 3-year financial model spreadsheet for a SaaS startup. Include revenue projections (MRR/ARR), cost structure, headcount plan, burn rate, runway, and key unit economics (CAC, LTV, churn).',
      },
      {
        label: 'Project Tracker',
        format: 'xlsx',
        prompt: 'Create a project tracker spreadsheet for a 6-month product launch. Include task list, owner, priority, status, start date, due date, dependencies, and a progress summary dashboard.',
      },
    ],
  },
  {
    category: 'PDF Documents',
    items: [
      {
        label: 'Business Proposal',
        format: 'pdf',
        prompt: 'Write a professional business proposal PDF for an enterprise AI automation service. Include executive summary, problem statement, proposed solution, scope of work, timeline, pricing, team credentials, and next steps.',
      },
      {
        label: 'Strategy Report',
        format: 'pdf',
        prompt: 'Write a strategic planning report PDF for a tech company entering a new market. Cover market opportunity, strategic objectives, competitive positioning, go-to-market plan, resource requirements, risk assessment, and success metrics.',
      },
      {
        label: 'Project Brief',
        format: 'pdf',
        prompt: 'Write a project brief PDF for a 90-day digital transformation initiative. Include project background, objectives, deliverables, stakeholders, timeline with milestones, budget overview, risks, and approval sign-off section.',
      },
    ],
  },
]

export default function MainWorkspace() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [format, setFormat] = useState('docx')
  const [sessionId] = useState(() => crypto.randomUUID())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const applyTemplate = (tpl) => {
    setPrompt(tpl.prompt)
    setFormat(tpl.format)
  }

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError(null)
    try {
      const { job_id } = await generateDocument(prompt, sessionId, format)
      navigate(`/pipeline/${job_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-8 max-w-3xl mx-auto py-12 px-6">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--primary)', fontFamily: 'Manrope, sans-serif' }}>
          AgentPress
        </h1>
        <p className="mt-1 text-sm" style={{ color: 'var(--on-surface-var)' }}>
          Brand-aware autonomous document pipeline
        </p>
      </div>

      {/* Templates */}
      <div className="flex flex-col gap-4">
        <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>
          Quick Templates
        </label>
        <div className="flex flex-col gap-4">
          {TEMPLATES.map(group => (
            <div key={group.category} className="flex flex-col gap-2">
              <p className="text-xs" style={{ color: 'var(--outline)' }}>{group.category}</p>
              <div className="flex flex-wrap gap-2">
                {group.items.map(tpl => (
                  <button
                    key={tpl.label}
                    onClick={() => applyTemplate(tpl)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                    style={{
                      background: prompt === tpl.prompt ? 'rgba(205,189,255,0.15)' : 'var(--surface-high)',
                      color: prompt === tpl.prompt ? 'var(--primary)' : 'var(--on-surface-var)',
                      border: `1px solid ${prompt === tpl.prompt ? 'var(--primary)' : 'var(--outline-var)'}`,
                    }}
                  >
                    <span className="uppercase font-bold text-[10px] px-1 py-0.5 rounded"
                      style={{
                        background: 'var(--surface-highest)',
                        color: tpl.format === 'pptx' ? '#f9a8d4'
                             : tpl.format === 'xlsx' ? '#44ddc1'
                             : tpl.format === 'pdf'  ? '#fbbf24'
                             : 'var(--primary)',
                      }}>
                      {tpl.format}
                    </span>
                    {tpl.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prompt */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>
            Document Request
          </label>
          {prompt && (
            <button onClick={() => setPrompt('')} className="text-xs transition-opacity hover:opacity-100 opacity-50"
              style={{ color: 'var(--on-surface-var)' }}>
              Clear
            </button>
          )}
        </div>
        <textarea
          rows={6}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Describe the document you want to generate, or pick a template above..."
          className="w-full resize-none rounded-xl px-4 py-3 text-sm outline-none transition-all"
          style={{
            background: 'var(--surface-highest)',
            color: 'var(--on-surface)',
            border: '1px solid var(--outline-var)',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--primary)'}
          onBlur={e => e.target.style.borderColor = 'var(--outline-var)'}
        />
      </div>

      {/* Format picker */}
      <div className="flex flex-col gap-3">
        <label className="text-xs font-medium uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>
          Output Format
        </label>
        <div className="flex gap-2">
          {FORMATS.map(f => (
            <button key={f} onClick={() => setFormat(f)}
              className="px-4 py-2 rounded-lg text-sm font-medium uppercase tracking-wide transition-all"
              style={{
                background: format === f ? 'var(--primary-container)' : 'var(--surface-high)',
                color: format === f ? 'var(--primary)' : 'var(--on-surface-var)',
                border: `1px solid ${format === f ? 'var(--primary)' : 'var(--outline-var)'}`,
              }}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="text-sm px-4 py-3 rounded-lg" style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171', border: '1px solid #f87171' }}>
          {error}
        </p>
      )}

      {/* CTA */}
      <div className="flex items-center gap-4">
        <button onClick={handleGenerate} disabled={loading || !prompt.trim()}
          className="flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-40"
          style={{
            background: loading ? 'var(--surface-high)' : 'var(--primary-container)',
            color: 'var(--primary)',
            border: '1px solid var(--primary)',
          }}>
          <Zap size={14} strokeWidth={2} />
          {loading ? 'Launching pipeline...' : 'Generate Document'}
        </button>
        <p className="text-xs" style={{ color: 'var(--outline)' }}>
          Session <code style={{ color: 'var(--on-surface-var)' }}>{sessionId.slice(0, 8)}</code>
        </p>
      </div>

    </div>
  )
}
