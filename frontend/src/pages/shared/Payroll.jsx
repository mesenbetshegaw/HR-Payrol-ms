import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  getPayrollRuns, createPayrollRun, generatePayslips, advancePayroll,
  getBankTransfer, getPayslips, getPayslipPDF, updateSalaryStructure,
  getSalaryStructures, createSalaryStructure,
} from '../../api/index'
import { useAuth } from '../../context/AuthContext'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import { statusBadge, statusLabel, formatETB, formatDate } from '../../utils/format'
import ErrorMessage from '../../components/common/ErrorMessage'
import { PageSpinner } from '../../components/common/Spinner'

const statusFlow = { DRAFT:'REVIEWED', REVIEWED:'APPROVED', APPROVED:'PAID' }
const statusColor = { DRAFT:'badge-gray', REVIEWED:'badge-yellow', APPROVED:'badge-green', PAID:'badge-blue' }
const nextActionLabel = { DRAFT:'Mark Reviewed', REVIEWED:'Approve (Admin)', APPROVED:'Mark Paid' }

export default function Payroll() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const isAdmin = user?.role === 'ADMIN'
  const isHR = ['ADMIN','SUB_ADMIN'].includes(user?.role)

  const [activeTab, setActiveTab] = useState('runs')
  const [selectedRun, setSelectedRun] = useState(null)
  const [newRunModal, setNewRunModal] = useState(false)
  const [newRunData, setNewRunData] = useState({ year: new Date().getFullYear(), month: new Date().getMonth() + 1 })
  const [editPayslip, setEditPayslip] = useState(null)
  const [salaryModal, setSalaryModal] = useState(false)
  const [salaryForm, setSalaryForm] = useState({})

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ['payroll-runs'],
    queryFn: () => getPayrollRuns().then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: payslipsData, isLoading: payslipsLoading } = useQuery({
    queryKey: ['payslips', selectedRun?.id],
    queryFn: () => getPayslips({ payroll_run: selectedRun?.id }).then(r => r.data),
    enabled: !!selectedRun,
  })

  const { data: salariesData, isLoading: salariesLoading } = useQuery({
    queryKey: ['salary-structures'],
    queryFn: () => getSalaryStructures().then(r => r.data),
    enabled: activeTab === 'salaries',
  })

  // ── Mutations ──────────────────────────────────────────────────────────────
  const createRunMut = useMutation({
    mutationFn: createPayrollRun,
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ['payroll-runs'] })
      setNewRunModal(false)
      setSelectedRun(r.data)
    },
  })

  const generateMut = useMutation({
    mutationFn: (id) => generatePayslips(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['payroll-runs'] })
      qc.invalidateQueries({ queryKey: ['payslips', id] })
    },
  })

  const advanceMut = useMutation({
    mutationFn: ({ id, notes }) => advancePayroll(id, { notes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['payroll-runs'] })
      if (selectedRun) {
        const updated = (runsData?.results || runsData || []).find(r => r.id === selectedRun.id)
        if (updated) setSelectedRun(updated)
      }
    },
  })

  const saveSalaryMut = useMutation({
    mutationFn: (d) => d.id ? updateSalaryStructure(d.id, d) : createSalaryStructure(d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['salary-structures'] }); setSalaryModal(false) },
  })

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleDownloadPDF = async (payslipId, empId, period) => {
    try {
      const res = await getPayslipPDF(payslipId)
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `payslip_${empId}_${period}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch { alert('Failed to download PDF') }
  }

  const handleBankExport = async (runId, period) => {
    try {
      const res = await getBankTransfer(runId)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `bank_transfer_${period}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch { alert('Failed to export bank transfer list') }
  }

  const runs = runsData?.results || runsData || []
  const payslips = payslipsData?.results || payslipsData || []
  const salaries = salariesData?.results || salariesData || []

  const canAdvance = (run) => {
    if (!run) return false
    if (run.status === 'PAID') return false
    if (run.status === 'REVIEWED' && !isAdmin) return false
    if (run.status === 'APPROVED' && !isAdmin) return false
    return isHR
  }

  // ── Run columns ────────────────────────────────────────────────────────────
  const runColumns = [
    {
      key: 'period', label: 'Period',
      render: r => (
        <button onClick={() => setSelectedRun(r)}
          className={`font-mono font-semibold text-sm ${selectedRun?.id === r.id ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`}>
          {r.year}/{String(r.month).padStart(2,'0')}
        </button>
      )
    },
    { key: 'status', label: 'Status', render: r => <span className={`badge ${statusColor[r.status]}`}>{statusLabel(r.status)}</span> },
    { key: 'payslip_count', label: 'Employees', render: r => <span className="font-medium">{r.payslip_count}</span> },
    { key: 'total_gross', label: 'Gross', render: r => <span className="text-gray-700">{formatETB(r.total_gross)}</span> },
    { key: 'total_net', label: 'Net Pay', render: r => <span className="text-green-600 font-semibold">{formatETB(r.total_net)}</span> },
    { key: 'total_tax', label: 'Tax', render: r => <span className="text-red-500">{formatETB(r.total_tax)}</span> },
    { key: 'prepared_by_name', label: 'Prepared By', render: r => r.prepared_by_name || '—' },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setSelectedRun(r)} className="text-xs text-primary-600 hover:underline">
            {selectedRun?.id === r.id ? '▼ Active' : 'Select'}
          </button>
          {isHR && r.status === 'DRAFT' && r.payslip_count === 0 && (
            <button onClick={() => generateMut.mutate(r.id)}
              disabled={generateMut.isPending}
              className="text-xs text-blue-600 hover:underline">
              ⚙ Generate
            </button>
          )}
          {canAdvance(r) && (
            <button onClick={() => advanceMut.mutate({ id: r.id })}
              disabled={advanceMut.isPending}
              className="text-xs text-green-600 hover:underline font-medium">
              → {nextActionLabel[r.status]}
            </button>
          )}
          {['APPROVED','PAID'].includes(r.status) && (
            <button onClick={() => handleBankExport(r.id, `${r.year}-${String(r.month).padStart(2,'0')}`)}
              className="text-xs text-gray-500 hover:underline">
              📊 Bank
            </button>
          )}
        </div>
      )
    },
  ]

  // ── Payslip columns ────────────────────────────────────────────────────────
  const payslipColumns = [
    {
      key: 'employee', label: 'Employee',
      render: r => (
        <div>
          <p className="font-medium text-gray-900 text-sm">{r.employee_name}</p>
        </div>
      )
    },
    { key: 'basic_salary', label: 'Basic', render: r => formatETB(r.basic_salary) },
    { key: 'taxable_allowances', label: 'Allowances', render: r => formatETB(r.taxable_allowances) },
    { key: 'overtime_pay', label: 'Overtime', render: r => r.overtime_pay > 0 ? <span className="text-blue-600">{formatETB(r.overtime_pay)}</span> : '—' },
    { key: 'bonus', label: 'Bonus', render: r => r.bonus > 0 ? <span className="text-green-600">{formatETB(r.bonus)}</span> : '—' },
    { key: 'gross_salary', label: 'Gross', render: r => <span className="font-medium">{formatETB(r.gross_salary)}</span> },
    { key: 'income_tax', label: 'Tax', render: r => <span className="text-red-500">{formatETB(r.income_tax)}</span> },
    { key: 'employee_pension', label: 'Pension', render: r => formatETB(r.employee_pension) },
    { key: 'net_pay', label: 'Net Pay', render: r => <span className="text-green-600 font-bold">{formatETB(r.net_pay)}</span> },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <div className="flex gap-2">
          {isHR && selectedRun?.status === 'DRAFT' && (
            <button onClick={() => setEditPayslip(r)} className="text-xs text-primary-600 hover:underline">Edit</button>
          )}
          {['APPROVED','PAID'].includes(selectedRun?.status) && (
            <button onClick={() => handleDownloadPDF(r.id, r.employee, `${selectedRun.year}-${String(selectedRun.month).padStart(2,'0')}`)}
              className="text-xs text-green-600 hover:underline flex items-center gap-1">
              📄 PDF
            </button>
          )}
        </div>
      )
    },
  ]

  // ── Salary columns ─────────────────────────────────────────────────────────
  const salaryColumns = [
    { key: 'employee_name', label: 'Employee', render: r => <span className="font-medium">{r.employee_name}</span> },
    { key: 'basic_salary', label: 'Basic Salary', render: r => <span className="font-semibold">{formatETB(r.basic_salary)}</span> },
    { key: 'housing_allowance', label: 'Housing Allow.', render: r => formatETB(r.housing_allowance) },
    { key: 'transport_allowance', label: 'Transport Allow.', render: r => formatETB(r.transport_allowance) },
    { key: 'non_taxable_allowance', label: 'Non-taxable Allow.', render: r => formatETB(r.non_taxable_allowance) },
    {
      key: 'total', label: 'Total Package',
      render: r => <span className="font-bold text-primary-600">{formatETB(
        Number(r.basic_salary) + Number(r.housing_allowance) + Number(r.transport_allowance) +
        Number(r.other_taxable_allowance) + Number(r.non_taxable_allowance)
      )}</span>
    },
    { key: 'effective_date', label: 'Effective', render: r => formatDate(r.effective_date) },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <button onClick={() => { setSalaryForm({ ...r }); setSalaryModal(true) }}
          className="text-xs text-primary-600 hover:underline">Edit</button>
      )
    },
  ]

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('payroll')}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{runs.length} payroll run{runs.length !== 1 ? 's' : ''} in database</p>
        </div>
        {isHR && (
          <div className="flex gap-2">
            <button onClick={() => { setActiveTab('salaries') }} className="btn-secondary text-sm">💼 Salary Structures</button>
            <button onClick={() => setNewRunModal(true)} className="btn-primary text-sm">
              + New Payroll Run
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {[
            { key:'runs', label:'Payroll Runs' },
            { key:'salaries', label:'Salary Structures', hidden: !isHR },
          ].filter(t => !t.hidden).map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Payroll Runs Tab */}
      {activeTab === 'runs' && (
        <div className="space-y-4">
          <div className="card">
            <Table columns={runColumns} data={runs} loading={runsLoading} emptyMessage="No payroll runs yet. Click 'New Payroll Run' to start." />
          </div>

          {/* Selected run detail */}
          {selectedRun && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Payslips — {selectedRun.year}/{String(selectedRun.month).padStart(2,'0')}
                  </h2>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`badge ${statusColor[selectedRun.status]}`}>{statusLabel(selectedRun.status)}</span>
                    <span className="text-sm text-gray-500">{payslips.length} employee{payslips.length !== 1 ? 's' : ''}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  {isHR && selectedRun.status === 'DRAFT' && payslips.length === 0 && (
                    <button onClick={() => generateMut.mutate(selectedRun.id)}
                      disabled={generateMut.isPending}
                      className="btn-primary text-sm">
                      {generateMut.isPending ? '⚙ Generating...' : '⚙ Generate Payslips'}
                    </button>
                  )}
                  {canAdvance(selectedRun) && (
                    <button
                      onClick={() => advanceMut.mutate({ id: selectedRun.id })}
                      disabled={advanceMut.isPending}
                      className="btn-primary text-sm bg-green-600 hover:bg-green-700">
                      → {nextActionLabel[selectedRun.status]}
                    </button>
                  )}
                </div>
              </div>

              {/* Run totals */}
              {payslips.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
                  {[
                    { label: 'Total Gross', value: formatETB(selectedRun.total_gross), color: 'text-gray-900' },
                    { label: 'Total Tax', value: formatETB(selectedRun.total_tax), color: 'text-red-500' },
                    { label: 'Employee Pension', value: formatETB(selectedRun.total_employee_pension), color: 'text-orange-500' },
                    { label: 'Employer Pension', value: formatETB(selectedRun.total_employer_pension), color: 'text-blue-500' },
                    { label: 'Total Net Pay', value: formatETB(selectedRun.total_net), color: 'text-green-600 text-lg font-bold' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className={`font-semibold mt-0.5 ${color}`}>{value}</p>
                    </div>
                  ))}
                </div>
              )}

              <Table columns={payslipColumns} data={payslips} loading={payslipsLoading}
                emptyMessage="No payslips yet. Click 'Generate Payslips' to create them." />
            </div>
          )}
        </div>
      )}

      {/* Salary Structures Tab */}
      {activeTab === 'salaries' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Salary Structures</h2>
            <button onClick={() => { setSalaryForm({ basic_salary: '', housing_allowance: 0, transport_allowance: 0, other_taxable_allowance: 0, non_taxable_allowance: 0, effective_date: new Date().toISOString().slice(0,10) }); setSalaryModal(true) }}
              className="btn-primary text-sm">+ Add Salary Structure</button>
          </div>
          <Table columns={salaryColumns} data={salaries} loading={salariesLoading}
            emptyMessage="No salary structures defined yet." />
        </div>
      )}

      {/* New Run Modal */}
      <Modal isOpen={newRunModal} onClose={() => setNewRunModal(false)} title="Create New Payroll Run">
        <ErrorMessage error={createRunMut.error} className="mb-3" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Year</label>
              <input type="number" value={newRunData.year}
                onChange={e => setNewRunData(d => ({ ...d, year: parseInt(e.target.value) }))}
                className="input-field" min="2020" max="2030" />
            </div>
            <div>
              <label className="label">Month</label>
              <select value={newRunData.month}
                onChange={e => setNewRunData(d => ({ ...d, month: parseInt(e.target.value) }))}
                className="input-field">
                {[...Array(12)].map((_, i) => (
                  <option key={i+1} value={i+1}>{new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-700">
            This will create a <strong>Draft</strong> payroll run for {newRunData.year}/{String(newRunData.month).padStart(2,'0')}.
            After creating, generate payslips for all active employees, then review and approve.
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setNewRunModal(false)} className="btn-secondary">Cancel</button>
            <button onClick={() => createRunMut.mutate({ year: newRunData.year, month: newRunData.month })}
              disabled={createRunMut.isPending} className="btn-primary">
              {createRunMut.isPending ? 'Creating...' : 'Create Payroll Run'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Edit Payslip Modal */}
      <Modal isOpen={!!editPayslip} onClose={() => setEditPayslip(null)} title={`Edit Payslip — ${editPayslip?.employee_name}`} size="lg">
        {editPayslip && (
          <EditPayslipForm
            payslip={editPayslip}
            onSave={(data) => {
              // Update via API
              import('../../api/index').then(({ default: api }) => {
                api.patch(`/payroll/payslips/${editPayslip.id}/`, data)
                  .then(() => {
                    qc.invalidateQueries({ queryKey: ['payslips', selectedRun?.id] })
                    qc.invalidateQueries({ queryKey: ['payroll-runs'] })
                    setEditPayslip(null)
                  })
              })
            }}
            onClose={() => setEditPayslip(null)}
          />
        )}
      </Modal>

      {/* Salary Modal */}
      <Modal isOpen={salaryModal} onClose={() => setSalaryModal(false)} title={salaryForm.id ? 'Edit Salary Structure' : 'Add Salary Structure'} size="lg">
        <ErrorMessage error={saveSalaryMut.error} className="mb-3" />
        <div className="grid grid-cols-2 gap-4">
          {!salaryForm.id && (
            <div className="col-span-2">
              <label className="label">Employee ID</label>
              <input type="number" placeholder="Employee database ID"
                onChange={e => setSalaryForm(f => ({ ...f, employee: parseInt(e.target.value) }))}
                className="input-field" />
            </div>
          )}
          {[
            { key: 'basic_salary', label: 'Basic Salary (ETB) *' },
            { key: 'housing_allowance', label: 'Housing Allowance (ETB)' },
            { key: 'transport_allowance', label: 'Transport Allowance (ETB)' },
            { key: 'other_taxable_allowance', label: 'Other Taxable Allowance (ETB)' },
            { key: 'non_taxable_allowance', label: 'Non-Taxable Allowance (ETB)' },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className="label">{label}</label>
              <input type="number" step="0.01" value={salaryForm[key] || ''}
                onChange={e => setSalaryForm(f => ({ ...f, [key]: e.target.value }))}
                className="input-field" />
            </div>
          ))}
          <div>
            <label className="label">Effective Date *</label>
            <input type="date" value={salaryForm.effective_date || ''}
              onChange={e => setSalaryForm(f => ({ ...f, effective_date: e.target.value }))}
              className="input-field" />
          </div>
        </div>
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={() => setSalaryModal(false)} className="btn-secondary">Cancel</button>
          <button onClick={() => saveSalaryMut.mutate(salaryForm)}
            disabled={saveSalaryMut.isPending} className="btn-primary">
            {saveSalaryMut.isPending ? 'Saving...' : '💾 Save'}
          </button>
        </div>
      </Modal>
    </div>
  )
}

