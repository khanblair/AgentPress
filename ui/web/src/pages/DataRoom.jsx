import { useQuery } from '@tanstack/react-query'
import { listOutputs, getDownloadUrl } from '../api/client'

const EXT_ICON = { pptx: '📊', docx: '📝', xlsx: '📈', pdf: '📄' }

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DataRoom() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['outputs'],
    queryFn: listOutputs,
    refetchInterval: 10000,
  })

  return (
    <div className="flex flex-col gap-8 py-10 px-8 max-w-4xl mx-auto">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)', fontFamily: 'Manrope, sans-serif' }}>
            Data Room
          </h2>
          <p className="text-xs mt-1" style={{ color: 'var(--on-surface-var)' }}>All generated documents</p>
        </div>
        <button onClick={() => refetch()}
          className="text-xs px-3 py-1.5 rounded-lg transition-all"
          style={{ background: 'var(--surface-high)', color: 'var(--on-surface-var)', border: '1px solid var(--outline-var)' }}>
          ↻ Refresh
        </button>
      </div>

      {isLoading && <p className="text-sm animate-pulse" style={{ color: 'var(--on-surface-var)' }}>Loading files...</p>}

      {data?.files?.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-16" style={{ color: 'var(--on-surface-var)' }}>
          <span className="text-4xl opacity-30">🗄</span>
          <p className="text-sm">No documents yet. Run a pipeline to generate files.</p>
        </div>
      )}

      <div className="flex flex-col gap-2">
        {data?.files?.map(f => (
          <div key={f.name} className="flex items-center justify-between px-4 py-3 rounded-xl transition-all"
            style={{ background: 'var(--surface-high)', border: '1px solid var(--outline-var)' }}>
            <div className="flex items-center gap-3">
              <span className="text-xl">{EXT_ICON[f.extension] || '📄'}</span>
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--on-surface)' }}>{f.name}</p>
                <p className="text-xs" style={{ color: 'var(--on-surface-var)' }}>
                  {formatBytes(f.size_bytes)} · {new Date(f.modified_at).toLocaleString()}
                </p>
              </div>
            </div>
            <a href={getDownloadUrl(f.name)} download
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: 'var(--primary-container)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
              ↓ Download
            </a>
          </div>
        ))}
      </div>

      {data && (
        <p className="text-xs" style={{ color: 'var(--outline)' }}>
          {data.total} file{data.total !== 1 ? 's' : ''} total
        </p>
      )}
    </div>
  )
}
