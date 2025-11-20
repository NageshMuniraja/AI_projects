'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export default function AddConnectorPage() {
  const router = useRouter()
  const [selectedType, setSelectedType] = useState('')
  const [loading, setLoading] = useState(false)

  const connectorTypes = [
    { id: 'gmail', name: 'Gmail', icon: '📧', requiresOAuth: true },
    { id: 'calendar', name: 'Google Calendar', icon: '📅', requiresOAuth: true },
    { id: 'hubspot', name: 'HubSpot CRM', icon: '🔗', requiresOAuth: true },
    { id: 'stripe', name: 'Stripe', icon: '💳', requiresOAuth: false },
    { id: 'razorpay', name: 'Razorpay', icon: '💰', requiresOAuth: false },
    { id: 'whatsapp', name: 'WhatsApp', icon: '💬', requiresOAuth: false },
  ]

  const handleConnect = async (type: string) => {
    setLoading(true)
    
    const connector = connectorTypes.find(c => c.id === type)
    
    if (connector?.requiresOAuth) {
      // Redirect to OAuth flow
      window.location.href = `/api/connectors/auth/${type}`
    } else {
      // Show API key input form
      setSelectedType(type)
      setLoading(false)
    }
  }

  if (selectedType) {
    return (
      <div>
        <div className="mb-8">
          <Button variant="ghost" onClick={() => setSelectedType('')}>
            ← Back
          </Button>
          <h1 className="text-3xl font-bold mt-4">
            Configure {connectorTypes.find(c => c.id === selectedType)?.name}
          </h1>
        </div>

        <div className="max-w-2xl bg-white p-8 rounded-lg shadow">
          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">
                Connector Name
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="My Stripe Account"
              />
            </div>

            {selectedType === 'stripe' && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Secret Key
                  </label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="sk_test_..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Publishable Key
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="pk_test_..."
                  />
                </div>
              </>
            )}

            {selectedType === 'razorpay' && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Key ID
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="rzp_test_..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Key Secret
                  </label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
              </>
            )}

            {selectedType === 'whatsapp' && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Twilio Account SID
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Auth Token
                  </label>
                  <input
                    type="password"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    WhatsApp Number
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="+1234567890"
                  />
                </div>
              </>
            )}

            <div className="flex space-x-4">
              <Button type="submit" className="flex-1">
                Save & Test Connection
              </Button>
              <Button type="button" variant="outline" onClick={() => setSelectedType('')}>
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <Button variant="ghost" onClick={() => router.back()}>
          ← Back to Connectors
        </Button>
        <h1 className="text-3xl font-bold mt-4">Add Connector</h1>
        <p className="text-gray-600 mt-1">Choose a service to connect</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {connectorTypes.map((connector) => (
          <div key={connector.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <div className="text-4xl mb-4">{connector.icon}</div>
            <h3 className="text-xl font-semibold mb-2">{connector.name}</h3>
            <p className="text-sm text-gray-600 mb-4">
              {connector.requiresOAuth ? 'OAuth 2.0 authentication' : 'API key authentication'}
            </p>
            <Button 
              className="w-full" 
              onClick={() => handleConnect(connector.id)}
              disabled={loading}
            >
              Connect {connector.name}
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
