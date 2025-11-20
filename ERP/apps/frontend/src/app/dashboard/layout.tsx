import { UserButton } from '@clerk/nextjs'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="text-xl font-bold text-blue-600">
                AI Agent Platform
              </Link>
              <div className="hidden md:flex space-x-6">
                <Link href="/dashboard" className="text-gray-700 hover:text-blue-600">
                  Dashboard
                </Link>
                <Link href="/dashboard/agents" className="text-gray-700 hover:text-blue-600">
                  Agents
                </Link>
                <Link href="/dashboard/connectors" className="text-gray-700 hover:text-blue-600">
                  Connectors
                </Link>
                <Link href="/dashboard/workflows" className="text-gray-700 hover:text-blue-600">
                  Workflows
                </Link>
                <Link href="/dashboard/reports" className="text-gray-700 hover:text-blue-600">
                  Reports
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="container mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  )
}
