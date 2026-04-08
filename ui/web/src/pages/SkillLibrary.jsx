import { useQuery } from '@tanstack/react-query'
import { listSkills } from '../api/client'

const CATEGORY_STYLE = {
  document_skills: { color: '#cdbdff', bg: 'rgba(205,189,255,0.1)' },
  research_skills:  { color: '#44ddc1', bg: 'rgba(68,221,193,0.1)'  },
  superpowers:      { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)'  },
}

export default function SkillLibrary() {
  const { data, isLoading } = useQuery({ queryKey: ['skills'], queryFn: listSkills })

  const allSkills = [
    ...(data?.static || []).map(s => ({ ...s, type: 'static' })),
    ...(data?.auto_generated || []).map(s => ({ ...s, type: 'generated' })),
  ]

  return (
    <div className="flex flex-col gap-8 py-10 px-8 max-w-4xl mx-auto">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
            Skill Library
          </h2>
          <p className="text-xs mt-1" style={{ color: 'var(--on-surface-var)' }}>
            All tools available to the agent pipeline
          </p>
        </div>
        {data && (
          <span className="text-xs px-3 py-1 rounded-full" style={{ background: 'var(--surface-high)', color: 'var(--on-surface-var)' }}>
            {data.total} skills
          </span>
        )}
      </div>

      {isLoading && <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading skills...</p>}

      <div className="grid grid-cols-1 gap-3">
        {allSkills.map((skill, i) => {
          const style = CATEGORY_STYLE[skill.category] || { color: '#948da2', bg: 'rgba(148,141,162,0.1)' }
          return (
            <div key={i} className="flex items-center justify-between px-4 py-3 rounded-xl"
              style={{ background: 'var(--surface-high)', border: '1px solid var(--outline-var)' }}>
              <div className="flex items-center gap-3">
                <span className="text-base">
                  {skill.category === 'document_skills' ? '📄' :
                   skill.category === 'research_skills'  ? '🔍' : '⚡'}
                </span>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--on-surface)' }}>{skill.filename}</p>
                  <p className="text-xs font-mono" style={{ color: 'var(--outline)' }}>{skill.path}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {skill.type === 'generated' && (
                  <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'rgba(248,113,113,0.1)', color: '#f87171' }}>
                    🧬 auto
                  </span>
                )}
                <span className="text-xs px-2 py-0.5 rounded font-medium"
                  style={{ background: style.bg, color: style.color }}>
                  {skill.category.replace('_', ' ')}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {allSkills.length === 0 && !isLoading && (
        <p className="text-sm" style={{ color: 'var(--on-surface-var)' }}>No skills found.</p>
      )}
    </div>
  )
}
