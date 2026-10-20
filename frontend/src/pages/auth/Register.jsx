import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { submitRegistration } from '../../api/index'
import { getDepartments, getPositions } from '../../api/index'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  first_name:      z.string().min(1, 'First name required'),
  last_name:       z.string().min(1, 'Last name required'),
  email:           z.string().email('Invalid email'),
  phone_number:    z.string().optional(),
  requested_role:  z.enum(['EMPLOYEE', 'MANAGER', 'SUB_ADMIN']),
  department:      z.coerce.number().optional().nullable(),
  position:        z.coerce.number().optional().nullable(),
  message:         z.string().optional(),
  password:        z.string().min(8, 'Minimum 8 characters'),
  confirm_password: z.string().min(1, 'Confirm your password'),
}).refine(d => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export default function Register() {
  const { t, i18n } = useTranslation()
  const [submitted, setSubmitted] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { requested_role: 'EMPLOYEE' },
  })

  const { data: depts } = useQuery({ queryKey: ['departments-public'], queryFn: () => getDepartments().then(r => r.data?.results || r.data) })
  const { data: positions } = useQuery({ queryKey: ['positions-public'], queryFn: () => getPositions().then(r => r.data?.results || r.data) })

  const { mutate, isPending, error } = useMutation({
    mutationFn: submitRegistration,
    onSuccess: () => setSubmitted(true),
  })

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Submitted!</h2>
          <p className="text-gray-600 mb-6">
            Your registration request has been sent to the administrators for review.
            You will receive a notification once it is approved.
          </p>
          <p className="text-sm text-gray-500 bg-blue-50 rounded-lg p-3 mb-6">
            <strong>What happens next:</strong><br />
            An Admin or HR Officer will review your request and either approve or reject it.
            Once approved, you can log in using your email and password.
          </p>
          <Link to="/login" className="btn-primary w-full block text-center py-3">
            Back to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center px-4 py-8">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <span className="text-white text-xl font-bold">HR</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
          <p className="text-sm text-gray-500 mt-1">Your request will be reviewed by an administrator</p>
        </div>

        <ErrorMessage error={error} className="mb-4" />

        <form onSubmit={handleSubmit(d => mutate(d))} className="space-y-4">
          {/* Name */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First Name *</label>
              <input {...register('first_name')} className={`input-field ${errors.first_name ? 'input-error' : ''}`} placeholder="Abebe" />
              {errors.first_name && <p className="text-xs text-red-500 mt-1">{errors.first_name.message}</p>}
            </div>
            <div>
              <label className="label">Last Name *</label>
              <input {...register('last_name')} className={`input-field ${errors.last_name ? 'input-error' : ''}`} placeholder="Bekele" />
              {errors.last_name && <p className="text-xs text-red-500 mt-1">{errors.last_name.message}</p>}
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="label">Email Address *</label>
            <input {...register('email')} type="email" className={`input-field ${errors.email ? 'input-error' : ''}`} placeholder="abebe@company.et" />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          {/* Phone */}
          <div>
            <label className="label">Phone Number</label>
            <input {...register('phone_number')} type="tel" className="input-field" placeholder="+251 91 234 5678" />
          </div>

          {/* Role */}
          <div>
            <label className="label">Requested Role *</label>
            <select {...register('requested_role')} className="input-field">
              <option value="EMPLOYEE">Employee</option>
              <option value="MANAGER">Manager / Team Lead</option>
              <option value="SUB_ADMIN">HR / Sub Admin</option>
            </select>
          </div>

          {/* Department & Position */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Department</label>
              <select {...register('department')} className="input-field">
                <option value="">Select...</option>
                {(depts || []).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Position</label>
              <select {...register('position')} className="input-field">
                <option value="">Select...</option>
                {(positions || []).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>

          {/* Message */}
          <div>
            <label className="label">Message / Reason for Joining</label>
            <textarea {...register('message')} rows={3} className="input-field"
              placeholder="Briefly describe why you need access to this system..." />
          </div>

          {/* Password */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Password *</label>
              <input {...register('password')} type="password" className={`input-field ${errors.password ? 'input-error' : ''}`} placeholder="Min 8 chars" />
              {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
            </div>
            <div>
              <label className="label">Confirm Password *</label>
              <input {...register('confirm_password')} type="password" className={`input-field ${errors.confirm_password ? 'input-error' : ''}`} />
              {errors.confirm_password && <p className="text-xs text-red-500 mt-1">{errors.confirm_password.message}</p>}
            </div>
          </div>

          {/* Notice */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-800">
            ⚠️ Your registration will be reviewed by an Administrator before you can log in.
            You will be notified of the decision.
          </div>

          <button type="submit" disabled={isPending} className="btn-primary w-full py-3">
            {isPending ? 'Submitting...' : 'Submit Registration Request'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 hover:underline font-medium">Sign in</Link>
        </p>

        {/* Language toggle */}
        <div className="text-center mt-3">
          <button onClick={() => i18n.changeLanguage(i18n.language === 'en' ? 'am' : 'en')}
            className="text-xs text-gray-400 hover:text-gray-600">
            {i18n.language === 'en' ? 'አማርኛ' : 'English'}
          </button>
        </div>
      </div>
    </div>
  )
}