// ── Edit Payslip subcomponent ─────────────────────────────────────────────────

function EditPayslipForm({ payslip, onSave, onClose }) {
  const [form, setForm] = useState({
    bonus: payslip.bonus || 0,
    loan_deduction: payslip.loan_deduction || 0,
    advance_deduction: payslip.advance_deduction || 0,
    penalty_deduction: payslip.penalty_deduction || 0,
    other_deduction: payslip.other_deduction || 0,
  })

  const fields = [
    { key:'bonus', label:'Bonus (ETB)', color:'text-green-600' },
    { key:'loan_deduction', label:'Loan Deduction (ETB)', color:'text-red-500' },
    { key:'advance_deduction', label:'Advance Deduction (ETB)', color:'text-red-500' },
    { key:'penalty_deduction', label:'Penalty Deduction (ETB)', color:'text-red-500' },
    { key:'other_deduction', label:'Other Deduction (ETB)', color:'text-red-500' },
  ]

  // Preview calculation
  const gross = Number(payslip.basic_salary) + Number(payslip.taxable_allowances) +
                Number(payslip.overtime_pay) + Number(form.bonus)
  const totalDeductions = Number(payslip.income_tax) + Number(payslip.employee_pension) +
    Number(form.loan_deduction) + Number(form.advance_deduction) +
    Number(form.penalty_deduction) + Number(form.other_deduction)
  const netPreview = gross + Number(payslip.non_taxable_allowances) - totalDeductions

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-lg p-3 text-sm grid grid-cols-2 gap-2">
        <div><span className="text-gray-500">Basic Salary:</span> <strong>{formatETB(payslip.basic_salary)}</strong></div>
        <div><span className="text-gray-500">Tax:</span> <strong className="text-red-500">{formatETB(payslip.income_tax)}</strong></div>
        <div><span className="text-gray-500">Allowances:</span> <strong>{formatETB(payslip.taxable_allowances)}</strong></div>
        <div><span className="text-gray-500">Pension:</span> <strong>{formatETB(payslip.employee_pension)}</strong></div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {fields.map(({ key, label, color }) => (
          <div key={key}>
            <label className="label">{label}</label>
            <input type="number" step="0.01" min="0"
              value={form[key]}
              onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              className="input-field" />
          </div>
        ))}
      </div>

      <div className="bg-primary-50 border border-primary-200 rounded-lg p-3 flex items-center justify-between">
        <span className="text-sm font-medium text-primary-700">Estimated Net Pay (preview):</span>
        <span className="text-xl font-bold text-green-600">{formatETB(Math.max(0, netPreview))}</span>
      </div>

      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="btn-secondary">Cancel</button>
        <button onClick={() => onSave(form)} className="btn-primary">💾 Save Changes</button>
      </div>
    </div>
  )
}
