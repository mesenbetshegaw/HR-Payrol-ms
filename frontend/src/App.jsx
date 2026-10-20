import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/common/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'

// Auth
import Login          from './pages/auth/Login'
import Register       from './pages/auth/Register'
import ChangePassword from './pages/auth/ChangePassword'
import ForgotPassword from './pages/auth/ForgotPassword'
import ResetPassword  from './pages/auth/ResetPassword'

// Shared
import Dashboard      from './pages/shared/Dashboard'
import Employees      from './pages/shared/Employees'
import EmployeeDetail from './pages/shared/EmployeeDetail'
import AddEmployee    from './pages/shared/AddEmployee'
import EditEmployee   from './pages/shared/EditEmployee'
import Leave          from './pages/shared/Leave'
import Attendance     from './pages/shared/Attendance'
import Payroll        from './pages/shared/Payroll'
import Notifications  from './pages/shared/Notifications'
import Profile        from './pages/shared/Profile'
import Unauthorized   from './pages/shared/Unauthorized'

// Admin
import Users            from './pages/admin/Users'
import Organization     from './pages/admin/Organization'
import AuditLog         from './pages/admin/AuditLog'
import PayrollSettings  from './pages/admin/PayrollSettings'
import PermissionMatrix from './pages/admin/PermissionMatrix'
import Registrations    from './pages/admin/Registrations'

// Employee
import MyPayslips from './pages/employee/MyPayslips'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* ── Public ─────────────────────────────────────────────── */}
        <Route path="/login"           element={<Login />} />
        <Route path="/register"        element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password"  element={<ResetPassword />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route path="/unauthorized"    element={<Unauthorized />} />

        {/* ── Protected ──────────────────────────────────────────── */}
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/"               element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard"      element={<Dashboard />} />
          <Route path="/profile"        element={<Profile />} />
          <Route path="/notifications"  element={<Notifications />} />

          {/* Employee self-service */}
          <Route path="/my-attendance"  element={<Attendance />} />
          <Route path="/my-leave"       element={<Leave />} />
          <Route path="/my-payslips"    element={<MyPayslips />} />

          {/* Admin + SubAdmin + Manager */}
          <Route path="/employees"      element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN','MANAGER']}><Employees /></ProtectedRoute>} />
          <Route path="/employees/new"  element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><AddEmployee /></ProtectedRoute>} />
          <Route path="/employees/:id"  element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN','MANAGER']}><EmployeeDetail /></ProtectedRoute>} />
          <Route path="/employees/:id/edit" element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><EditEmployee /></ProtectedRoute>} />
          <Route path="/attendance"     element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN','MANAGER']}><Attendance /></ProtectedRoute>} />
          <Route path="/leave"          element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN','MANAGER']}><Leave /></ProtectedRoute>} />

          {/* Admin + SubAdmin */}
          <Route path="/payroll"        element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><Payroll /></ProtectedRoute>} />
          <Route path="/organization"   element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><Organization /></ProtectedRoute>} />
          <Route path="/reports"        element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><Dashboard /></ProtectedRoute>} />
          <Route path="/registrations"  element={<ProtectedRoute allowedRoles={['ADMIN','SUB_ADMIN']}><Registrations /></ProtectedRoute>} />

          {/* Admin only */}
          <Route path="/users"            element={<ProtectedRoute allowedRoles={['ADMIN']}><Users /></ProtectedRoute>} />
          <Route path="/audit"            element={<ProtectedRoute allowedRoles={['ADMIN']}><AuditLog /></ProtectedRoute>} />
          <Route path="/payroll-settings" element={<ProtectedRoute allowedRoles={['ADMIN']}><PayrollSettings /></ProtectedRoute>} />
          <Route path="/permissions"      element={<ProtectedRoute allowedRoles={['ADMIN']}><PermissionMatrix /></ProtectedRoute>} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  )
}
