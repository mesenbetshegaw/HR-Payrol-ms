import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getAdminDashboard, getManagerDashboard, getEmployeeDashboard } from '../../api/index'
import { formatETB, statusBadge, statusLabel } from '../../utils/format'
import { PageSpinner } from '../../components/common/Spinner'
import StatCard from '../../components/common/StatCard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area,
} from 'recharts'

const COLORS = ['#2563eb','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2']

// ── Shared components ─────────────────────────────────────────────────────────

function KpiCard({ title, value, subtitle, change, color = 'blue', icon }) {
  const bg = { blue:'bg-blue-50 text-blue-600', green:'bg-green-50 text-green-600',
               yellow:'bg-yellow-50 text-yellow-600', red:'bg-red-50 text-red-600',
               purple:'bg-purple-50 text-purple-600' }
  return (
    <div className="card flex items-start gap-4">
      {icon && <div className={`p-3 rounded-xl flex-shrink-0 ${bg[color]}`}>{icon}</div>}
      <div className="min-w-0">
        <p className="text-sm text-gray-500 truncate">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
        {change !== undefined && (
          <p className={`text-xs mt-1 font-medium ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)} this month
          </p>
        )}
      </div>
    </div>
  )
}

function SectionTitle({ children }) {
  return <h2 className="text-base font-semibold text-gray-900 mb-3">{children}</h2>
}

// ── Admin Dashboard ───────────────────────────────────────────────────────────

function AdminDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => getAdminDashboard().then(r => r.data),
    refetchInterval: 60000,
  })

  if (isLoading) return <PageSpinner />
  if (error) return <div className="card text-red-500">Failed to load dashboard data.</div>

  const d = data
  const emp = d.employees
  const att = d.attendance
  const lv  = d.leave
  const pay = d.payroll

  const attendancePieData = [
    { name: 'Present', value: att.today_present },
    { name: 'Absent',  value: att.today_absent  },
    { name: 'Late',    value: att.today_late     },
  ].filter(x => x.value > 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Live data from PostgreSQL · Updated {new Date(d.generated_at).toLocaleTimeString()}
          </p>
        </div>
        {d.registrations.pending > 0 && (
          <Link to="/registrations"
            className="flex items-center gap-2 bg-orange-50 border border-orange-200 text-orange-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-100">
            <span className="w-5 h-5 bg-orange-500 text-white rounded-full text-xs flex items-center justify-center font-bold">
              {d.registrations.pending}
            </span>
            Pending Registrations
          </Link>
        )}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Active Employees" value={emp.total_active} change={emp.new_this_month}
          color="blue"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
        />
        <KpiCard title="Present Today" value={att.today_present}
          subtitle={`${att.attendance_rate}% rate`} color="green"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <KpiCard title="Pending Leaves" value={lv.pending}
          subtitle={`${lv.manager_approved} awaiting HR`} color="yellow"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
        <KpiCard title="Payroll Net Pay" value={formatETB(pay.latest_total_net)}
          subtitle={pay.latest_period || '—'} color="purple"
          icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Employees by Department */}
        <div className="card lg:col-span-2">
          <SectionTitle>Employees by Department</SectionTitle>
          {emp.by_department.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={emp.by_department} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [v, 'Employees']} />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]}>
                  {emp.by_department.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-sm text-center py-8">No department data yet</p>}
        </div>

        {/* Today Attendance Pie */}
        <div className="card">
          <SectionTitle>Today's Attendance</SectionTitle>
          {attendancePieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={attendancePieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                  dataKey="value" label={({ name, value }) => `${value}`}>
                  {attendancePieData.map((_, i) => (
                    <Cell key={i} fill={['#16a34a','#dc2626','#d97706'][i] || COLORS[i]} />
                  ))}
                </Pie>
                <Legend iconType="circle" iconSize={8} />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400 text-sm">
              No attendance recorded today
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Monthly Attendance Trend */}
        <div className="card">
          <SectionTitle>Monthly Attendance Trend</SectionTitle>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={att.monthly_trend}>
              <defs>
                <linearGradient id="presentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="present" stroke="#2563eb" fill="url(#presentGrad)" name="Present" />
              <Area type="monotone" dataKey="absent" stroke="#dc2626" fill="none" strokeDasharray="4 2" name="Absent" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Payroll History */}
        <div className="card">
          <SectionTitle>Payroll Cost History (ETB)</SectionTitle>
          {pay.history.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={pay.history.slice().reverse()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(0)}K`} />
                <Tooltip formatter={(v) => [formatETB(v), '']} />
                <Bar dataKey="total_net" fill="#16a34a" radius={[3, 3, 0, 0]} name="Net Pay" />
                <Bar dataKey="total_tax" fill="#dc2626" radius={[3, 3, 0, 0]} name="Tax" />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-sm text-center py-8">No payroll history yet</p>}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Leave Summary */}
        <div className="card">
          <SectionTitle>Leave Summary</SectionTitle>
          <div className="space-y-3">
            {[
              { label: 'Pending Approval',   value: lv.pending,           color: 'text-yellow-600', link: '/leave?status=PENDING' },
              { label: 'Manager Approved',    value: lv.manager_approved,  color: 'text-blue-600',   link: '/leave?status=MANAGER_APPROVED' },
              { label: 'Approved Today',      value: lv.approved_today,    color: 'text-green-600',  link: '/leave' },
              { label: 'On Leave Today',      value: lv.on_leave_today,    color: 'text-orange-600', link: '/employees' },
            ].map(({ label, value, color, link }) => (
              <Link key={label} to={link} className="flex items-center justify-between py-2 border-b border-gray-50 hover:bg-gray-50 rounded px-1">
                <span className="text-sm text-gray-600">{label}</span>
                <span className={`text-lg font-bold ${color}`}>{value}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Payroll Status */}
        <div className="card">
          <SectionTitle>Latest Payroll</SectionTitle>
          {pay.latest_period ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Period</span>
                <span className="font-semibold">{pay.latest_period}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Status</span>
                <span className={statusBadge(pay.latest_status)}>{statusLabel(pay.latest_status)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Gross</span>
                <span className="font-semibold">{formatETB(pay.latest_total_gross)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Tax</span>
                <span className="text-red-600 font-semibold">{formatETB(pay.latest_total_tax)}</span>
              </div>
              <div className="flex justify-between items-center border-t pt-2">
                <span className="text-sm font-medium">Net Pay</span>
                <span className="text-green-600 font-bold text-lg">{formatETB(pay.latest_total_net)}</span>
              </div>
              <Link to="/payroll" className="btn-secondary w-full text-center text-sm mt-2">
                View Payroll →
              </Link>
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-gray-400 text-sm mb-3">No payroll runs yet</p>
              <Link to="/payroll" className="btn-primary text-sm">Create Payroll Run</Link>
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="card">
          <SectionTitle>Quick Actions</SectionTitle>
          <div className="space-y-2">
            {[
              { to: '/employees/new',  label: '+ Add Employee',      color: 'bg-blue-50 text-blue-700 hover:bg-blue-100' },
              { to: '/leave',          label: '📋 Review Leaves',    color: 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100' },
              { to: '/payroll',        label: '💰 Run Payroll',      color: 'bg-green-50 text-green-700 hover:bg-green-100' },
              { to: '/registrations',  label: '👤 Registrations',    color: 'bg-purple-50 text-purple-700 hover:bg-purple-100' },
              { to: '/attendance',     label: '📅 Attendance',       color: 'bg-orange-50 text-orange-700 hover:bg-orange-100' },
              { to: '/audit',          label: '🔍 Audit Log',        color: 'bg-gray-50 text-gray-700 hover:bg-gray-100' },
            ].map(({ to, label, color }) => (
              <Link key={to} to={to}
                className={`block w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${color}`}>
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Manager Dashboard ─────────────────────────────────────────────────────────

function ManagerDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['manager-dashboard'],
    queryFn: () => getManagerDashboard().then(r => r.data),
    refetchInterval: 60000,
  })
  if (isLoading) return <PageSpinner />
  const d = data

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Manager Dashboard — {d.department}</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Team Size" value={d.team_count} color="blue" />
        <KpiCard title="Present Today" value={d.today.present}
          subtitle={`${d.today.attendance_rate}% rate`} color="green" />
        <KpiCard title="Absent Today" value={d.today.absent} color="red" />
        <KpiCard title="Pending Leaves" value={d.leave.pending_approvals} color="yellow" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <SectionTitle>Monthly Attendance Trend</SectionTitle>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={d.monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="present" fill="#2563eb" radius={[3, 3, 0, 0]} name="Present" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <SectionTitle>Quick Actions</SectionTitle>
          <div className="space-y-2 mt-2">
            <Link to="/leave" className="block w-full bg-yellow-50 text-yellow-700 hover:bg-yellow-100 px-4 py-3 rounded-lg text-sm font-medium">
              📋 Review {d.leave.pending_approvals} Pending Leave{d.leave.pending_approvals !== 1 ? 's' : ''}
            </Link>
            {d.overtime.pending_approvals > 0 && (
              <Link to="/attendance" className="block w-full bg-orange-50 text-orange-700 hover:bg-orange-100 px-4 py-3 rounded-lg text-sm font-medium">
                ⏱ Approve {d.overtime.pending_approvals} Overtime Request{d.overtime.pending_approvals !== 1 ? 's' : ''}
              </Link>
            )}
            <Link to="/employees" className="block w-full bg-blue-50 text-blue-700 hover:bg-blue-100 px-4 py-3 rounded-lg text-sm font-medium">
              👥 View Team Directory
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Employee Dashboard ────────────────────────────────────────────────────────

function EmployeeDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['employee-dashboard'],
    queryFn: () => getEmployeeDashboard().then(r => r.data),
    refetchInterval: 30000,
  })
  if (isLoading) return <PageSpinner />
  const d = data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome, {d.name} 👋</h1>
        <p className="text-sm text-gray-500 mt-0.5">{d.position} · {d.department}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Check In" value={d.today_attendance.check_in || '—'} color="blue" />
        <KpiCard title="Check Out" value={d.today_attendance.check_out || '—'} color="green" />
        <KpiCard title="This Month Present" value={d.this_month.present_days} color="blue" />
        <KpiCard title="This Month Absent" value={d.this_month.absent_days} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Leave Balances */}
        <div className="card">
          <SectionTitle>Leave Balances</SectionTitle>
          {d.leave_balances.length > 0 ? (
            <div className="space-y-3">
              {d.leave_balances.map((b, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{b.leave_type__name}</span>
                    <span className="font-semibold">{b.remaining} / {b.allocated_days} days</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5">
                    <div className="bg-primary-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, (b.remaining / b.allocated_days) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-gray-400 text-sm">No leave balances</p>}
          <Link to="/my-leave" className="btn-secondary w-full text-center text-sm mt-4">Request Leave</Link>
        </div>

        {/* Last Payslip */}
        <div className="card">
          <SectionTitle>Last Payslip</SectionTitle>
          {d.last_payslip.period ? (
            <div className="space-y-3">
              <div className="text-center py-2">
                <p className="text-xs text-gray-400">{d.last_payslip.period}</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{formatETB(d.last_payslip.net_pay)}</p>
                <p className="text-xs text-gray-400 mt-0.5">Net Pay</p>
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Gross</span><span>{formatETB(d.last_payslip.gross_salary)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Tax</span><span className="text-red-500">-{formatETB(d.last_payslip.income_tax)}</span></div>
              </div>
              <Link to="/my-payslips" className="btn-primary w-full text-center text-sm">Download PDF</Link>
            </div>
          ) : <p className="text-gray-400 text-sm text-center py-6">No payslip yet</p>}
        </div>

        {/* Net Pay History chart */}
        <div className="card">
          <SectionTitle>Net Pay History</SectionTitle>
          {d.payslip_history.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={d.payslip_history.slice().reverse()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 9 }} tickFormatter={v => `${(v/1000).toFixed(0)}K`} />
                <Tooltip formatter={(v) => [formatETB(v), 'Net Pay']} />
                <Line type="monotone" dataKey="net_pay" stroke="#16a34a" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-sm text-center py-6">No history yet</p>}
        </div>
      </div>
    </div>
  )
}

// ── Router ────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth()
  if (user?.role === 'MANAGER') return <ManagerDashboard />
  if (user?.role === 'EMPLOYEE') return <EmployeeDashboard />
  return <AdminDashboard />
}
