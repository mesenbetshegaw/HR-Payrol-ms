import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { logout } from '../../api/auth'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/index'

export default function Topbar({ onToggleSidebar }) {
  const { t, i18n } = useTranslation()
  const { user, logoutUser } = useAuth()
  const navigate = useNavigate()
  const [showProfile, setShowProfile] = useState(false)

  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: () => getUnreadCount().then(r => r.data),
    refetchInterval: 30000,
  })

  const handleLogout = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      await logout(refresh)
    } catch (_) {}
    logoutUser()
    navigate('/login')
  }

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'am' : 'en')
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-30">
      <button onClick={onToggleSidebar} className="text-gray-500 hover:text-gray-700 p-1 rounded">
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className="flex items-center gap-4">
        {/* Language Toggle */}
        <button
          onClick={toggleLang}
          className="text-sm font-medium text-gray-600 hover:text-primary-600 border border-gray-200 rounded-lg px-3 py-1.5 transition-colors"
        >
          {i18n.language === 'en' ? 'አማርኛ' : 'English'}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="relative text-gray-500 hover:text-gray-700 p-1"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {(unreadData?.unread_count ?? 0) > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
              {unreadData.unread_count > 9 ? '9+' : unreadData.unread_count}
            </span>
          )}
        </button>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
          >
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="hidden md:block text-left">
              <p className="font-medium text-sm">{user?.first_name} {user?.last_name}</p>
              <p className="text-xs text-gray-400">{user?.role?.replace('_', ' ')}</p>
            </div>
          </button>
          {showProfile && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-1 z-50">
              <button onClick={() => { navigate('/profile'); setShowProfile(false) }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                My Profile
              </button>
              <button onClick={() => { navigate('/change-password'); setShowProfile(false) }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                {t('change_password')}
              </button>
              <hr className="my-1" />
              <button onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                {t('logout')}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
