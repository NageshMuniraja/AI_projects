'use client'

import { useState } from 'react'
import { ChatInterface } from '@/components/chat/chat-interface'
import { DatabaseSelector } from '@/components/database/database-selector'
import { InsightsPanel } from '@/components/insights/insights-panel'
import { VisualizationPanel } from '@/components/visualizations/visualization-panel'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { useAuthStore } from '@/store/auth-store'
import { useQueryStore } from '@/store/query-store'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user } = useAuthStore()
  const { currentQuery, results, insights, visualizations } = useQueryStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-hidden flex">
          {/* Left Panel - Chat Interface */}
          <div className="flex-1 flex flex-col border-r">
            <div className="p-4 border-b bg-white">
              <DatabaseSelector />
            </div>
            
            <div className="flex-1 overflow-hidden">
              <ChatInterface />
            </div>
          </div>

          {/* Right Panel - Results & Insights */}
          <div className="w-1/2 flex flex-col overflow-hidden bg-white">
            <div className="flex-1 overflow-y-auto">
              {results && results.length > 0 && (
                <div className="space-y-4 p-4">
                  {/* Insights */}
                  {insights && (
                    <InsightsPanel insights={insights} />
                  )}

                  {/* Visualizations */}
                  {visualizations && visualizations.length > 0 && (
                    <VisualizationPanel 
                      data={results} 
                      visualizations={visualizations} 
                    />
                  )}

                  {/* Raw Data Table */}
                  <div className="bg-white rounded-lg border p-4">
                    <h3 className="text-lg font-semibold mb-4">Query Results</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            {Object.keys(results[0] || {}).map((key) => (
                              <th
                                key={key}
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                              >
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {results.slice(0, 100).map((row, idx) => (
                            <tr key={idx}>
                              {Object.values(row).map((value, cellIdx) => (
                                <td
                                  key={cellIdx}
                                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                                >
                                  {String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {results.length > 100 && (
                      <div className="mt-4 text-sm text-gray-500 text-center">
                        Showing 100 of {results.length} rows
                      </div>
                    )}
                  </div>
                </div>
              )}

              {!results && (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Ask a question to see insights and visualizations
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
