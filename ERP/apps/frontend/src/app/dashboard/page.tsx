import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's your overview.</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-600 mb-1">Total Revenue</div>
          <div className="text-2xl font-bold">$125,450</div>
          <div className="text-sm text-green-600 mt-1">+15% from last month</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-600 mb-1">Active Leads</div>
          <div className="text-2xl font-bold">48</div>
          <div className="text-sm text-blue-600 mt-1">12 high priority</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-600 mb-1">Pending Invoices</div>
          <div className="text-2xl font-bold">8</div>
          <div className="text-sm text-orange-600 mt-1">3 overdue</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-600 mb-1">Agent Executions</div>
          <div className="text-2xl font-bold">1,234</div>
          <div className="text-sm text-gray-600 mt-1">Last 7 days</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <Link href="/dashboard/connectors/add">
            <Button className="w-full" variant="outline">
              + Add Connector
            </Button>
          </Link>
          <Link href="/dashboard/agents">
            <Button className="w-full" variant="outline">
              🤖 Run Agent
            </Button>
          </Link>
          <Link href="/dashboard/reports">
            <Button className="w-full" variant="outline">
              📊 Generate Report
            </Button>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Recent Agent Actions</h2>
          <div className="space-y-4">
            {[
              { agent: 'Finance Agent', action: 'Sent 3 invoice reminders', time: '5 min ago', status: 'success' },
              { agent: 'Sales Agent', action: 'Scored new lead (85 points)', time: '12 min ago', status: 'success' },
              { agent: 'Finance Agent', action: 'Detected payment anomaly', time: '1 hour ago', status: 'warning' },
              { agent: 'Reporting Agent', action: 'Generated daily summary', time: '2 hours ago', status: 'success' },
            ].map((activity, i) => (
              <div key={i} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  activity.status === 'success' ? 'bg-green-500' : 'bg-orange-500'
                }`} />
                <div className="flex-1">
                  <div className="font-medium">{activity.agent}</div>
                  <div className="text-sm text-gray-600">{activity.action}</div>
                  <div className="text-xs text-gray-500 mt-1">{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Connected Services</h2>
          <div className="space-y-4">
            {[
              { name: 'Gmail', status: 'active', lastSync: '2 min ago' },
              { name: 'Google Calendar', status: 'active', lastSync: '5 min ago' },
              { name: 'HubSpot CRM', status: 'active', lastSync: '10 min ago' },
              { name: 'Stripe', status: 'active', lastSync: '15 min ago' },
            ].map((connector, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <div>
                    <div className="font-medium">{connector.name}</div>
                    <div className="text-xs text-gray-500">Last sync: {connector.lastSync}</div>
                  </div>
                </div>
                <Link href={`/dashboard/connectors/${i}`}>
                  <Button variant="ghost" size="sm">View</Button>
                </Link>
              </div>
            ))}
          </div>
          <Link href="/dashboard/connectors/add">
            <Button className="w-full mt-4" variant="outline">
              + Add New Connector
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
