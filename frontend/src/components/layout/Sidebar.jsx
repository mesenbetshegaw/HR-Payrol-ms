import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { getPendingCount } from '../../api/index'

const icons = {
  dashboard: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>),
  employees: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  attendance: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>),
  leave: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>),
  payroll: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  organization: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>),
  users: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>),
  audit: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>),
  reports: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>),
  register: (<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>),
}

const navByRole = {
  ADMIN: [
    { to: '/dashboard',     key: 'dashboard',     icon: 'dashboard' },
    { to: '/employees',     key: 'employees',     icon: 'employees' },
    { to: '/attendance',    key: 'attendance',    icon: 'attendance' },
    { to: '/leave',         key: 'leave',         icon: 'leave' },
    { to: '/payroll',       key: 'payroll',       icon: 'payroll' },
    { to: '/organization',  key: 'organization',  icon: 'organization' },
    { to: '/users',         key: 'users',         icon: 'users' },
    { to: '/registrations', key: 'Registrations', icon: 'register', badge: true },
    { to: '/reports',       key: 'reports',       icon: 'reports' },
    { to: '/audit',         key: 'audit_log',     icon: 'audit' },
  ],
  SUB_ADMIN: [
    { to: '/dashboard',     key: 'dashboard',     icon: 'dashboard' },
    { to: '/employees',     key: 'employees',     icon: 'employees' },
    { to: '/attendance',    key: 'attendance',    icon: 'attendance' },
    { to: '/leave',         key: 'leave',         icon: 'leave' },
    { to: '/payroll',       key: 'payroll',       icon: 'payroll' },
    { to: '/registrations', key: 'Registrations', icon: 'register', badge: true },
    { to: '/reports',       key: 'reports',       icon: 'reports' },
  ],
  MANAGER: [
    { to: '/dashboard',  key: 'dashboard',  icon: 'dashboard' },
    { to: '/employees',  key: 'employees',  icon: 'employees' },
    { to: '/attendance', key: 'attendance', icon: 'attendance' },
    { to: '/leave',      key: 'leave',      icon: 'leave' },
  ],
  EMPLOYEE: [
    { to: '/dashboard',    key: 'dashboard',  icon: 'dashboard' },
    { to: '/my-attendance',key: 'attendance', icon: 'attendance' },
    { to: '/my-leave',     key: 'leave',      icon: 'leave' },
    { to: '/my-payslips',  key: 'payroll',    icon: 'payroll' },
  ],
}

export default function Sidebar({ collapsed }) {
  const { t } = useTranslation()
  const { user } = useAuth()
  const navItems = navByRole[user?.role] || []
  const isAdminOrSubAdmin = ['ADMIN', 'SUB_ADMIN'].includes(user?.role)

  // Live pending registration count badge
  const { data: pendingData } = useQuery({
    queryKey: ['pending-reg-count'],
    queryFn: () => getPendingCount().then(r => r.data),
    refetchInterval: 20000,
    enabled: isAdminOrSubAdmin,
  })
  const pendingCount = pendingData?.pending_count || 0

  return (
    <aside className={`${collapsed ? 'w-16' : 'w-64'} bg-primary-900 text-white flex flex-col transition-all duration-200 min-h-screen flex-shrink-0`}>
      {/* Logo */}
      <div className="p-4 border-b border-primary-700">
        {!collapsed ? (
          <div>
            <h1 className="text-sm font-bold text-white">HR & Payroll</h1>
            <p className="text-xs text-primary-300 mt-0.5">Ethiopia</p>
          </div>
        ) : (
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">HR</div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-700 text-white'
                  : 'text-primary-200 hover:bg-primary-800 hover:text-white'
              }`
            }
          >
            <span className="flex-shrink-0 relative">
              {icons[item.icon]}
              {/* Pending badge on registrations */}
              {item.badge && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                  {pendingCount > 9 ? '9+' : pendingCount}
                </span>
              )}
            </span>
            {!collapsed && (
              <span className="flex items-center gap-2 flex-1">
                {t(item.key) || item.key}
                {item.badge && pendingCount > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 font-bold">
                    {pendingCount}
                  </span>
                )}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User role badge at bottom */}
      {!collapsed && (
        <div className="p-4 border-t border-primary-700">
          <p className="text-xs text-primary-400 truncate">{user?.email}</p>
          <p className="text-xs text-primary-300 mt-0.5">{user?.role?.replace('_', ' ')}</p>
        </div>
      )}
    </aside>
  )
}
