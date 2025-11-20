import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function ConnectorsPage() {
  const connectors = [
    {
      id: '1',
      type: 'gmail',
      name: 'Gmail',
      status: 'active',
      lastSync: '2 minutes ago',
      description: 'Email integration for automated communication',
    },
    {
      id: '2',
      type: 'calendar',
      name: 'Google Calendar',
      status: 'active',
      lastSync: '5 minutes ago',
      description: 'Calendar integration for meeting scheduling',
    },
    {
      id: '3',
      type: 'hubspot',
      name: 'HubSpot CRM',
      status: 'active',
      lastSync: '10 minutes ago',
      description: 'CRM integration for lead management',
    },
    {
      id: '4',
      type: 'stripe',
      name: 'Stripe',
      status: 'active',
      lastSync: '15 minutes ago',
      description: 'Payment processing integration',
    },
  ]

  const availableConnectors = [
    { type: 'razorpay', name: 'Razorpay', description: 'Alternative payment processor' },
    { type: 'whatsapp', name: 'WhatsApp', description: 'Messaging via Twilio' },
    { type: 'zoho', name: 'Zoho CRM', description: 'Alternative CRM system' },
    { type: 'salesforce', name: 'Salesforce', description: 'Enterprise CRM' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Connectors</h1>
          <p className="text-gray-600 mt-1">Manage your integrations</p>
        </div>
        <Link href="/dashboard/connectors/add">
          <Button>+ Add Connector</Button>
        </Link>
      </div>

      {/* Active Connectors */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Active Connectors</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {connectors.map((connector) => (
            <div key={connector.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
                    {connector.type === 'gmail' && '📧'}
                    {connector.type === 'calendar' && '📅'}
                    {connector.type === 'hubspot' && '🔗'}
                    {connector.type === 'stripe' && '💳'}
                  </div>
                  <div>
                    <h3 className="font-semibold">{connector.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-sm text-gray-600">{connector.status}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">{connector.description}</p>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Last sync: {connector.lastSync}</span>
                <div className="space-x-2">
                  <Button variant="ghost" size="sm">Test</Button>
                  <Button variant="ghost" size="sm">Configure</Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Available Connectors */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Available Connectors</h2>
        <div className="grid md:grid-cols-4 gap-4">
          {availableConnectors.map((connector) => (
            <div key={connector.type} className="bg-white p-4 rounded-lg shadow text-center">
              <div className="text-3xl mb-2">
                {connector.type === 'razorpay' && '💰'}
                {connector.type === 'whatsapp' && '💬'}
                {connector.type === 'zoho' && '📊'}
                {connector.type === 'salesforce' && '☁️'}
              </div>
              <h3 className="font-medium mb-1">{connector.name}</h3>
              <p className="text-xs text-gray-600 mb-3">{connector.description}</p>
              <Link href={`/dashboard/connectors/add?type=${connector.type}`}>
                <Button size="sm" variant="outline" className="w-full">
                  Connect
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
