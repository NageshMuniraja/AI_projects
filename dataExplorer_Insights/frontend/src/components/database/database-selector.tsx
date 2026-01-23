'use client'

import { useState } from 'react'
import { Database, ChevronDown } from 'lucide-react'
import { useDatabaseStore } from '@/store/database-store'
import { DatabaseConnectionModal } from './database-connection-modal'

export function DatabaseSelector() {
  const [showModal, setShowModal] = useState(false)
  const { selectedDatabase, databases } = useDatabaseStore()

  const databaseIcons: Record<string, string> = {
    postgresql: '🐘',
    mysql: '🐬',
    mssql: '💾',
    sqlite: '📦',
    mongodb: '🍃',
  }

  return (
    <div>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center space-x-2 w-full px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
      >
        <Database className="h-5 w-5 text-gray-600" />
        <div className="flex-1 text-left">
          {selectedDatabase ? (
            <div>
              <p className="text-sm font-medium">
                {databaseIcons[selectedDatabase.type]} {selectedDatabase.name}
              </p>
              <p className="text-xs text-gray-500">{selectedDatabase.type}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a database</p>
          )}
        </div>
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </button>

      <DatabaseConnectionModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </div>
  )
}
