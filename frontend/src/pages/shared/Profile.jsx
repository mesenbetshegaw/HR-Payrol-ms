import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateUser } from '../../api/auth'
import { useAuth } from '../../context/AuthContext'
import ErrorMessage from '../../components/common/ErrorMessage'

const schema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  phone_number: z.string().optional(),
})

export default function Profile() {
  const { user, reloadUser } = useAuth()
  const qc = useQueryClient()

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { first_name: user?.first_name, last_name: user?.last_name, phone_number: user?.phone_number },
  })

  const { mutate, isPending, isSuccess, error } = useMutation({
    mutationFn: (d) => updateUser(user.id, d),
    onSuccess: () => reloadUser(),
  })

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>

      <div className="card">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div>
            <h2 className="text-lg font-semibold">{user?.first_name} {user?.last_name}</h2>
            <p className="text-sm text-gray-500">{user?.email}</p>
            <span className="badge badge-blue mt-1">{user?.role?.replace('_', ' ')}</span>
          </div>
        </div>

        <ErrorMessage error={error} className="mb-4" />
        {isSuccess && <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-sm text-green-800">Profile updated successfully.</div>}

        <form onSubmit={handleSubmit(mutate)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First Name</label>
              <input {...register('first_name')} className={`input-field ${errors.first_name ? 'input-error' : ''}`} />
              {errors.first_name && <p className="text-xs text-red-500 mt-1">{errors.first_name.message}</p>}
            </div>
            <div>
              <label className="label">Last Name</label>
              <input {...register('last_name')} className={`input-field ${errors.last_name ? 'input-error' : ''}`} />
            </div>
          </div>
          <div>
            <label className="label">Phone Number</label>
            <input {...register('phone_number')} type="tel" className="input-field" />
          </div>
          <div>
            <label className="label">Email</label>
            <input value={user?.email} disabled className="input-field bg-gray-50 text-gray-500 cursor-not-allowed" />
            <p className="text-xs text-gray-400 mt-1">Email cannot be changed.</p>
          </div>
          <button type="submit" disabled={isPending} className="btn-primary">
            {isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
