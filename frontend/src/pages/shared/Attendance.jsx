import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { getAttendance, checkIn, checkOut, approveOvertime, getMonthlySummary } from '../../api/index'
import { useAuth } from '../../context/AuthContext'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import { statusBadge, statusLabel, formatDate } from '../../utils/format'
import ErrorMessage from '../../components/common/ErrorMessage'

export default function Attendance() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const qc = useQueryClient()
  const isHR = ['ADMIN','SUB_ADMIN'].includes(user?.role)
  const isManager = ['ADMIN','MANAGER'].includes(user?.role)

  const [dateFilter, setDateFilter] = useState(new Date().toISOString().slice(0,10))
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [checkInModal, setCheckInModal] = useState(false)
  const [activeTab, setActiveTab] = useState('records')

  const { data, isLoading } = useQuery({
    queryKey: ['attendance', dateFilter, statusFilter, page],
    queryFn: () => getAttendance({
      date: dateFilter || undefined,
      status: statusFilter || undefined,
      page
    }).then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['attendance-summary'],
    queryFn: () => getMonthlySummary({
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1
    }).then(r => r.data),
    enabled: activeTab === 'summary',
  })

  const checkInMut = useMutation({
    mutationFn: checkIn,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['attendance'] }); setCheckInModal(false); reset() },
  })
  const checkOutMut = useMutation({
    mutationFn: ({ id, data }) => checkOut(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance'] }),
  })
  const approveMut = useMutation({
    mutationFn: ({ id, action }) => approveOvertime(id, action),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance'] }),
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      date: new Date().toISOString().slice(0, 10),
      check_in: '08:30',
    },
  })

  const records = data?.results || data || []
  const total = data?.count || 0

  // Stats for today
  const todayPresent  = records.filter(r => r.status === 'PRESENT').length
  const todayAbsent   = records.filter(r => r.status === 'ABSENT').length
  const todayLate     = records.filter(r => r.status === 'LATE').length
  const pendingOT     = records.filter(r => r.overtime_status === 'PENDING' && r.overtime_hours > 0).length

  const columns = [
    {
      key: 'employee_name', label: 'Employee',
      render: r => (
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
            {r.employee_name?.split(' ').map(n => n[0]).join('').slice(0,2)}
          </div>
          <span className="font-medium text-sm">{r.employee_name}</span>
        </div>
      )
    },
    { key: 'date', label: t('date'), render: r => formatDate(r.date) },
    {
      key: 'check_in', label: 'Check In',
      render: r => r.check_in
        ? <span className="text-green-600 font-mono text-sm">{r.check_in}</span>
        : <span className="text-gray-300">—</span>
    },
    {
      key: 'check_out', label: 'Check Out',
      render: r => r.check_out
        ? <span className="text-blue-600 font-mono text-sm">{r.check_out}</span>
        : <span className="text-gray-300">—</span>
    },
    {
      key: 'worked_hours', label: 'Hours',
      render: r => r.worked_hours > 0
        ? <span className="text-gray-700 font-medium">{r.worked_hours}h</span>
        : <span className="text-gray-300">—</span>
    },
    {
      key: 'status', label: t('status'),
      render: r => <span className={statusBadge(r.status)}>{statusLabel(r.status)}</span>
    },
    {
      key: 'overtime', label: 'Overtime',
      render: r => r.overtime_hours > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium text-blue-600">{r.overtime_hours}h ({r.overtime_type || 'NORMAL'})</p>
          <span className={statusBadge(r.overtime_status)}>{r.overtime_status}</span>
        </div>
      ) : <span className="text-gray-300">—</span>
    },
    {
      key: 'actions', label: t('actions'),
      render: r => (
        <div className="flex gap-2 flex-wrap">
          {r.check_in && !r.check_out && (
            <button onClick={() => checkOutMut.mutate({ id: r.id, data: { check_out: new Date().toTimeString().slice(0,5) }})}
              className="text-xs text-blue-600 hover:underline">Check Out</button>
          )}
          {isManager && r.overtime_status === 'PENDING' && r.overtime_hours > 0 && (
            <>
              <button onClick={() => approveMut.mutate({ id: r.id, action: 'approve' })}
                className="text-xs text-green-600 hover:underline font-medium">✓ OT</button>
              <button onClick={() => approveMut.mutate({ id: r.id, action: 'reject' })}
                className="text-xs text-red-500 hover:underline">✗ OT</button>
            </>
          )}
        </div>
      )
    },
  ]

  const summaryColumns = [
    { key: 'employee_name', label: 'Employee' },
    { key: 'present_days', label: 'Present', render: r => <span className="text-green-600 font-semibold">{r.present_days}</span> },
    { key: 'absent_days', label: 'Absent', render: r => <span className="text-red-500 font-semibold">{r.absent_days}</span> },
    { key: 'late_days', label: 'Late', render: r => <span className="text-yellow-600">{r.late_days}</span> },
    { key: 'half_days', label: 'Half Day', render: r => r.half_days },
    { key: 'total_overtime_hours', label: 'OT Hours', render: r => r.total_overtime_hours > 0 ? <span className="text-blue-600 font-medium">{r.total_overtime_hours}h</span> : '—' },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('attendance')}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} record{total !== 1 ? 's' : ''}</p>
        </div>
        {isHR && (
          <button onClick={() => setCheckInModal(true)} className="btn-primary text-sm">+ Manual Check-In</button>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Present', value: todayPresent, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Absent', value: todayAbsent, color: 'text-red-500', bg: 'bg-red-50' },
          { label: 'Late', value: todayLate, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'Pending OT', value: pendingOT, color: 'text-blue-600', bg: 'bg-blue-50' },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`rounded-xl p-4 ${bg}`}>
            <p className="text-xs text-gray-500">{label}</p>
            <p className={`text-2xl font-bold mt-0.5 ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {[{ key:'records', label:'Daily Records'}, { key:'summary', label:'Monthly Summary'}].map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>{tab.label}</button>
          ))}
        </nav>
      </div>

      {activeTab === 'records' && (
        <div className="card">
          <div className="flex flex-wrap gap-3 mb-4">
            <div>
              <label className="label">Date</label>
              <input type="date" value={dateFilter} onChange={e => { setDateFilter(e.target.value); setPage(1) }}
                className="input-field" />
            </div>
            <div>
              <label className="label">Status</label>
              <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="input-field">
                <option value="">All</option>
                {['PRESENT','ABSENT','LATE','HALF_DAY','ON_LEAVE','HOLIDAY'].map(s => (
                  <option key={s} value={s}>{s.replace('_',' ')}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button onClick={() => { setDateFilter(''); setStatusFilter(''); setPage(1) }} className="btn-secondary text-sm">Clear</button>
            </div>
          </div>
          <Table columns={columns} data={records} loading={isLoading} emptyMessage="No attendance records for this date." />
          {total > 20 && (
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
              <span className="text-sm text-gray-500">Page {page} of {Math.ceil(total/20)}</span>
              <div className="flex gap-2">
                <button disabled={!data?.previous} onClick={() => setPage(p => p-1)} className="btn-secondary text-sm">←</button>
                <button disabled={!data?.next} onClick={() => setPage(p => p+1)} className="btn-secondary text-sm">→</button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'summary' && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">
            Monthly Summary — {new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}
          </h3>
          <Table columns={summaryColumns} data={summaryData?.results || summaryData || []} loading={summaryLoading}
            emptyMessage="No monthly summary data. Generate summary from the attendance page." />
        </div>
      )}

      {/* Manual Check-In Modal */}
      <Modal isOpen={checkInModal} onClose={() => setCheckInModal(false)} title="Manual Attendance Entry">
        <ErrorMessage error={checkInMut.error} className="mb-3" />
        <form onSubmit={handleSubmit(d => checkInMut.mutate({
          employee_id: parseInt(d.employee_id),
          date: d.date, check_in: d.check_in, notes: d.notes || '',
        }))} className="space-y-4">
          <div>
            <label className="label">Employee ID (database ID) *</label>
            <input {...register('employee_id', { required: true })} type="number" placeholder="e.g. 1" className="input-field" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Date *</label>
              <input {...register('date', { required: true })} type="date" className="input-field" />
            </div>
            <div>
              <label className="label">Check-In Time *</label>
              <input {...register('check_in', { required: true })} type="time" className="input-field" />
            </div>
          </div>
          <div>
            <label className="label">Notes</label>
            <input {...register('notes')} className="input-field" placeholder="Optional notes" />
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setCheckInModal(false)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={checkInMut.isPending} className="btn-primary">
              {checkInMut.isPending ? 'Saving...' : '✓ Record Check-In'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
