'use client'

import { useState } from 'react'
import { X, Database } from 'lucide-react'
import { useDatabaseStore } from '@/store/database-store'
import toast from 'react-hot-toast'

interface DatabaseConnectionModalProps {
  isOpen: boolean
  onClose: () => void
}

const DATABASE_TYPES = [
  // Traditional RDBMS
  { type: 'postgresql', name: 'PostgreSQL', icon: '🐘', defaultPort: 5432, category: 'RDBMS' },
  { type: 'mysql', name: 'MySQL', icon: '🐬', defaultPort: 3306, category: 'RDBMS' },
  { type: 'mariadb', name: 'MariaDB', icon: '🦭', defaultPort: 3306, category: 'RDBMS' },
  { type: 'mssql', name: 'SQL Server', icon: '🗄️', defaultPort: 1433, category: 'RDBMS' },
  { type: 'sqlite', name: 'SQLite', icon: '💾', defaultPort: 0, category: 'RDBMS' },
  { type: 'oracle', name: 'Oracle', icon: '🏛️', defaultPort: 1521, category: 'RDBMS' },
  { type: 'db2', name: 'IBM DB2', icon: '🔷', defaultPort: 50000, category: 'RDBMS' },
  
  // Cloud Data Warehouses
  { type: 'snowflake', name: 'Snowflake', icon: '❄️', defaultPort: 0, category: 'Cloud' },
  { type: 'redshift', name: 'Redshift', icon: '🔴', defaultPort: 5439, category: 'Cloud' },
  { type: 'bigquery', name: 'BigQuery', icon: '🔷', defaultPort: 0, category: 'Cloud' },
  
  // NoSQL
  { type: 'mongodb', name: 'MongoDB', icon: '🍃', defaultPort: 27017, category: 'NoSQL' },
  { type: 'cassandra', name: 'Cassandra', icon: '💿', defaultPort: 9042, category: 'NoSQL' },
  { type: 'dynamodb', name: 'DynamoDB', icon: '⚡', defaultPort: 0, category: 'NoSQL' },
]

export function DatabaseConnectionModal({ isOpen, onClose }: DatabaseConnectionModalProps) {
  const [selectedType, setSelectedType] = useState('postgresql')
  const [formData, setFormData] = useState({
    name: '',
    host: 'localhost',
    port: '5432',
    user: '',
    password: '',
    database: '',
  })

  const { addDatabase, setSelectedDatabase } = useDatabaseStore()

  const handleConnect = () => {
    if (!formData.name || !formData.database) {
      toast.error('Please fill in required fields')
      return
    }

    const newDatabase = {
      id: Date.now().toString(),
      name: formData.name,
      type: selectedType,
      connectionParams: {
        host: formData.host,
        port: parseInt(formData.port),
        user: formData.user,
        password: formData.password,
        database: formData.database,
      },
    }

    addDatabase(newDatabase)
    setSelectedDatabase(newDatabase)
    toast.success('Database connected successfully')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Connect to Database</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {/* Database Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Database Type</label>
            <div className="grid grid-cols-5 gap-2">
              {DATABASE_TYPES.map((db) => (
                <button
                  key={db.type}
                  onClick={() => {
                    setSelectedType(db.type)
                    setFormData((prev) => ({
                      ...prev,
                      port: db.defaultPort.toString(),
                    }))
                  }}
                  className={`p-3 border rounded-lg text-center hover:border-blue-500 ${
                    selectedType === db.type
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300'
                  }`}
                >
                  <div className="text-2xl mb-1">{db.icon}</div>
                  <div className="text-xs font-medium">{db.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Connection Form */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Connection Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="My Database"
              />
            </div>

            {selectedType !== 'sqlite' && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Host</label>
                    <input
                      type="text"
                      value={formData.host}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, host: e.target.value }))
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="localhost"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Port</label>
                    <input
                      type="number"
                      value={formData.port}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, port: e.target.value }))
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Username</label>
                  <input
                    type="text"
                    value={formData.user}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, user: e.target.value }))
                    }
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="postgres"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Password</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, password: e.target.value }))
                    }
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="••••••••"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium mb-1">
                Database Name *
              </label>
              <input
                type="text"
                value={formData.database}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, database: e.target.value }))
                }
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={selectedType === 'sqlite' ? '/path/to/database.db' : 'mydb'}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConnect}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Connect
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
