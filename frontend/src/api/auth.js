import api from './client'

export const login = (credentials) => api.post('/auth/login/', credentials)
export const logout = (refresh) => api.post('/auth/logout/', { refresh })
export const getMe = () => api.get('/auth/me/')
export const changePassword = (data) => api.post('/auth/change-password/', data)
export const forgotPassword = (email) => api.post('/auth/forgot-password/', { email })
export const resetPassword = (data) => api.post('/auth/reset-password/', data)
export const getUsers = (params) => api.get('/auth/users/', { params })
export const createUser = (data) => api.post('/auth/users/', data)
export const updateUser = (id, data) => api.patch(`/auth/users/${id}/`, data)
export const unlockUser = (id) => api.post(`/auth/users/${id}/unlock/`)
export const getPermissionMatrix = (userId) => api.get(`/auth/permissions/matrix/${userId}/`)
export const updatePermissionMatrix = (userId, permissions) => api.put(`/auth/permissions/matrix/${userId}/`, { permissions })
