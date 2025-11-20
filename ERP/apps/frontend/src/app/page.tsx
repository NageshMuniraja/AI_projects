import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="text-2xl font-bold text-blue-600">AI Agent Platform</div>
          <div className="space-x-4">
            <Link href="/sign-in">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/sign-up">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-6 text-gray-900">
            Automate Your Business with AI Agents
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Intelligent agents for finance, sales, and reporting. Connect your tools, 
            automate workflows, and let AI handle the rest.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/sign-up">
              <Button size="lg" className="text-lg px-8">
                Start Free Trial
              </Button>
            </Link>
            <Link href="#features">
              <Button size="lg" variant="outline" className="text-lg px-8">
                Learn More
              </Button>
            </Link>
          </div>
        </div>

        <div id="features" className="mt-32 grid md:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-4">💰</div>
            <h3 className="text-xl font-semibold mb-2">Finance Agent</h3>
            <p className="text-gray-600">
              Automate invoice processing, payment reminders, and reconciliation. 
              Detect anomalies and prevent revenue leakage.
            </p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-4">📈</div>
            <h3 className="text-xl font-semibold mb-2">Sales Agent</h3>
            <p className="text-gray-600">
              Intelligent lead scoring, automated follow-ups, and meeting scheduling. 
              Keep your pipeline moving automatically.
            </p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Reporting Agent</h3>
            <p className="text-gray-600">
              Generate comprehensive reports automatically. Daily summaries, 
              analytics, and insights delivered to your inbox.
            </p>
          </div>
        </div>

        <div className="mt-32 text-center">
          <h2 className="text-3xl font-bold mb-6">Integrates with Your Tools</h2>
          <div className="flex justify-center gap-8 flex-wrap">
            {['Gmail', 'Calendar', 'HubSpot', 'Stripe', 'Razorpay', 'WhatsApp'].map((tool) => (
              <div key={tool} className="px-6 py-3 bg-gray-100 rounded-lg font-medium">
                {tool}
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="container mx-auto px-6 py-8 mt-20 border-t">
        <div className="text-center text-gray-600">
          © 2025 AI Agent Platform. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
