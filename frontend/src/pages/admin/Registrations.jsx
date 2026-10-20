import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getRegistrations, approveRegistration, rejectRegistration } from '../../api/index'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import { statusBadge, statusLabel, formatDate } from '../../utils/format'
import ErrorMessage from '../../components/common/ErrorMessage'

export default function Registrations() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [selected, setSelected] = useState(null)
  const [rejectModal, setRejectModal] = useState(null)
  const [rejectReason, setRejectReason] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['registrations', statusFilter],
    queryFn: () => getRegistrations({ status: statusFilter || undefined }).then(r => r.data),
    refetchInterval: 15000, // auto-refresh every 15s
  })

  const approveMut = useMutation({
    mutationFn: approveRegistration,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['registrations'] })
      qc.invalidateQueries({ queryKey: ['pending-reg-count'] })
      setSelected(null)
      alert('✅ Registration approved! User account has been created.')
    },
  })

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }) => rejectRegistration(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['registrations'] })
      qc.invalidateQueries({ queryKey: ['pending-reg-count'] })
      setRejectModal(null)
      setRejectReason('')
    },
  })

  const columns = [
    { key: 'name', label: 'Applicant', render: r => <span className="font-medium">{r.first_name} {r.last_name}</span> },
    { key: 'email', label: 'Email' },
    { key: 'requested_role', label: 'Role', render: r => <span className="badge badge-blue">{r.requested_role.replace('_', ' ')}</span> },
    { key: 'department_name', label: 'Department', render: r => r.department_name || '—' },
    { key: 'position_name', label: 'Position', render: r => r.position_name || '—' },
    { key: 'submitted_at', label: 'Submitted', render: r => formatDate(r.submitted_at) },
    { key: 'status', label: 'Status', render: r => <span className={statusBadge(r.status)}>{statusLabel(r.status)}</span> },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <div className="flex gap-2">
          <button onClick={() => setSelected(r)} className="text-xs text-primary-600 hover:underline">View</button>
          {r.status === 'PENDING' && (
            <>
              <button onClick={() => approveMut.mutate(r.id)}
                className="text-xs text-green-600 hover:underline font-medium">✓ Approve</button>
              <button onClick={() => { setRejectModal(r); setRejectReason('') }}
                className="text-xs text-red-600 hover:underline">✗ Reject</button>
            </>
          )}
        </div>
      )
    },
  ]

  const pendingCount = (data?.results || data || []).filter(r => r.status === 'PENDING').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Registration Requests</h1>
          {statusFilter === 'PENDING' && pendingCount > 0 && (
            <p className="text-sm text-orange-600 mt-1">⚠️ {pendingCount} request{pendingCount !== 1 ? 's' : ''} awaiting review</p>
          )}
        </div>
      </div>

      <div className="card">
        <div className="flex gap-3 mb-4">
          {['', 'PENDING', 'APPROVED', 'REJECTED'].map(s => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === s ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}>
              {s || 'All'}
            </button>
          ))}
        </div>

        <Table columns={columns} data={data?.results || data || []} loading={isLoading}
          emptyMessage="No registration requests found." />
      </div>

      {/* Detail Modal */}
      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Registration Request Details" size="lg">
        {selected && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {[
                ['Full Name', `${selected.first_name} ${selected.last_name}`],
                ['Email', selected.email],
                ['Phone', selected.phone_number || '—'],
                ['Requested Role', selected.requested_role],
                ['Department', selected.department_name || '—'],
                ['Position', selected.position_name || '—'],
                ['Submitted', formatDate(selected.submitted_at)],
                ['Status', statusLabel(selected.status)],
              ].map(([k, v]) => (
                <div key={k}>
                  <p className="text-gray-500 text-xs">{k}</p>
                  <p className="font-medium">{v}</p>
                </div>
              ))}
            </div>

            {selected.message && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Message from applicant:</p>
                <p className="text-sm text-gray-800">{selected.message}</p>
              </div>
            )}

            {selected.status === 'REJECTED' && selected.rejection_reason && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs text-red-600 mb-1">Rejection reason:</p>
                <p className="text-sm text-red-800">{selected.rejection_reason}</p>
              </div>
            )}

            {selected.status === 'PENDING' && (
              <div className="flex gap-3 pt-2">
                <button onClick={() => { approveMut.mutate(selected.id) }}
                  disabled={approveMut.isPending}
                  className="btn-primary flex-1">
                  {approveMut.isPending ? 'Approving...' : '✓ Approve — Create Account'}
                </button>
                <button onClick={() => { setRejectModal(selected); setSelected(null) }}
                  className="btn-danger flex-1">
                  ✗ Reject
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Reject Modal */}
      <Modal isOpen={!!rejectModal} onClose={() => setRejectModal(null)} title="Reject Registration">
        {rejectModal && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Rejecting registration for <strong>{rejectModal.first_name} {rejectModal.last_name}</strong> ({rejectModal.email})
            </p>
            <div>
              <label className="label">Reason for Rejection *</label>
              <textarea
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                rows={4}
                className="input-field"
                placeholder="Please provide a clear reason why this request is being rejected..."
              />
            </div>
            <ErrorMessage error={rejectMut.error} />
            <div className="flex gap-3">
              <button onClick={() => setRejectModal(null)} className="btn-secondary flex-1">Cancel</button>
              <button
                onClick={() => rejectMut.mutate({ id: rejectModal.id, reason: rejectReason })}
                disabled={rejectMut.isPending || rejectReason.length < 5}
                className="btn-danger flex-1">
                {rejectMut.isPending ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
