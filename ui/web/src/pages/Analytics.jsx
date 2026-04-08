import { useQuery } from '@tanstack/react-query'
import { getAnalytics, listJobs } from '../api/client'
import { useNavigate } from 'react-router-dom'

function StatCard({ label, value, color, sub }) {
  return (
    <div className="flex flex-col gap-1 px-5 py-4 rounded-xl"
      style={{ background: 'var(--surface-high)', border: '1px solid var(--outline-var)' }}>
      <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>{label}</p>
      <p className="text-3xl font-bold" style={{ color: color || 'var(--primary)' }}>{value ?? '—'}</p>
      {sub && <p className="text-xs" style={{ color: 'var(--outline)' }}>{sub}</p>}
    </div>
  )
}

const STATUS_COLOR = {
  completed: '#44ddc1',
  failed:    '#f87171',
  processing:'#cdbdff',
  queued:    '#948da2',
}

export default function Analytics() {
  const { data: stats } = useQuery({ queryKey: ['analytics'], queryFn: getAnalytics, refetchInterval: 5000 })
  const { data: jobsData } = useQuery({ queryKey: ['jobs'], queryFn: listJobs, refetchInterval: 5000 })
  const navigate = useNavigate()

  return (
    <div className="flex flex-col gap-8 py-10 px-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
        Analytics
      </h2>

      {/* Stat grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Jobs"     value={stats?.total_jobs}       color="var(--primary)" />
        <StatCard label="Completed"      value={stats?.completed}        color="#44ddc1" />
        <StatCard label="Failed"         value={stats?.failed}           color="#f87171" />
        <StatCard label="QA Pass Rate"   value={stats ? `${stats.qa_pass_rate}%` : null} color="#44ddc1" />
        <StatCard label="Avg QA Retries" value={stats?.avg_qa_retries}   color="#fbbf24" />
        <StatCard label="Evolutions"     value={stats?.evolution_count}  color="#f87171" sub="Meta-Engineer runs" />
        <StatCard label="Processing"     value={stats?.processing}       color="#cdbdff" />
        <StatCard label="Queued"         value={stats?.queued}           color="#948da2" />
      </div>

      {/* Job history table */}
      <div className="flex flex-col gap-3">
        <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--on-surface-var)' }}>Recent Jobs</p>
        <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--outline-var)' }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: 'var(--surface-highest)' }}>
                {['Job ID', 'Status', 'Agent', 'QA Retries', 'Evolution', 'Created'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wide"
                    style={{ color: 'var(--on-surface-var)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobsData?.jobs?.slice(0, 20).map((job, i) => (
                <tr key={job.job_id}
                  onClick={() => navigate(`/pipeline/${job.job_id}`)}
                  className="cursor-pointer transition-colors"
                  style={{ background: i % 2 === 0 ? 'var(--surface-high)' : 'var(--surface-low)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-highest)'}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'var(--surface-high)' : 'var(--surface-low)'}>
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--on-surface-var)' }}>
                    {job.job_id.slice(0, 8)}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded text-xs font-semibold"
                      style={{ color: STATUS_COLOR[job.status] || 'var(--on-surface-var)', background: `${STATUS_COLOR[job.status]}20` }}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: 'var(--on-surface-var)' }}>{job.current_node || '—'}</td>
                  <td className="px-4 py-3 text-xs" style={{ color: 'var(--on-surface-var)' }}>{job.qa_retry_count ?? 0}</td>
                  <td className="px-4 py-3 text-xs" style={{ color: job.evolution_triggered ? '#f87171' : 'var(--outline)' }}>
                    {job.evolution_triggered ? '🧬 yes' : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: 'var(--on-surface-var)' }}>
                    {job.created_at ? new Date(job.created_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!jobsData?.jobs?.length && (
            <p className="text-sm text-center py-8" style={{ color: 'var(--on-surface-var)' }}>No jobs yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
