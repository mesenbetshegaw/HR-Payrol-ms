import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import {
  getTaxBrackets, createTaxBracket, updateTaxBracket, deleteTaxBracket,
  getPensionSettings, createPensionSetting,
  getOvertimeRules, updateOvertimeRule,
} from '../../api/index'
import Table from '../../components/common/Table'
import Modal from '../../components/common/Modal'
import ErrorMessage from '../../components/common/ErrorMessage'
import { formatETB } from '../../utils/format'

const tabs = ['Tax Brackets', 'Pension', 'Overtime Rules']

export default function PayrollSettings() {
  const [tab, setTab] = useState('Tax Brackets')
  const [modal, setModal] = useState(null)
  const [editItem, setEditItem] = useState(null)
  const qc = useQueryClient()

  const brackets = useQuery({ queryKey: ['tax-brackets'], queryFn: () => getTaxBrackets().then(r => r.data?.results || r.data) })
  const pension = useQuery({ queryKey: ['pension-settings'], queryFn: () => getPensionSettings().then(r => r.data?.results || r.data) })
  const overtime = useQuery({ queryKey: ['overtime-rules'], queryFn: () => getOvertimeRules().then(r => r.data?.results || r.data) })

  const createBracketMut = useMutation({ mutationFn: createTaxBracket, onSuccess: () => { qc.invalidateQueries(['tax-brackets']); setModal(null) } })
  const deleteBracketMut = useMutation({ mutationFn: deleteTaxBracket, onSuccess: () => qc.invalidateQueries(['tax-brackets']) })
  const createPensionMut = useMutation({ mutationFn: createPensionSetting, onSuccess: () => { qc.invalidateQueries(['pension-settings']); setModal(null) } })
  const updateOtMut = useMutation({ mutationFn: ({ id, ...d }) => updateOvertimeRule(id, d), onSuccess: () => { qc.invalidateQueries(['overtime-rules']); setModal(null) } })

  const bracketForm = useForm()
  const pensionForm = useForm()
  const otForm = useForm()

  const bracketCols = [
    { key: 'min_income', label: 'Min Income', render: r => formatETB(r.min_income) },
    { key: 'max_income', label: 'Max Income', render: r => r.max_income ? formatETB(r.max_income) : '∞' },
    { key: 'rate', label: 'Rate', render: r => `${(r.rate * 100).toFixed(0)}%` },
    { key: 'deduction', label: 'Deduction', render: r => formatETB(r.deduction) },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
    {
      key: 'actions', label: 'Actions',
      render: r => <button onClick={() => deleteBracketMut.mutate(r.id)} className="text-red-600 text-xs hover:underline">Delete</button>
    },
  ]

  const pensionCols = [
    { key: 'employee_rate', label: 'Employee %', render: r => `${(r.employee_rate * 100).toFixed(0)}%` },
    { key: 'employer_rate', label: 'Employer %', render: r => `${(r.employer_rate * 100).toFixed(0)}%` },
    { key: 'pension_reduces_taxable_income', label: 'Reduces Tax?', render: r => r.pension_reduces_taxable_income ? 'Yes' : 'No' },
    { key: 'effective_date', label: 'Effective Date' },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
  ]

  const otCols = [
    { key: 'overtime_type', label: 'Type' },
    { key: 'multiplier', label: 'Multiplier', render: r => `×${r.multiplier}` },
    { key: 'hourly_divisor', label: 'Hourly Divisor' },
    { key: 'is_active', label: 'Active', render: r => <span className={r.is_active ? 'badge-green badge' : 'badge-gray badge'}>{r.is_active ? 'Yes' : 'No'}</span> },
    {
      key: 'actions', label: 'Actions',
      render: r => (
        <button onClick={() => { setEditItem(r); otForm.reset({ multiplier: r.multiplier, hourly_divisor: r.hourly_divisor }); setModal('ot') }}
          className="text-primary-600 text-xs hover:underline">Edit</button>
      )
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Payroll Settings</h1>

      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t}
            </button>
          ))}
        </nav>
      </div>

      <div className="card">
        {tab === 'Tax Brackets' && (
          <>
            <div className="flex justify-end mb-3">
              <button onClick={() => setModal('bracket')} className="btn-primary text-sm">Add Bracket</button>
            </div>
            <Table columns={bracketCols} data={brackets.data || []} loading={brackets.isLoading} />
          </>
        )}
        {tab === 'Pension' && (
          <>
            <div className="flex justify-end mb-3">
              <button onClick={() => setModal('pension')} className="btn-primary text-sm">Add Setting</button>
            </div>
            <Table columns={pensionCols} data={pension.data || []} loading={pension.isLoading} />
          </>
        )}
        {tab === 'Overtime Rules' && (
          <Table columns={otCols} data={overtime.data || []} loading={overtime.isLoading} />
        )}
      </div>

      {/* Tax Bracket Modal */}
      <Modal isOpen={modal === 'bracket'} onClose={() => setModal(null)} title="Add Tax Bracket">
        <ErrorMessage error={createBracketMut.error} className="mb-3" />
        <form onSubmit={bracketForm.handleSubmit(d => createBracketMut.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Min Income (ETB)</label><input {...bracketForm.register('min_income')} type="number" step="0.01" className="input-field" /></div>
            <div><label className="label">Max Income (ETB, blank=∞)</label><input {...bracketForm.register('max_income')} type="number" step="0.01" className="input-field" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Rate (e.g. 0.15)</label><input {...bracketForm.register('rate')} type="number" step="0.001" className="input-field" /></div>
            <div><label className="label">Deduction (ETB)</label><input {...bracketForm.register('deduction')} type="number" step="0.01" className="input-field" /></div>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={createBracketMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>

      {/* Pension Modal */}
      <Modal isOpen={modal === 'pension'} onClose={() => setModal(null)} title="Add Pension Setting">
        <ErrorMessage error={createPensionMut.error} className="mb-3" />
        <form onSubmit={pensionForm.handleSubmit(d => createPensionMut.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Employee Rate (e.g. 0.07)</label><input {...pensionForm.register('employee_rate')} type="number" step="0.001" defaultValue="0.07" className="input-field" /></div>
            <div><label className="label">Employer Rate (e.g. 0.11)</label><input {...pensionForm.register('employer_rate')} type="number" step="0.001" defaultValue="0.11" className="input-field" /></div>
          </div>
          <div><label className="label">Effective Date</label><input {...pensionForm.register('effective_date')} type="date" className="input-field" /></div>
          <div className="flex items-center gap-2">
            <input {...pensionForm.register('pension_reduces_taxable_income')} type="checkbox" id="prti" />
            <label htmlFor="prti" className="text-sm text-gray-700">Pension reduces taxable income</label>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={createPensionMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>

      {/* Overtime Edit Modal */}
      <Modal isOpen={modal === 'ot'} onClose={() => setModal(null)} title={`Edit Overtime: ${editItem?.overtime_type}`}>
        <ErrorMessage error={updateOtMut.error} className="mb-3" />
        <form onSubmit={otForm.handleSubmit(d => updateOtMut.mutate({ id: editItem.id, ...d }))} className="space-y-4">
          <div><label className="label">Multiplier</label><input {...otForm.register('multiplier')} type="number" step="0.01" className="input-field" /></div>
          <div><label className="label">Hourly Divisor</label><input {...otForm.register('hourly_divisor')} type="number" step="0.5" className="input-field" /></div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setModal(null)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={updateOtMut.isPending} className="btn-primary">Save</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
