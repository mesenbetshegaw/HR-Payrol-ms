import api from './client'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Public API (no auth required) — for registration form
const publicApi = axios.create({ baseURL: BASE_URL })

// Organization — public GET for registration form, authenticated for mutations
export const getDepartments = (p) => publicApi.get('/organization/departments/', { params: p })
export const createDepartment = (d) => api.post('/organization/departments/', d)
export const updateDepartment = (id, d) => api.patch(`/organization/departments/${id}/`, d)
export const deleteDepartment = (id) => api.delete(`/organization/departments/${id}/`)
export const getPositions = (p) => publicApi.get('/organization/positions/', { params: p })
export const createPosition = (d) => api.post('/organization/positions/', d)
export const updatePosition = (id, d) => api.patch(`/organization/positions/${id}/`, d)
export const deletePosition = (id) => api.delete(`/organization/positions/${id}/`)
export const getBranches = (p) => api.get('/organization/branches/', { params: p })
export const createBranch = (d) => api.post('/organization/branches/', d)
export const updateBranch = (id, d) => api.patch(`/organization/branches/${id}/`, d)
export const getHolidays = (p) => api.get('/organization/holidays/', { params: p })
export const createHoliday = (d) => api.post('/organization/holidays/', d)
export const deleteHoliday = (id) => api.delete(`/organization/holidays/${id}/`)

// Employees
export const getEmployees = (p) => api.get('/employees/', { params: p })
export const getEmployee = (id) => api.get(`/employees/${id}/`)
export const createEmployee = (d) => api.post('/employees/', d)
export const updateEmployee = (id, d) => api.patch(`/employees/${id}/`, d)
export const changeEmployeeStatus = (id, d) => api.post(`/employees/${id}/status/`, d)
export const getStatusHistory = (id) => api.get(`/employees/${id}/status-history/`)
export const getContracts = (empId) => api.get(`/employees/${empId}/contracts/`)
export const createContract = (empId, d) => api.post(`/employees/${empId}/contracts/`, d)
export const getDocuments = (empId) => api.get(`/employees/${empId}/documents/`)
export const uploadDocument = (empId, formData) => api.post(`/employees/${empId}/documents/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const exportEmployees = (fmt = 'csv') => api.get(`/employees/export/?format=${fmt}`, { responseType: 'blob' })

// Attendance
export const getAttendance = (p) => api.get('/attendance/', { params: p })
export const checkIn = (d) => api.post('/attendance/check-in/', d)
export const checkOut = (id, d) => api.post(`/attendance/${id}/check-out/`, d)
export const approveOvertime = (id, action) => api.post(`/attendance/${id}/overtime-approval/`, { action })
export const getMonthlySummary = (p) => api.get('/attendance/summary/', { params: p })
export const generateSummary = (d) => api.post('/attendance/summary/generate/', d)

// Leave
export const getLeaveTypes = () => api.get('/leave/types/')
export const createLeaveType = (d) => api.post('/leave/types/', d)
export const updateLeaveType = (id, d) => api.patch(`/leave/types/${id}/`, d)
export const getLeaveBalances = (p) => api.get('/leave/balances/', { params: p })
export const getLeaveRequests = (p) => api.get('/leave/requests/', { params: p })
export const createLeaveRequest = (d) => api.post('/leave/requests/', d)
export const managerApproveLeave = (id, d) => api.post(`/leave/requests/${id}/manager-approve/`, d)
export const hrApproveLeave = (id, d) => api.post(`/leave/requests/${id}/hr-approve/`, d)
export const rejectLeave = (id, d) => api.post(`/leave/requests/${id}/reject/`, d)
export const cancelLeave = (id) => api.post(`/leave/requests/${id}/cancel/`)
export const getLeaveCalendar = (p) => api.get('/leave/calendar/', { params: p })

// Payroll
export const getTaxBrackets = () => api.get('/payroll/tax-brackets/')
export const createTaxBracket = (d) => api.post('/payroll/tax-brackets/', d)
export const updateTaxBracket = (id, d) => api.patch(`/payroll/tax-brackets/${id}/`, d)
export const deleteTaxBracket = (id) => api.delete(`/payroll/tax-brackets/${id}/`)
export const getPensionSettings = () => api.get('/payroll/pension-settings/')
export const createPensionSetting = (d) => api.post('/payroll/pension-settings/', d)
export const getOvertimeRules = () => api.get('/payroll/overtime-rules/')
export const updateOvertimeRule = (id, d) => api.patch(`/payroll/overtime-rules/${id}/`, d)
export const getSalaryStructures = (p) => api.get('/payroll/salary/', { params: p })
export const createSalaryStructure = (d) => api.post('/payroll/salary/', d)
export const updateSalaryStructure = (id, d) => api.patch(`/payroll/salary/${id}/`, d)
export const getPayrollRuns = (p) => api.get('/payroll/runs/', { params: p })
export const createPayrollRun = (d) => api.post('/payroll/runs/', d)
export const generatePayslips = (id) => api.post(`/payroll/runs/${id}/generate/`)
export const advancePayroll = (id, d) => api.post(`/payroll/runs/${id}/advance/`, d)
export const getBankTransfer = (id) => api.get(`/payroll/runs/${id}/bank-transfer/`, { responseType: 'blob' })
export const getPayslips = (p) => api.get('/payroll/payslips/', { params: p })
export const getPayslipPDF = (id) => api.get(`/payroll/payslips/${id}/pdf/`, { responseType: 'blob' })

// Reports / Dashboard
export const getAdminDashboard = () => api.get('/reports/dashboard/admin/')
export const getManagerDashboard = () => api.get('/reports/dashboard/manager/')
export const getEmployeeDashboard = () => api.get('/reports/dashboard/employee/')

// Notifications
export const getNotifications = (p) => api.get('/notifications/', { params: p })
export const getUnreadCount = () => api.get('/notifications/unread-count/')
export const markRead = (id) => api.post(`/notifications/${id}/read/`)
export const markAllRead = () => api.post('/notifications/mark-all-read/')

// Audit
export const getAuditLogs = (p) => api.get('/audit/logs/', { params: p })

// Registration workflow
export const submitRegistration = (d) => api.post('/auth/register/', d)
export const getRegistrations = (p) => api.get('/auth/registrations/', { params: p })
export const getPendingCount = () => api.get('/auth/registrations/pending-count/')
export const approveRegistration = (id) => api.post(`/auth/registrations/${id}/approve/`)
export const rejectRegistration = (id, reason) => api.post(`/auth/registrations/${id}/reject/`, { reason })
