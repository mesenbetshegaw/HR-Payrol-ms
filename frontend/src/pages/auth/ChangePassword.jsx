import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { changePassword } from '../../api/auth'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  old_password: z.string().min(1, 'Current password required'),
  new_password: z.string().min(8, 'At least 8 characters'),
  confirm_new_password: z.string().min(1, 'Confirm your password'),
}).refine(d => d.new_password === d.confirm_new_password, {
  message: 'Passwords do not match', path: ['confirm_new_password'],
})

export default function ChangePassword() {
  const [params] = useSearchParams()
  const isForced = params.get('forced') === 'true'
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) })

  const { mutate, isPending, error, isSuccess } = useMutation({
    mutationFn: (d) => changePassword(d),
    onSuccess: () => setTimeout(() => navigate('/dashboard'), 1500),
  })

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Change Password</h2>
        {isForced && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 text-sm text-yellow-800">
            You must change your password before continuing.
          </div>
        )}

        {isSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-sm text-green-800">
            Password changed successfully! Redirecting...
          </div>
        )}

        <ErrorMessage error={error} className="mb-4" />

        <form onSubmit={handleSubmit(mutate)} className="space-y-4">
          {['old_password', 'new_password', 'confirm_new_password'].map((f) => (
            <div key={f}>
              <label className="label">{f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</label>
              <input {...register(f)} type="password" className={`input-field ${errors[f] ? 'input-error' : ''}`} />
              {errors[f] && <p className="text-xs text-red-500 mt-1">{errors[f].message}</p>}
            </div>
          ))}
          <button type="submit" disabled={isPending} className="btn-primary w-full py-3 mt-2">
            {isPending ? 'Saving...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
