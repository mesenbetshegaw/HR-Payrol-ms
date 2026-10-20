import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { getUsers, createUser, unlockUser } from '../../api/auth'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import { statusBadge, formatDate } from '../../utils/format'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  email: z.string().email(),
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  role: z.enum(['ADMIN', 'SUB_ADMIN', 'MANAGER', 'EMPLOYEE']),
  password: z.string().min(8),
  confirm_password: z.string().min(1),
  must_change_password: z.boolean().optional(),
}).refine(d => d.password === d.confirm_password, { message: 'Passwords do not match', path: ['confirm_password'] })

export default function Users() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [roleFilter, setRoleFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['users', roleFilter],
    queryFn: () => getUsers({ role: roleFilter || undefined }).then(r => r.data),
  })

  const { register, handleSubmit, formState: { errors }, reset } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { must_change_password: true },
  })

  const createMut = useMutation({
    mutationFn: createUser,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setShowModal(false); reset() },
  })
  const unlockMut = useMutation({
    mutationFn: unlockUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  const columns = [
    { key: 'email', label: 'Email' },
    { key: 'full_name', label: 'Name' },
    { key: 'role', label: 'Role', render: r => <span className="badge badge-blue">{r.role.replace('_', ' ')}</span> },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-red badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
    { key: 'is_locked', label: 'Locked', render: r => r.is_locked ? <span className="badge-red badge">Locked</span> : '—' },
    { key: 'date_joined', label: 'Joined', render: r => formatDate(r.date_joined) },
    {
      key: 'actions', label: 'Actions',
      render: r => r.is_locked
        ? <button onClick={() => unlockMut.mutate(r.id)} className="text-xs text-primary-600 hover:underline">Unlock</button>
        : null
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">Add User</button>
      </div>

      <div className="card">
        <div className="flex gap-3 mb-4">
          <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)} className="input-field max-w-xs">
            <option value="">All Roles</option>
            <option value="ADMIN">Admin</option>
            <option value="SUB_ADMIN">Sub Admin</option>
            <option value="MANAGER">Manager</option>
            <option value="EMPLOYEE">Employee</option>
          </select>
        </div>
        <Table columns={columns} data={data?.results || data || []} loading={isLoading} />
      </div>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Create User">
        <ErrorMessage error={createMut.error} className="mb-3" />
        <form onSubmit={handleSubmit(d => createMut.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First Name</label>
              <input {...register('first_name')} className={`input-field ${errors.first_name ? 'input-error' : ''}`} />
            </div>
            <div>
              <label className="label">Last Name</label>
              <input {...register('last_name')} className={`input-field ${errors.last_name ? 'input-error' : ''}`} />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <input {...register('email')} type="email" className={`input-field ${errors.email ? 'input-error' : ''}`} />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>
          <div>
            <label className="label">Role</label>
            <select {...register('role')} className="input-field">
              <option value="EMPLOYEE">Employee</option>
              <option value="MANAGER">Manager</option>
              <option value="SUB_ADMIN">Sub Admin</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Password</label>
              <input {...register('password')} type="password" className={`input-field ${errors.password ? 'input-error' : ''}`} />
              {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
            </div>
            <div>
              <label className="label">Confirm Password</label>
              <input {...register('confirm_password')} type="password" className={`input-field ${errors.confirm_password ? 'input-error' : ''}`} />
              {errors.confirm_password && <p className="text-xs text-red-500 mt-1">{errors.confirm_password.message}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input {...register('must_change_password')} type="checkbox" id="must_change" />
            <label htmlFor="must_change" className="text-sm text-gray-700">Force password change on first login</label>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={createMut.isPending} className="btn-primary">Create User</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
