import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { login } from '../../api/auth'
import { useAuth } from '../../context/AuthContext'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

export default function Login() {
  const { t, i18n } = useTranslation()
  const { loginUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  })

  const { mutate, isPending, error } = useMutation({
    mutationFn: login,
    onSuccess: ({ data }) => {
      loginUser(data.user, { access: data.access, refresh: data.refresh })
      if (data.must_change_password) {
        navigate('/change-password?forced=true')
      } else {
        navigate(from, { replace: true })
      }
    },
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl font-bold">HR</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">HR & Payroll System</h1>
          <p className="text-sm text-gray-500 mt-1">Ethiopian Human Resource Management</p>
        </div>

        <ErrorMessage error={error} className="mb-4" />

        <form onSubmit={handleSubmit(mutate)} className="space-y-5">
          <div>
            <label className="label">{t('email')}</label>
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              placeholder="admin@hrpayroll.et"
              className={`input-field ${errors.email ? 'input-error' : ''}`}
            />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="label">{t('password')}</label>
            <input
              {...register('password')}
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              className={`input-field ${errors.password ? 'input-error' : ''}`}
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <div className="flex justify-end">
            <a href="/forgot-password" className="text-sm text-primary-600 hover:text-primary-700">
              {t('forgot_password')}
            </a>
          </div>

          <button type="submit" disabled={isPending} className="btn-primary w-full py-3">
            {isPending ? 'Signing in...' : t('login')}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          Don't have an account?{' '}
          <a href="/register" className="text-primary-600 hover:underline font-medium">
            Register / Apply for Access
          </a>
        </p>

        <div className="mt-6 text-center">
          <button
            onClick={() => i18n.changeLanguage(i18n.language === 'en' ? 'am' : 'en')}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {i18n.language === 'en' ? 'አማርኛ' : 'English'}
          </button>
        </div>
      </div>
    </div>
  )
}
