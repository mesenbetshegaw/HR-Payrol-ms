export default function ErrorMessage({ error, className = '' }) {
  if (!error) return null
  const msg = error?.response?.data?.errors?.detail
    || error?.response?.data?.detail
    || error?.message
    || 'Something went wrong.'
  return (
    <div className={`rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700 ${className}`}>
      {msg}
    </div>
  )
}
