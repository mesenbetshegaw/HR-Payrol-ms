import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createEmployee, getDepartments, getPositions } from '../../api/index'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  employee_id:               z.string().optional(),
  first_name:                z.string().min(1, 'First name is required'),
  last_name:                 z.string().min(1, 'Last name is required'),
  amharic_name:              z.string().optional(),
  date_of_birth:             z.string().optional(),
  gender:                    z.string().optional(),
  nationality:               z.string().optional(),
  phone_number:              z.string().optional(),
  personal_email:            z.string().email().optional().or(z.literal('')),
  tin_number:                z.string().optional(),
  pension_number:            z.string().optional(),
  bank_name:                 z.string().optional(),
  bank_account_number:       z.string().optional(),
  emergency_contact_name:    z.string().optional(),
  emergency_contact_phone:   z.string().optional(),
  emergency_contact_relation:z.string().optional(),
  department:                z.coerce.number().min(1, 'Department is required'),
  position:                  z.coerce.number().min(1, 'Position is required'),
  hire_date:                 z.string().min(1, 'Hire date is required'),
  status:                    z.string().default('ACTIVE'),
})

const Section = ({ title, children }) => (
  <div className="card mb-4">
    <h3 className="text-base font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-100">{title}</h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
  </div>
)

const Field = ({ label, required, error, children }) => (
  <div>
    <label className="label">{label}{required && <span className="text-red-500 ml-1">*</span>}</label>
    {children}
    {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
  </div>
)

export default function AddEmployee() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: depts } = useQuery({
    queryKey: ['departments'],
    queryFn: () => getDepartments().then(r => r.data?.results || r.data),
  })
  const { data: positions } = useQuery({
    queryKey: ['positions'],
    queryFn: () => getPositions().then(r => r.data?.results || r.data),
  })

  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      nationality: 'Ethiopian',
      status: 'ACTIVE',
      gender: '',
    },
  })

  const selectedDept = watch('department')

  const filteredPositions = positions?.filter(p =>
    !selectedDept || p.department === Number(selectedDept)
  ) || []

  const { mutate, isPending, error } = useMutation({
    mutationFn: (data) => createEmployee(data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['employees'] })
      navigate(`/employees/${res.data.id}`)
    },
  })

  const onSubmit = (data) => {
    // Clean empty optional fields
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    mutate(cleaned)
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/employees')} className="text-gray-500 hover:text-gray-700">
          ← Back
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Add New Employee</h1>
          <p className="text-sm text-gray-500">All fields marked * are required</p>
        </div>
      </div>

      <ErrorMessage error={error} className="mb-4" />

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Personal Information */}
        <Section title="👤 Personal Information">
          <Field label="First Name" required error={errors.first_name?.message}>
            <input {...register('first_name')} placeholder="Abebe" className={`input-field ${errors.first_name ? 'input-error' : ''}`} />
          </Field>
          <Field label="Last Name" required error={errors.last_name?.message}>
            <input {...register('last_name')} placeholder="Bekele" className={`input-field ${errors.last_name ? 'input-error' : ''}`} />
          </Field>
          <Field label="Amharic Name">
            <input {...register('amharic_name')} placeholder="አበበ በቀለ" className="input-field" />
          </Field>
          <Field label="Date of Birth">
            <input {...register('date_of_birth')} type="date" className="input-field" />
          </Field>
          <Field label="Gender">
            <select {...register('gender')} className="input-field">
              <option value="">Select gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </Field>
          <Field label="Nationality">
            <input {...register('nationality')} className="input-field" />
          </Field>
          <Field label="Phone Number">
            <input {...register('phone_number')} placeholder="+251 91 234 5678" className="input-field" />
          </Field>
          <Field label="Personal Email">
            <input {...register('personal_email')} type="email" placeholder="personal@email.com" className="input-field" />
          </Field>
        </Section>

        {/* Employment Information */}
        <Section title="💼 Employment Information">
          <Field label="Department" required error={errors.department?.message}>
            <select {...register('department')} className={`input-field ${errors.department ? 'input-error' : ''}`}>
              <option value="">Select department</option>
              {(depts || []).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </Field>
          <Field label="Position" required error={errors.position?.message}>
            <select {...register('position')} className={`input-field ${errors.position ? 'input-error' : ''}`}>
              <option value="">Select position</option>
              {(filteredPositions.length > 0 ? filteredPositions : positions || []).map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </Field>
          <Field label="Hire Date" required error={errors.hire_date?.message}>
            <input {...register('hire_date')} type="date" className={`input-field ${errors.hire_date ? 'input-error' : ''}`} />
          </Field>
          <Field label="Employment Status">
            <select {...register('status')} className="input-field">
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>
          </Field>
        </Section>

        {/* Tax & Pension */}
        <Section title="🏦 Tax, Pension & Bank">
          <Field label="TIN Number">
            <input {...register('tin_number')} placeholder="TIN123456789" className="input-field" />
          </Field>
          <Field label="Pension Number">
            <input {...register('pension_number')} placeholder="PEN123456789" className="input-field" />
          </Field>
          <Field label="Bank Name">
            <input {...register('bank_name')} placeholder="Commercial Bank of Ethiopia" className="input-field" />
          </Field>
          <Field label="Bank Account Number">
            <input {...register('bank_account_number')} placeholder="1000123456789" className="input-field" />
          </Field>
        </Section>

        {/* Emergency Contact */}
        <Section title="🆘 Emergency Contact">
          <Field label="Contact Name">
            <input {...register('emergency_contact_name')} placeholder="Contact full name" className="input-field" />
          </Field>
          <Field label="Contact Phone">
            <input {...register('emergency_contact_phone')} placeholder="+251 91 234 5678" className="input-field" />
          </Field>
          <Field label="Relationship">
            <input {...register('emergency_contact_relation')} placeholder="Spouse / Parent / Sibling" className="input-field" />
          </Field>
        </Section>

        {/* Submit */}
        <div className="flex gap-3 justify-end mt-4">
          <button type="button" onClick={() => navigate('/employees')} className="btn-secondary px-8">Cancel</button>
          <button type="submit" disabled={isPending} className="btn-primary px-8">
            {isPending ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Saving...
              </span>
            ) : '💾 Save Employee'}
          </button>
        </div>
      </form>
    </div>
  )
}
