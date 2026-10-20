/**
 * Format a number as Ethiopian Birr (ETB).
 * @param {number|string} amount
 * @returns {string}
 */
export function formatETB(amount) {
  if (amount === null || amount === undefined) return 'ETB 0.00'
  return `ETB ${Number(amount).toLocaleString('en-ET', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * Format an ISO date string to readable format.
 * @param {string} dateStr
 * @returns {string}
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

/**
 * Map a status string to a badge CSS class.
 * @param {string} status
 * @returns {string}
 */
export function statusBadge(status) {
  const map = {
    ACTIVE: 'badge-green',
    APPROVED: 'badge-green',
    PAID: 'badge-green',
    PRESENT: 'badge-green',
    PENDING: 'badge-yellow',
    MANAGER_APPROVED: 'badge-yellow',
    REVIEWED: 'badge-yellow',
    DRAFT: 'badge-gray',
    REJECTED: 'badge-red',
    TERMINATED: 'badge-red',
    CANCELLED: 'badge-gray',
    INACTIVE: 'badge-gray',
    ABSENT: 'badge-red',
    LATE: 'badge-yellow',
  }
  return map[status] || 'badge-gray'
}

/**
 * Get human-readable label for a status.
 * @param {string} status
 * @returns {string}
 */
export function statusLabel(status) {
  const map = {
    ACTIVE: 'Active', INACTIVE: 'Inactive', TERMINATED: 'Terminated',
    PENDING: 'Pending', MANAGER_APPROVED: 'Manager Approved',
    APPROVED: 'Approved', REJECTED: 'Rejected', CANCELLED: 'Cancelled',
    DRAFT: 'Draft', REVIEWED: 'Reviewed', PAID: 'Paid',
    PRESENT: 'Present', ABSENT: 'Absent', LATE: 'Late', HALF_DAY: 'Half Day',
    ON_LEAVE: 'On Leave', HOLIDAY: 'Holiday',
  }
  return map[status] || status
}
