import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function AgentsPage() {
  const agents = [
    {
      id: 'finance',
      name: 'Finance Agent',
      icon: '💰',
      description: 'Manages invoices, payments, and financial operations',
      status: 'active',
      executions: 234,
      successRate: 98.5,
      actions: [
        'Parse invoices',
        'Detect overdue payments',
        'Reconcile payments',
        'Detect anomalies',
      ],
    },
    {
      id: 'sales',
      name: 'Sales Agent',
      icon: '📈',
      description: 'Handles lead management and sales automation',
      status: 'active',
      executions: 156,
      successRate: 96.2,
      actions: [
        'Score leads',
        'Intake new leads',
        'Schedule meetings',
        'Update CRM',
      ],
    },
    {
      id: 'reporting',
      name: 'Reporting Agent',
      icon: '📊',
      description: 'Generates reports and analytics',
      status: 'active',
      executions: 89,
      successRate: 100,
      actions: [
        'Generate summaries',
        'Create reports',
        'Analyze trends',
        'Send insights',
      ],
    },
    {
      id: 'supervisor',
      name: 'Supervisor Agent',
      icon: '🎯',
      description: 'Manages approvals and conflict resolution',
      status: 'beta',
      executions: 12,
      successRate: 100,
      actions: [
        'Review actions',
        'Handle approvals',
        'Resolve conflicts',
        'Risk assessment',
      ],
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">AI Agents</h1>
          <p className="text-gray-600 mt-1">Manage and monitor your intelligent agents</p>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="text-4xl">{agent.icon}</div>
                <div>
                  <h3 className="text-xl font-semibold">{agent.name}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                    }`} />
                    <span className="text-sm text-gray-600 capitalize">{agent.status}</span>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-gray-600 mb-4">{agent.description}</p>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-xs text-gray-600">Executions</div>
                <div className="text-xl font-semibold">{agent.executions}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-xs text-gray-600">Success Rate</div>
                <div className="text-xl font-semibold">{agent.successRate}%</div>
              </div>
            </div>

            {/* Capabilities */}
            <div className="mb-4">
              <div className="text-sm font-medium mb-2">Capabilities:</div>
              <div className="flex flex-wrap gap-2">
                {agent.actions.map((action, i) => (
                  <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {action}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-2">
              <Link href={`/dashboard/agents/${agent.id}`} className="flex-1">
                <Button variant="outline" className="w-full">View Details</Button>
              </Link>
              <Link href={`/dashboard/agents/${agent.id}/run`} className="flex-1">
                <Button className="w-full">Run Agent</Button>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Agent Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Recent Agent Actions</h2>
        <div className="space-y-3">
          {[
            {
              agent: 'Finance Agent',
              action: 'Sent 3 overdue invoice reminders',
              time: '5 minutes ago',
              status: 'success',
              confidence: 0.95,
            },
            {
              agent: 'Sales Agent',
              action: 'Scored new lead: TechCorp Inc (Score: 85)',
              time: '12 minutes ago',
              status: 'success',
              confidence: 0.92,
            },
            {
              agent: 'Finance Agent',
              action: 'Detected payment anomaly - flagged for review',
              time: '1 hour ago',
              status: 'warning',
              confidence: 0.88,
            },
            {
              agent: 'Reporting Agent',
              action: 'Generated daily financial summary',
              time: '2 hours ago',
              status: 'success',
              confidence: 1.0,
            },
            {
              agent: 'Sales Agent',
              action: 'Scheduled meeting with lead via Calendar',
              time: '3 hours ago',
              status: 'success',
              confidence: 0.96,
            },
          ].map((log, i) => (
            <div key={i} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                log.status === 'success' ? 'bg-green-500' : 'bg-orange-500'
              }`} />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{log.agent}</span>
                  <span className="text-xs text-gray-500">{log.time}</span>
                </div>
                <p className="text-sm text-gray-700 mb-1">{log.action}</p>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">
                    Confidence: {(log.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
