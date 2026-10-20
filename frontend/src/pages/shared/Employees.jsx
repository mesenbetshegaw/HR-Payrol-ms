import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { getEmployees, exportEmployees, changeEmployeeStatus } from '../../api/index'
import { useAuth } from '../../context/AuthContext'
import Table from '../../components/common/Table'
import { statusBadge, statusLabel, formatDate } from '../../utils/format'
import { PageSpinner } from '../../components/common/Spinner'

export default function Employees() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const isHR = ['ADMIN', 'SUB_ADMIN'].includes(user?.role)

  const { data, isLoading } = useQuery({
    queryKey: ['employees', search, statusFilter, page],
    queryFn: () => getEmployees({ search, status: statusFilter || undefined, page }).then(r => r.data),
  })

  const terminateMut = useMutation({
    mutationFn: (id) => changeEmployeeStatus(id, { status: 'TERMINATED', reason: 'Terminated by admin' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['employees'] }),
  })

  const handleExport = async (fmt) => {
    try {
      const res = await exportEmployees(fmt)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `employees.${fmt}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('Export failed: ' + e.message)
    }
  }

  const employees = data?.results || []
  const totalCount = data?.count || 0

  const columns = [
    {
      key: 'employee_id', label: t('employee_id'),
      render: r => <span className="font-mono text-xs font-medium text-primary-600">{r.employee_id}</span>
    },
    {
      key: 'full_name', label: t('full_name'),
      render: r => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
            {r.first_name?.[0]}{r.last_name?.[0]}
          </div>
          <div>
            <p className="font-medium text-gray-900">{r.first_name} {r.last_name}</p>
            <p className="text-xs text-gray-400">{r.position_name || '—'}</p>
          </div>
        </div>
      )
    },
    { key: 'department_name', label: t('department'), render: r => r.department_name || '—' },
    { key: 'hire_date', label: t('hire_date'), render: r => formatDate(r.hire_date) },
    {
      key: 'status', label: t('status'),
      render: r => <span className={statusBadge(r.status)}>{statusLabel(r.status)}</span>
    },
    {
      key: 'actions', label: t('actions'),
      render: r => (
        <div className="flex items-center gap-3">
          <Link to={`/employees/${r.id}`} className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            View
          </Link>
          {isHR && (
            <Link to={`/employees/${r.id}/edit`} className="text-sm text-gray-500 hover:text-gray-700">
              Edit
            </Link>
          )}
        </div>
      )
    },
  ]

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('employees')}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{totalCount} employee{totalCount !== 1 ? 's' : ''} total</p>
        </div>
        {isHR && (
          <div className="flex gap-2">
            <button onClick={() => handleExport('csv')} className="btn-secondary text-sm gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              CSV
            </button>
            <button onClick={() => handleExport('xlsx')} className="btn-secondary text-sm">Excel</button>
            <Link to="/employees/new" className="btn-primary text-sm gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Add Employee
            </Link>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-3 mb-5">
          <div className="relative flex-1 min-w-48">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by name, ID, TIN..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="input-field pl-9"
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            className="input-field w-40"
          >
            <option value="">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="TERMINATED">Terminated</option>
            <option value="ON_LEAVE">On Leave</option>
          </select>
          {(search || statusFilter) && (
            <button onClick={() => { setSearch(''); setStatusFilter(''); setPage(1) }} className="btn-secondary text-sm">
              Clear
            </button>
          )}
        </div>

        <Table columns={columns} data={employees} loading={isLoading} emptyMessage="No employees found." />

        {/* Pagination */}
        {totalCount > 20 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">
              Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, totalCount)} of {totalCount}
            </p>
            <div className="flex gap-2">
              <button disabled={!data?.previous} onClick={() => setPage(p => p - 1)}
                className="btn-secondary text-sm disabled:opacity-40">← Previous</button>
              <span className="text-sm text-gray-500 self-center px-2">Page {page}</span>
              <button disabled={!data?.next} onClick={() => setPage(p => p + 1)}
                className="btn-secondary text-sm disabled:opacity-40">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
