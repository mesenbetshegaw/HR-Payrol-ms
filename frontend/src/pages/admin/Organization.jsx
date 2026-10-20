import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  getDepartments, createDepartment, updateDepartment, deleteDepartment,
  getPositions, createPosition, updatePosition, deletePosition,
  getBranches, createBranch, updateBranch,
  getHolidays, createHoliday, deleteHoliday,
} from '../../api/index'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import ErrorMessage from '../../components/common/ErrorMessage'
import { formatDate } from '../../utils/format'

const tabs = ['Departments', 'Positions', 'Branches', 'Holidays']

const deptSchema = z.object({ name: z.string().min(1), code: z.string().min(1), description: z.string().optional() })
const posSchema = z.object({ name: z.string().min(1), department: z.coerce.number().min(1), grade: z.string().optional() })
const branchSchema = z.object({ name: z.string().min(1), city: z.string().min(1), address: z.string().optional() })
const holidaySchema = z.object({ name: z.string().min(1), date: z.string().min(1), holiday_type: z.enum(['NATIONAL', 'RELIGIOUS', 'REGIONAL']) })

export default function Organization() {
  const [tab, setTab] = useState('Departments')
  const [modal, setModal] = useState(null)
  const qc = useQueryClient()

  // Departments
  const depts = useQuery({ queryKey: ['departments'], queryFn: () => getDepartments().then(r => r.data?.results || r.data) })
  const positions = useQuery({ queryKey: ['positions'], queryFn: () => getPositions().then(r => r.data?.results || r.data) })
  const branches = useQuery({ queryKey: ['branches'], queryFn: () => getBranches().then(r => r.data?.results || r.data) })
  const holidays = useQuery({ queryKey: ['holidays'], queryFn: () => getHolidays().then(r => r.data?.results || r.data) })

  const deptMut = useMutation({ mutationFn: createDepartment, onSuccess: () => { qc.invalidateQueries(['departments']); setModal(null) } })
  const posMut = useMutation({ mutationFn: createPosition, onSuccess: () => { qc.invalidateQueries(['positions']); setModal(null) } })
  const branchMut = useMutation({ mutationFn: createBranch, onSuccess: () => { qc.invalidateQueries(['branches']); setModal(null) } })
  const holidayMut = useMutation({ mutationFn: createHoliday, onSuccess: () => { qc.invalidateQueries(['holidays']); setModal(null) } })
  const delHolidayMut = useMutation({ mutationFn: deleteHoliday, onSuccess: () => qc.invalidateQueries(['holidays']) })

  const deptForm = useForm({ resolver: zodResolver(deptSchema) })
  const posForm = useForm({ resolver: zodResolver(posSchema) })
  const branchForm = useForm({ resolver: zodResolver(branchSchema) })
  const holidayForm = useForm({ resolver: zodResolver(holidaySchema) })

  const deptCols = [
    { key: 'name', label: 'Name' },
    { key: 'code', label: 'Code' },
    { key: 'description', label: 'Description', render: r => r.description || '—' },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
  ]

  const posCols = [
    { key: 'name', label: 'Name' },
    { key: 'department_name', label: 'Department' },
    { key: 'grade', label: 'Grade', render: r => r.grade || '—' },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
  ]

  const branchCols = [
    { key: 'name', label: 'Name' },
    { key: 'city', label: 'City' },
    { key: 'address', label: 'Address', render: r => r.address || '—' },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
  ]

  const holidayCols = [
    { key: 'name', label: 'Name' },
    { key: 'date', label: 'Date', render: r => formatDate(r.date) },
    { key: 'holiday_type', label: 'Type' },
    {
      key: 'actions', label: 'Actions',
      render: r => <button onClick={() => delHolidayMut.mutate(r.id)} className="text-red-600 hover:underline text-xs">Delete</button>
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Organization</h1>
        <button onClick={() => setModal(tab)} className="btn-primary">Add {tab.slice(0, -1)}</button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t}
            </button>
          ))}
        </nav>
      </div>

      <div className="card">
        {tab === 'Departments' && <Table columns={deptCols} data={depts.data || []} loading={depts.isLoading} />}
        {tab === 'Positions' && <Table columns={posCols} data={positions.data || []} loading={positions.isLoading} />}
        {tab === 'Branches' && <Table columns={branchCols} data={branches.data || []} loading={branches.isLoading} />}
        {tab === 'Holidays' && <Table columns={holidayCols} data={holidays.data || []} loading={holidays.isLoading} />}
      </div>

      {/* Department Modal */}
      <Modal isOpen={modal === 'Departments'} onClose={() => setModal(null)} title="Add Department">
        <ErrorMessage error={deptMut.error} className="mb-3" />
        <form onSubmit={deptForm.handleSubmit(d => deptMut.mutate(d))} className="space-y-4">
          <div><label className="label">Name</label><input {...deptForm.register('name')} className="input-field" /></div>
          <div><label className="label">Code</label><input {...deptForm.register('code')} className="input-field" /></div>
          <div><label className="label">Description</label><textarea {...deptForm.register('description')} rows={2} className="input-field" /></div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={deptMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>

      {/* Position Modal */}
      <Modal isOpen={modal === 'Positions'} onClose={() => setModal(null)} title="Add Position">
        <ErrorMessage error={posMut.error} className="mb-3" />
        <form onSubmit={posForm.handleSubmit(d => posMut.mutate(d))} className="space-y-4">
          <div><label className="label">Name</label><input {...posForm.register('name')} className="input-field" /></div>
          <div>
            <label className="label">Department</label>
            <select {...posForm.register('department')} className="input-field">
              <option value="">Select department</option>
              {(depts.data || []).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div><label className="label">Grade</label><input {...posForm.register('grade')} className="input-field" /></div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={posMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>

      {/* Branch Modal */}
      <Modal isOpen={modal === 'Branches'} onClose={() => setModal(null)} title="Add Branch">
        <ErrorMessage error={branchMut.error} className="mb-3" />
        <form onSubmit={branchForm.handleSubmit(d => branchMut.mutate(d))} className="space-y-4">
          <div><label className="label">Name</label><input {...branchForm.register('name')} className="input-field" /></div>
          <div><label className="label">City</label><input {...branchForm.register('city')} className="input-field" /></div>
          <div><label className="label">Address</label><textarea {...branchForm.register('address')} rows={2} className="input-field" /></div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={branchMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>

      {/* Holiday Modal */}
      <Modal isOpen={modal === 'Holidays'} onClose={() => setModal(null)} title="Add Holiday">
        <ErrorMessage error={holidayMut.error} className="mb-3" />
        <form onSubmit={holidayForm.handleSubmit(d => holidayMut.mutate(d))} className="space-y-4">
          <div><label className="label">Name</label><input {...holidayForm.register('name')} className="input-field" /></div>
          <div><label className="label">Date</label><input {...holidayForm.register('date')} type="date" className="input-field" /></div>
          <div>
            <label className="label">Type</label>
            <select {...holidayForm.register('holiday_type')} className="input-field">
              <option value="NATIONAL">National</option>
              <option value="RELIGIOUS">Religious</option>
              <option value="REGIONAL">Regional</option>
            </select>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={holidayMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
