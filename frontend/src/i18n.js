import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

const en = {
  translation: {
    // Auth
    login: 'Login',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    forgot_password: 'Forgot Password?',
    change_password: 'Change Password',
    // Nav
    dashboard: 'Dashboard',
    employees: 'Employees',
    attendance: 'Attendance',
    leave: 'Leave',
    payroll: 'Payroll',
    reports: 'Reports',
    organization: 'Organization',
    users: 'Users',
    audit_log: 'Audit Log',
    notifications: 'Notifications',
    settings: 'Settings',
    // Common
    save: 'Save',
    cancel: 'Cancel',
    edit: 'Edit',
    delete: 'Delete',
    add: 'Add',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    loading: 'Loading...',
    no_data: 'No data found',
    confirm_delete: 'Are you sure you want to delete this?',
    actions: 'Actions',
    status: 'Status',
    name: 'Name',
    date: 'Date',
    // Status labels
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    cancelled: 'Cancelled',
    draft: 'Draft',
    reviewed: 'Reviewed',
    paid: 'Paid',
    active: 'Active',
    inactive: 'Inactive',
    // Employee
    employee_id: 'Employee ID',
    full_name: 'Full Name',
    department: 'Department',
    position: 'Position',
    hire_date: 'Hire Date',
    // Leave
    leave_type: 'Leave Type',
    start_date: 'Start Date',
    end_date: 'End Date',
    days: 'Days',
    reason: 'Reason',
    balance: 'Balance',
    // Payroll
    basic_salary: 'Basic Salary',
    gross_salary: 'Gross Salary',
    net_pay: 'Net Pay',
    income_tax: 'Income Tax',
    pension: 'Pension',
    // Currency
    etb: 'ETB',
    // Roles
    admin: 'Admin',
    sub_admin: 'Sub Admin',
    manager: 'Manager',
    employee: 'Employee',
  }
}

const am = {
  translation: {
    // Auth
    login: 'ግባ',
    logout: 'ውጣ',
    email: 'ኢሜይል',
    password: 'የሚስጥር ቃል',
    forgot_password: 'የሚስጥር ቃልዎን ረሱ?',
    change_password: 'የሚስጥር ቃል ቀይር',
    // Nav
    dashboard: 'ዳሽቦርድ',
    employees: 'ሠራተኞች',
    attendance: 'ቀን መቁጠሪያ',
    leave: 'ፈቃድ',
    payroll: 'ደሞዝ',
    reports: 'ሪፖርቶች',
    organization: 'ድርጅት',
    users: 'ተጠቃሚዎች',
    audit_log: 'ኦዲት ምዝገባ',
    notifications: 'ማሳወቂያዎች',
    settings: 'ቅንብሮች',
    // Common
    save: 'አስቀምጥ',
    cancel: 'ሰርዝ',
    edit: 'አርም',
    delete: 'ሰርዝ',
    add: 'ጨምር',
    search: 'ፈልግ',
    filter: 'አጣራ',
    export: 'ላክ',
    loading: 'እየጫነ ነው...',
    no_data: 'ምንም መረጃ አልተገኘም',
    confirm_delete: 'እርግጠኛ ነዎት ይህን መሰረዝ ይፈልጋሉ?',
    actions: 'ተግባሮች',
    status: 'ሁኔታ',
    name: 'ስም',
    date: 'ቀን',
    // Status labels
    pending: 'በመጠባበቅ ላይ',
    approved: 'ተቀባይነት አግኝቷል',
    rejected: 'ተቀባይነት አላገኘም',
    cancelled: 'ተሰርዟል',
    draft: 'ረቂቅ',
    reviewed: 'ተገምጋሚ',
    paid: 'ተከፍሏል',
    active: 'ንቁ',
    inactive: 'ንቁ ያልሆነ',
    // Employee
    employee_id: 'የሠራተኛ መለያ',
    full_name: 'ሙሉ ስም',
    department: 'ክፍል',
    position: 'ቦታ',
    hire_date: 'የቅጥር ቀን',
    // Leave
    leave_type: 'የፈቃድ ዓይነት',
    start_date: 'የመጀመሪያ ቀን',
    end_date: 'የመጨረሻ ቀን',
    days: 'ቀናት',
    reason: 'ምክንያት',
    balance: 'ቀሪ ቀናት',
    // Payroll
    basic_salary: 'መሰረተ ደሞዝ',
    gross_salary: 'ጠቅላላ ደሞዝ',
    net_pay: 'ተጣራ ክፍያ',
    income_tax: 'የገቢ ግብር',
    pension: 'ጡረታ',
    // Currency
    etb: 'ብር',
    // Roles
    admin: 'አስተዳዳሪ',
    sub_admin: 'ምክትል አስተዳዳሪ',
    manager: 'ሥራ አስኪያጅ',
    employee: 'ሠራተኛ',
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en, am },
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  })

export default i18n
