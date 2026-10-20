import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers } from '../../api/auth'
import { getPermissionMatrix, updatePermissionMatrix } from '../../api/auth'
import { PageSpinner } from '../../components/common/Spinner'
import ErrorMessage from '../../components/common/ErrorMessage'

const MODULES = ['employees', 'attendance', 'leave', 'payroll', 'reports', 'organization', 'notifications', 'audit']
const ACTIONS = ['can_view', 'can_create', 'can_edit', 'can_delete', 'can_approve']

export default function PermissionMatrix() {
  const [selectedUser, setSelectedUser] = useState(null)
  const [perms, setPerms] = useState({})
  const qc = useQueryClient()

  const { data: users } = useQuery({
    queryKey: ['users', 'SUB_ADMIN'],
    queryFn: () => getUsers({ role: 'SUB_ADMIN' }).then(r => r.data?.results || r.data),
  })

  const { data: matrix, isLoading } = useQuery({
    queryKey: ['permission-matrix', selectedUser],
    queryFn: () => getPermissionMatrix(selectedUser).then(r => r.data.permissions),
    enabled: !!selectedUser,
    onSuccess: (data) => setPerms(data),
  })

  const saveMut = useMutation({
    mutationFn: () => {
      const permissions = MODULES.map(m => ({ module: m, ...(perms[m] || {}) }))
      return updatePermissionMatrix(selectedUser, permissions)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['permission-matrix', selectedUser] }),
  })

  const toggle = (module, action) => {
    setPerms(prev => ({
      ...prev,
      [module]: { ...(prev[module] || {}), [action]: !(prev[module]?.[action]) },
    }))
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Sub Admin Permission Matrix</h1>

      <div className="card">
        <div className="flex gap-4 mb-6">
          <select
            value={selectedUser || ''}
            onChange={e => setSelectedUser(e.target.value ? Number(e.target.value) : null)}
            className="input-field max-w-xs"
          >
            <option value="">Select Sub Admin</option>
            {(users || []).map(u => <option key={u.id} value={u.id}>{u.first_name} {u.last_name} — {u.email}</option>)}
          </select>
          {selectedUser && (
            <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="btn-primary">
              {saveMut.isPending ? 'Saving...' : 'Save Permissions'}
            </button>
          )}
        </div>

        {saveMut.isSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-sm text-green-800">Permissions saved.</div>
        )}
        <ErrorMessage error={saveMut.error} className="mb-3" />

        {selectedUser && isLoading && <PageSpinner />}

        {selectedUser && !isLoading && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="table-header">Module</th>
                  {ACTIONS.map(a => <th key={a} className="table-header capitalize">{a.replace('can_', '')}</th>)}
                </tr>
              </thead>
              <tbody>
                {MODULES.map(m => (
                  <tr key={m} className="border-t hover:bg-gray-50">
                    <td className="table-cell font-medium capitalize">{m}</td>
                    {ACTIONS.map(a => (
                      <td key={a} className="table-cell text-center">
                        <input
                          type="checkbox"
                          checked={perms[m]?.[a] || false}
                          onChange={() => toggle(m, a)}
                          className="w-4 h-4 text-primary-600 rounded cursor-pointer"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!selectedUser && (
          <p className="text-gray-400 text-center py-8">Select a Sub Admin user to view and edit permissions.</p>
        )}
      </div>
    </div>
  )
}
