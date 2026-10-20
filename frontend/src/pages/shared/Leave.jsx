import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import {
  getLeaveRequests, getLeaveTypes, getLeaveBalances,
  createLeaveRequest, managerApproveLeave, hrApproveLeave,
  rejectLeave, cancelLeave, getLeaveCalendar,
} from '../../api/index'
import { useAuth } from '../../context/AuthContext'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import { statusBadge, statusLabel, formatDate } from '../../utils/format'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  employee:       z.coerce.number().min(1, 'Employee required'),
  leave_type:     z.coerce.number().min(1, 'Leave type required'),
  start_date:     z.string().min(1, 'Start date required'),
  end_date:       z.string().min(1, 'End date required'),
  number_of_days: z.coerce.number().min(0.5, 'Minimum 0.5 days'),
  reason:         z.string().optional(),
}).refine(d => new Date(d.end_date) >= new Date(d.start_date), {
  message: 'End date must be after start date', path: ['end_date'],
})

export default function Leave() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const qc = useQueryClient()
  const isHR = ['ADMIN','SUB_ADMIN'].includes(user?.role)
  const isManager = ['ADMIN','MANAGER'].includes(user?.role)
  const isEmployee = user?.role === 'EMPLOYEE'

  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [requestModal, setRequestModal] = useState(false)
  const [rejectModal, setRejectModal] = useState(null)
  const [rejectReason, setRejectReason] = useState('')
  const [detailModal, setDetailModal] = useState(null)
  const [activeTab, setActiveTab] = useState('requests')

  const { data: requests, isLoading } = useQuery({
    queryKey: ['leave-requests', statusFilter, page],
    queryFn: () => getLeaveRequests({ status: statusFilter || undefined, page }).then(r => r.data),
    refetchInterval: 15000,
  })
  const { data: types }    = useQuery({ queryKey: ['leave-types'], queryFn: () => getLeaveTypes().then(r => r.data?.results || r.data) })
  const { data: balances } = useQuery({ queryKey: ['leave-balances'], queryFn: () => getLeaveBalances().then(r => r.data?.results || r.data) })

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { number_of_days: 1 },
  })

  const createMut = useMutation({
    mutationFn: createLeaveRequest,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leave-requests'] }); qc.invalidateQueries({ queryKey: ['leave-balances'] }); setRequestModal(false); reset() },
  })
  const approveMgrMut = useMutation({
    mutationFn: (id) => managerApproveLeave(id, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['leave-requests'] }),
  })
  const approveHRMut = useMutation({
    mutationFn: (id) => hrApproveLeave(id, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['leave-requests'] }),
  })
  const rejectMut = useMutation({
    mutationFn: ({ id, reason }) => rejectLeave(id, { reason }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leave-requests'] }); setRejectModal(null); setRejectReason('') },
  })
  const cancelMut = useMutation({
    mutationFn: cancelLeave,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leave-requests'] }); qc.invalidateQueries({ queryKey: ['leave-balances'] }) },
  })

  const items = requests?.results || requests || []
  const total = requests?.count || 0

  const pendingCount = items.filter(r => r.status === 'PENDING').length
  const mgrCount     = items.filter(r => r.status === 'MANAGER_APPROVED').length

  const columns = [
    {
      key: 'employee_name', label: 'Employee',
      render: r => (
        <button onClick={() => setDetailModal(r)} className="text-left">
          <p className="font-medium text-primary-600 hover:underline text-sm">{r.employee_name}</p>
          <p className="text-xs text-gray-400">{r.leave_type_name}</p>
        </button>
      )
    },
    {
      key: 'dates', label: 'Period',
      render: r => (
        <div className="text-sm">
          <p>{formatDate(r.start_date)}</p>
          <p className="text-gray-400">to {formatDate(r.end_date)}</p>
        </div>
      )
    },
    {
      key: 'number_of_days', label: t('days'),
      render: r => <span className="font-semibold text-gray-900">{r.number_of_days} {Number(r.number_of_days) === 1 ? 'day' : 'days'}</span>
    },
    {
      key: 'status', label: t('status'),
      render: r => <span className={statusBadge(r.status)}>{statusLabel(r.status)}</span>
    },
    {
      key: 'reviewed', label: 'Reviewed By',
      render: r => (
        <div className="text-xs">
          {r.manager_approved_by_name && <p className="text-blue-600">Mgr: {r.manager_approved_by_name}</p>}
          {r.hr_approved_by_name && <p className="text-green-600">HR: {r.hr_approved_by_name}</p>}
          {!r.manager_approved_by_name && !r.hr_approved_by_name && <span className="text-gray-300">—</span>}
        </div>
      )
    },
    {
      key: 'actions', label: t('actions'),
      render: r => (
        <div className="flex gap-2 flex-wrap">
          {isManager && r.status === 'PENDING' && (
            <>
              <button onClick={() => approveMgrMut.mutate(r.id)}
                className="text-xs text-green-600 hover:underline font-medium">✓ Approve</button>
              <button onClick={() => { setRejectModal(r); setRejectReason('') }}
                className="text-xs text-red-500 hover:underline">✗ Reject</button>
            </>
          )}
          {isHR && r.status === 'MANAGER_APPROVED' && (
            <button onClick={() => approveHRMut.mutate(r.id)}
              className="text-xs text-green-600 hover:underline font-medium">✓ HR Confirm</button>
          )}
          {r.status === 'PENDING' && (
            <button onClick={() => cancelMut.mutate(r.id)}
              className="text-xs text-gray-400 hover:underline">Cancel</button>
          )}
        </div>
      )
    },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('leave')}</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {pendingCount > 0 && <span className="text-yellow-600 font-medium">{pendingCount} pending · </span>}
            {mgrCount > 0 && <span className="text-blue-600 font-medium">{mgrCount} awaiting HR · </span>}
            {total} total
          </p>
        </div>
        <button onClick={() => setRequestModal(true)} className="btn-primary text-sm">+ Request Leave</button>
      </div>

      {/* Leave Balances */}
      {(balances || []).length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3 text-sm">Leave Balances — {new Date().getFullYear()}</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {(balances || []).map(b => (
              <div key={b.id} className="bg-gray-50 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">{b.leave_type_name}</p>
                <p className="text-2xl font-bold text-primary-600">{Number(b.remaining_days).toFixed(1)}</p>
                <p className="text-xs text-gray-400">of {Number(b.allocated_days).toFixed(0)} days</p>
                <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                  <div className="bg-primary-500 h-1 rounded-full"
                    style={{ width: `${Math.min(100, (b.remaining_days / b.allocated_days) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['', 'PENDING', 'MANAGER_APPROVED', 'APPROVED', 'REJECTED', 'CANCELLED'].map(s => (
          <button key={s} onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}>
            {s || 'All'}
            {s === 'PENDING' && pendingCount > 0 && (
              <span className="ml-1.5 bg-yellow-400 text-yellow-900 px-1 rounded-full">{pendingCount}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="card">
        <Table columns={columns} data={items} loading={isLoading} emptyMessage="No leave requests found." />
        {total > 20 && (
          <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
            <span className="text-sm text-gray-500">Page {page} · {total} total</span>
            <div className="flex gap-2">
              <button disabled={!requests?.previous} onClick={() => setPage(p => p-1)} className="btn-secondary text-sm">←</button>
              <button disabled={!requests?.next} onClick={() => setPage(p => p+1)} className="btn-secondary text-sm">→</button>
            </div>
          </div>
        )}
      </div>

      {/* Request Modal */}
      <Modal isOpen={requestModal} onClose={() => { setRequestModal(false); reset() }} title="Request Leave" size="md">
        <ErrorMessage error={createMut.error} className="mb-3" />
        <form onSubmit={handleSubmit(d => createMut.mutate(d))} className="space-y-4">
          {(isHR || isManager) && (
            <div>
              <label className="label">Employee ID *</label>
              <input {...register('employee')} type="number" className="input-field" placeholder="DB Employee ID" />
              {errors.employee && <p className="text-xs text-red-500 mt-1">{errors.employee.message}</p>}
            </div>
          )}
          <div>
            <label className="label">Leave Type *</label>
            <select {...register('leave_type')} className={`input-field ${errors.leave_type ? 'input-error' : ''}`}>
              <option value="">Select leave type</option>
              {(types?.results || types || []).map(t => (
                <option key={t.id} value={t.id}>{t.name} ({t.is_paid ? 'Paid' : 'Unpaid'})</option>
              ))}
            </select>
            {errors.leave_type && <p className="text-xs text-red-500 mt-1">{errors.leave_type.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Start Date *</label>
              <input {...register('start_date')} type="date" className={`input-field ${errors.start_date ? 'input-error' : ''}`} />
              {errors.start_date && <p className="text-xs text-red-500 mt-1">{errors.start_date.message}</p>}
            </div>
            <div>
              <label className="label">End Date *</label>
              <input {...register('end_date')} type="date" className={`input-field ${errors.end_date ? 'input-error' : ''}`} />
              {errors.end_date && <p className="text-xs text-red-500 mt-1">{errors.end_date.message}</p>}
            </div>
          </div>
          <div>
            <label className="label">Number of Working Days *</label>
            <input {...register('number_of_days')} type="number" step="0.5" min="0.5"
              className={`input-field ${errors.number_of_days ? 'input-error' : ''}`} />
            {errors.number_of_days && <p className="text-xs text-red-500 mt-1">{errors.number_of_days.message}</p>}
          </div>
          <div>
            <label className="label">Reason</label>
            <textarea {...register('reason')} rows={3} className="input-field"
              placeholder="Brief reason for leave..." />
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => { setRequestModal(false); reset() }} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={createMut.isPending} className="btn-primary">
              {createMut.isPending ? 'Submitting...' : '📤 Submit Request'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Detail Modal */}
      <Modal isOpen={!!detailModal} onClose={() => setDetailModal(null)} title="Leave Request Details" size="md">
        {detailModal && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Employee', detailModal.employee_name],
                ['Leave Type', detailModal.leave_type_name],
                ['Start Date', formatDate(detailModal.start_date)],
                ['End Date', formatDate(detailModal.end_date)],
                ['Days', detailModal.number_of_days],
                ['Status', statusLabel(detailModal.status)],
                ['Manager', detailModal.manager_approved_by_name || '—'],
                ['HR', detailModal.hr_approved_by_name || '—'],
              ].map(([k, v]) => (
                <div key={k} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-0.5">{k}</p>
                  <p className="font-medium text-gray-900">{v}</p>
                </div>
              ))}
            </div>
            {detailModal.reason && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">Reason</p>
                <p className="text-gray-900">{detailModal.reason}</p>
              </div>
            )}
            {detailModal.rejection_reason && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs text-red-400 mb-0.5">Rejection Reason</p>
                <p className="text-red-700">{detailModal.rejection_reason}</p>
              </div>
            )}
            {detailModal.manager_notes && (
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs text-blue-400 mb-0.5">Manager Notes</p>
                <p className="text-blue-700">{detailModal.manager_notes}</p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Reject Modal */}
      <Modal isOpen={!!rejectModal} onClose={() => setRejectModal(null)} title="Reject Leave Request">
        {rejectModal && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Rejecting leave for <strong>{rejectModal.employee_name}</strong>
              ({rejectModal.number_of_days} days — {rejectModal.leave_type_name})
            </p>
            <div>
              <label className="label">Reason for Rejection *</label>
              <textarea value={rejectReason} onChange={e => setRejectReason(e.target.value)}
                rows={3} className="input-field"
                placeholder="Please provide a clear reason..." />
            </div>
            <ErrorMessage error={rejectMut.error} />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setRejectModal(null)} className="btn-secondary">Cancel</button>
              <button onClick={() => rejectMut.mutate({ id: rejectModal.id, reason: rejectReason })}
                disabled={rejectMut.isPending || rejectReason.trim().length < 5}
                className="btn-danger">
                {rejectMut.isPending ? 'Rejecting...' : '✗ Confirm Rejection'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
