'use client'

import { Mail, CreditCard, Video, BarChart3, MessageCircle, Database, Zap, CheckCircle } from 'lucide-react'

export default function IntegrationSettings() {
  const integrations = [
    { icon: Mail, title: 'Email Service', description: 'SendGrid, Mailgun, AWS SES', color: 'blue', enabled: true },
    { icon: CreditCard, title: 'Payment Gateway', description: 'Stripe, PayPal', color: 'purple', enabled: true },
    { icon: Video, title: 'Video Conferencing', description: 'Zoom, Google Meet', color: 'green', enabled: false },
    { icon: BarChart3, title: 'Analytics', description: 'Google Analytics, Mixpanel', color: 'yellow', enabled: true },
    { icon: MessageCircle, title: 'Live Chat', description: 'Intercom, Crisp', color: 'red', enabled: false },
    { icon: Database, title: 'Cloud Storage', description: 'AWS S3, MinIO', color: 'indigo', enabled: true }
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {integrations.map((integration, index) => {
          const Icon = integration.icon
          return (
            <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className={`w-12 h-12 bg-${integration.color}-100 rounded-lg flex items-center justify-center`}>
                    <Icon className={`w-6 h-6 text-${integration.color}-600`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">{integration.title}</h4>
                    <p className="text-sm text-gray-600">{integration.description}</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={integration.enabled} className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-pink-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-pink-500 peer-checked:to-purple-600"></div>
                </label>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                {integration.enabled ? 'Automated integration for platform services' : 'Enable integration for additional features'}
              </p>
              <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Configure</button>
            </div>
          )
        })}
      </div>

      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5" />
          API Access & Webhooks
        </h3>
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold text-gray-800 mb-1">API Keys</h4>
                <p className="text-sm text-gray-600">Manage access tokens for external integrations</p>
              </div>
              <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Manage Keys</button>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span>3 active keys</span>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold text-gray-800 mb-1">Webhooks</h4>
                <p className="text-sm text-gray-600">Configure event notifications to external services</p>
              </div>
              <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Add Webhook</button>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span>2 webhooks configured</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-pink-600 hover:to-purple-700 transition-all">
          Save Integration Settings
        </button>
      </div>
    </div>
  )
}
