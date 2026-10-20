import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../../api/auth'

const schema = z.object({ email: z.string().email('Invalid email') })

export default function ForgotPassword() {
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) })
  const { mutate, isPending, isSuccess } = useMutation({ mutationFn: (d) => forgotPassword(d.email) })

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-1">Forgot Password</h2>
        <p className="text-sm text-gray-500 mb-6">Enter your email and we'll send a reset link.</p>

        {isSuccess ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
            If that email is registered, a reset link has been sent. Check your inbox.
          </div>
        ) : (
          <form onSubmit={handleSubmit(mutate)} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input {...register('email')} type="email" className={`input-field ${errors.email ? 'input-error' : ''}`} />
              {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
            </div>
            <button type="submit" disabled={isPending} className="btn-primary w-full py-3">
              {isPending ? 'Sending...' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <p className="text-center text-sm text-gray-500 mt-4">
          <Link to="/login" className="text-primary-600 hover:underline">Back to Login</Link>
        </p>
      </div>
    </div>
  )
}
