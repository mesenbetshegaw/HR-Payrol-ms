import { useQuery } from '@tanstack/react-query'
import { getPayslips, getPayslipPDF } from '../../api/index'
import Table from '../../components/common/Table'
import { formatETB } from '../../utils/format'
import { PageSpinner } from '../../components/common/Spinner'

export default function MyPayslips() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-payslips'],
    queryFn: () => getPayslips().then(r => r.data),
  })

  const handleDownload = async (id, empId, period) => {
    const res = await getPayslipPDF(id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `payslip_${empId}_${period}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const columns = [
    { key: 'period', label: 'Period', render: r => `${r.payroll_run}` },
    { key: 'basic_salary', label: 'Basic', render: r => formatETB(r.basic_salary) },
    { key: 'gross_salary', label: 'Gross', render: r => formatETB(r.gross_salary) },
    { key: 'income_tax', label: 'Tax', render: r => formatETB(r.income_tax) },
    { key: 'employee_pension', label: 'Pension', render: r => formatETB(r.employee_pension) },
    { key: 'net_pay', label: 'Net Pay', render: r => <span className="font-bold text-green-700">{formatETB(r.net_pay)}</span> },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <button
          onClick={() => handleDownload(r.id, r.employee, r.payroll_run)}
          className="text-primary-600 hover:underline text-sm flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          PDF
        </button>
      )
    },
  ]

  if (isLoading) return <PageSpinner />

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Payslips</h1>
      <div className="card">
        <Table columns={columns} data={data?.results || data || []} loading={false} emptyMessage="No payslips yet." />
      </div>
    </div>
  )
}
