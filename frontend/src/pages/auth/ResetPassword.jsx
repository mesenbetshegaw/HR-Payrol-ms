import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { resetPassword } from '../../api/auth'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  new_password: z.string().min(8, 'At least 8 characters'),
  confirm_new_password: z.string().min(1),
}).refine(d => d.new_password === d.confirm_new_password, {
  message: 'Passwords do not match', path: ['confirm_new_password'],
})

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) })
  const { mutate, isPending, error, isSuccess } = useMutation({
    mutationFn: (d) => resetPassword({ ...d, token }),
    onSuccess: () => setTimeout(() => navigate('/login'), 2000),
  })

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Reset Password</h2>

        {isSuccess ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
            Password reset successfully! Redirecting to login...
          </div>
        ) : (
          <>
            <ErrorMessage error={error} className="mb-4" />
            <form onSubmit={handleSubmit(mutate)} className="space-y-4">
              <div>
                <label className="label">New Password</label>
                <input {...register('new_password')} type="password" className={`input-field ${errors.new_password ? 'input-error' : ''}`} />
                {errors.new_password && <p className="text-xs text-red-500 mt-1">{errors.new_password.message}</p>}
              </div>
              <div>
                <label className="label">Confirm Password</label>
                <input {...register('confirm_new_password')} type="password" className={`input-field ${errors.confirm_new_password ? 'input-error' : ''}`} />
                {errors.confirm_new_password && <p className="text-xs text-red-500 mt-1">{errors.confirm_new_password.message}</p>}
              </div>
              <button type="submit" disabled={isPending || !token} className="btn-primary w-full py-3">
                {isPending ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          </>
        )}
        <p className="text-center text-sm text-gray-500 mt-4">
          <Link to="/login" className="text-primary-600 hover:underline">Back to Login</Link>
        </p>
      </div>
    </div>
  )
}
