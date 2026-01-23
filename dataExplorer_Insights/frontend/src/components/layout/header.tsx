'use client'

import { User, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">DataInsights AI</h1>
        <p className="text-sm text-gray-500">Enterprise Database Analytics Platform</p>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <User className="h-5 w-5 text-gray-600" />
          <span className="text-sm font-medium">{user?.email || 'Guest'}</span>
        </div>
        
        <button
          onClick={logout}
          className="flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </button>
      </div>
    </header>
  )
}
