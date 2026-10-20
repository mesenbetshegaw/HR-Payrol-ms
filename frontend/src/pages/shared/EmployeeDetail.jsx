import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { getEmployee, updateEmployee, getDepartments, getPositions } from '../../api/index'
import { formatDate, statusBadge, statusLabel } from '../../utils/format'
import { PageSpinner } from '../../components/common/Spinner'
import ErrorMessage from '../../components/common/ErrorMessage'

export default function EmployeeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: emp, isLoading } = useQuery({
    queryKey: ['employee', id],
    queryFn: () => getEmployee(id).then(r => r.data),
  })

  if (isLoading) return <PageSpinner />
  if (!emp) return <div className="card">Employee not found.</div>

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-gray-700">← Back</button>
        <h1 className="text-2xl font-bold text-gray-900">{emp.first_name} {emp.last_name}</h1>
        <span className={statusBadge(emp.status)}>{statusLabel(emp.status)}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Personal Information</h3>
          <dl className="space-y-3 text-sm">
            {[
              ['Employee ID', emp.employee_id],
              ['Full Name', `${emp.first_name} ${emp.last_name}`],
              ['Date of Birth', formatDate(emp.date_of_birth)],
              ['Gender', emp.gender],
              ['Nationality', emp.nationality],
              ['Phone', emp.phone_number],
              ['Personal Email', emp.personal_email],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-gray-500">{k}</dt>
                <dd className="font-medium">{v || '—'}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Employment Information</h3>
          <dl className="space-y-3 text-sm">
            {[
              ['Department', emp.department_name],
              ['Position', emp.position_name],
              ['Branch', emp.branch_name],
              ['Hire Date', formatDate(emp.hire_date)],
              ['Years of Service', `${emp.years_of_service?.toFixed(1)} years`],
              ['TIN Number', emp.tin_number],
              ['Pension Number', emp.pension_number],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-gray-500">{k}</dt>
                <dd className="font-medium">{v || '—'}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Bank Details</h3>
          <dl className="space-y-3 text-sm">
            {[
              ['Bank Name', emp.bank_name],
              ['Account Number', emp.bank_account_number],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-gray-500">{k}</dt>
                <dd className="font-medium">{v || '—'}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Emergency Contact</h3>
          <dl className="space-y-3 text-sm">
            {[
              ['Name', emp.emergency_contact_name],
              ['Phone', emp.emergency_contact_phone],
              ['Relation', emp.emergency_contact_relation],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-gray-500">{k}</dt>
                <dd className="font-medium">{v || '—'}</dd>
              </div>
            ))}
          </dl>
        </div>

        {emp.contracts?.length > 0 && (
          <div className="card md:col-span-2">
            <h3 className="font-semibold text-gray-900 mb-4">Contracts</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead><tr className="bg-gray-50">
                  <th className="table-header">Type</th>
                  <th className="table-header">Start</th>
                  <th className="table-header">End</th>
                  <th className="table-header">Active</th>
                </tr></thead>
                <tbody>
                  {emp.contracts.map(c => (
                    <tr key={c.id} className="border-t">
                      <td className="table-cell">{c.contract_type}</td>
                      <td className="table-cell">{formatDate(c.start_date)}</td>
                      <td className="table-cell">{formatDate(c.end_date) || '—'}</td>
                      <td className="table-cell">{c.is_active ? <span className="badge-green badge">Yes</span> : <span className="badge-gray badge">No</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
