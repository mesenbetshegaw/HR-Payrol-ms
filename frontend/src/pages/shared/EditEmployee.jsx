import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { getEmployee, updateEmployee, getDepartments, getPositions } from '../../api/index'
import ErrorMessage from '../../components/common/ErrorMessage'
import { PageSpinner } from '../../components/common/Spinner'

const schema = z.object({
  first_name: z.string().min(1, 'Required'),
  last_name:  z.string().min(1, 'Required'),
  amharic_name: z.string().optional(),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  nationality: z.string().optional(),
  phone_number: z.string().optional(),
  personal_email: z.string().optional(),
  tin_number: z.string().optional(),
  pension_number: z.string().optional(),
  bank_name: z.string().optional(),
  bank_account_number: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: z.string().optional(),
  emergency_contact_relation: z.string().optional(),
  department: z.coerce.number().min(1, 'Required'),
  position: z.coerce.number().min(1, 'Required'),
  hire_date: z.string().min(1, 'Required'),
  status: z.string(),
})

export default function EditEmployee() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: emp, isLoading } = useQuery({
    queryKey: ['employee', id],
    queryFn: () => getEmployee(id).then(r => r.data),
  })
  const { data: depts } = useQuery({ queryKey: ['departments'], queryFn: () => getDepartments().then(r => r.data?.results || r.data) })
  const { data: positions } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions().then(r => r.data?.results || r.data) })

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    values: emp ? {
      first_name: emp.first_name, last_name: emp.last_name,
      amharic_name: emp.amharic_name || '',
      date_of_birth: emp.date_of_birth || '',
      gender: emp.gender || '',
      nationality: emp.nationality || 'Ethiopian',
      phone_number: emp.phone_number || '',
      personal_email: emp.personal_email || '',
      tin_number: emp.tin_number || '',
      pension_number: emp.pension_number || '',
      bank_name: emp.bank_name || '',
      bank_account_number: emp.bank_account_number || '',
      emergency_contact_name: emp.emergency_contact_name || '',
      emergency_contact_phone: emp.emergency_contact_phone || '',
      emergency_contact_relation: emp.emergency_contact_relation || '',
      department: emp.department || '',
      position: emp.position || '',
      hire_date: emp.hire_date || '',
      status: emp.status || 'ACTIVE',
    } : undefined,
  })

  const { mutate, isPending, error } = useMutation({
    mutationFn: (data) => updateEmployee(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee', id] })
      qc.invalidateQueries({ queryKey: ['employees'] })
      navigate(`/employees/${id}`)
    },
  })

  if (isLoading) return <PageSpinner />

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/employees/${id}`)} className="text-gray-500 hover:text-gray-700">← Back</button>
        <h1 className="text-2xl font-bold text-gray-900">Edit Employee: {emp?.first_name} {emp?.last_name}</h1>
      </div>
      <ErrorMessage error={error} className="mb-4" />
      <form onSubmit={handleSubmit(d => mutate(d))} className="space-y-4">
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 pb-2 border-b">Personal Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">First Name *</label><input {...register('first_name')} className="input-field" /></div>
            <div><label className="label">Last Name *</label><input {...register('last_name')} className="input-field" /></div>
            <div><label className="label">Amharic Name</label><input {...register('amharic_name')} className="input-field" /></div>
            <div><label className="label">Date of Birth</label><input {...register('date_of_birth')} type="date" className="input-field" /></div>
            <div><label className="label">Gender</label>
              <select {...register('gender')} className="input-field">
                <option value="">Select</option><option value="M">Male</option><option value="F">Female</option><option value="O">Other</option>
              </select>
            </div>
            <div><label className="label">Nationality</label><input {...register('nationality')} className="input-field" /></div>
            <div><label className="label">Phone</label><input {...register('phone_number')} className="input-field" /></div>
            <div><label className="label">Personal Email</label><input {...register('personal_email')} type="email" className="input-field" /></div>
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 pb-2 border-b">Employment</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Department *</label>
              <select {...register('department')} className="input-field">
                <option value="">Select</option>
                {(depts || []).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Position *</label>
              <select {...register('position')} className="input-field">
                <option value="">Select</option>
                {(positions || []).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div><label className="label">Hire Date *</label><input {...register('hire_date')} type="date" className="input-field" /></div>
            <div>
              <label className="label">Status</label>
              <select {...register('status')} className="input-field">
                <option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option>
                <option value="ON_LEAVE">On Leave</option><option value="TERMINATED">Terminated</option>
              </select>
            </div>
            <div><label className="label">TIN Number</label><input {...register('tin_number')} className="input-field" /></div>
            <div><label className="label">Pension Number</label><input {...register('pension_number')} className="input-field" /></div>
            <div><label className="label">Bank Name</label><input {...register('bank_name')} className="input-field" /></div>
            <div><label className="label">Bank Account</label><input {...register('bank_account_number')} className="input-field" /></div>
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 pb-2 border-b">Emergency Contact</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Name</label><input {...register('emergency_contact_name')} className="input-field" /></div>
            <div><label className="label">Phone</label><input {...register('emergency_contact_phone')} className="input-field" /></div>
            <div><label className="label">Relation</label><input {...register('emergency_contact_relation')} className="input-field" /></div>
          </div>
        </div>
        <div className="flex gap-3 justify-end">
          <button type="button" onClick={() => navigate(`/employees/${id}`)} className="btn-secondary px-8">Cancel</button>
          <button type="submit" disabled={isPending} className="btn-primary px-8">
            {isPending ? 'Saving...' : '💾 Save Changes'}
          </button>
        </div>
      </form>
    </div>
  )
}
