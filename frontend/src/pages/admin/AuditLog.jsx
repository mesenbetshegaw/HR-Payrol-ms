import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAuditLogs } from '../../api/index'
import Table from '../../components/common/Table'
import { formatDate } from '../../utils/format'

export default function AuditLog() {
  const [actionFilter, setActionFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', actionFilter, page],
    queryFn: () => getAuditLogs({ action: actionFilter || undefined, page }).then(r => r.data),
  })

  const columns = [
    { key: 'timestamp', label: 'Time', render: r => new Date(r.timestamp).toLocaleString() },
    { key: 'actor_email', label: 'Actor', render: r => r.actor_email || 'System' },
    { key: 'action', label: 'Action', render: r => <span className="badge badge-blue">{r.action}</span> },
    { key: 'model_name', label: 'Model', render: r => r.model_name || '—' },
    { key: 'object_repr', label: 'Object' },
    { key: 'ip_address', label: 'IP', render: r => r.ip_address || '—' },
    {
      key: 'changes', label: 'Changes',
      render: r => (r.old_value || r.new_value) ? (
        <details className="text-xs">
          <summary className="cursor-pointer text-primary-600">View</summary>
          <pre className="mt-1 bg-gray-50 p-2 rounded text-xs max-w-xs overflow-auto">
            {JSON.stringify({ old: r.old_value, new: r.new_value }, null, 2)}
          </pre>
        </details>
      ) : '—'
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
      <div className="card">
        <div className="flex gap-3 mb-4">
          <select value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1) }} className="input-field max-w-xs">
            <option value="">All Actions</option>
            {['CREATE','UPDATE','DELETE','APPROVE','REJECT','LOGIN','LOGOUT','EXPORT'].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <Table columns={columns} data={data?.results || data || []} loading={isLoading} />
        {data?.count > 20 && (
          <div className="flex justify-center gap-2 mt-4">
            <button disabled={!data?.previous} onClick={() => setPage(p => p-1)} className="btn-secondary text-sm">Previous</button>
            <span className="text-sm text-gray-500 self-center">Page {page}</span>
            <button disabled={!data?.next} onClick={() => setPage(p => p+1)} className="btn-secondary text-sm">Next</button>
          </div>
        )}
      </div>
    </div>
  )
}
