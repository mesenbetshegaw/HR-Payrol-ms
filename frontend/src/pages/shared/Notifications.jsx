import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getNotifications, markRead, markAllRead } from '../../api/index'
import { PageSpinner } from '../../components/common/Spinner'

export default function Notifications() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => getNotifications().then(r => r.data),
  })

  const readMut = useMutation({
    mutationFn: markRead,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifications'] }); qc.invalidateQueries({ queryKey: ['unread-count'] }) },
  })

  const readAllMut = useMutation({
    mutationFn: markAllRead,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifications'] }); qc.invalidateQueries({ queryKey: ['unread-count'] }) },
  })

  if (isLoading) return <PageSpinner />

  const items = data?.results || data || []

  const categoryColor = {
    leave: 'bg-blue-50 border-blue-200',
    payroll: 'bg-green-50 border-green-200',
    attendance: 'bg-yellow-50 border-yellow-200',
    general: 'bg-gray-50 border-gray-200',
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
        {items.some(n => !n.is_read) && (
          <button onClick={() => readAllMut.mutate()} disabled={readAllMut.isPending}
            className="btn-secondary text-sm">Mark All Read</button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">No notifications yet.</div>
      ) : (
        <div className="space-y-3">
          {items.map(n => (
            <div
              key={n.id}
              className={`rounded-xl border p-4 flex items-start gap-3 transition-opacity ${
                n.is_read ? 'opacity-60' : ''
              } ${categoryColor[n.category] || categoryColor.general}`}
            >
              <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${n.is_read ? 'bg-gray-300' : 'bg-primary-500'}`} />
              <div className="flex-1">
                <p className="text-sm text-gray-800">{n.message}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</span>
                  <span className="text-xs text-gray-500 capitalize">{n.category}</span>
                </div>
              </div>
              {!n.is_read && (
                <button onClick={() => readMut.mutate(n.id)}
                  className="text-xs text-primary-600 hover:underline flex-shrink-0">Mark read</button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
