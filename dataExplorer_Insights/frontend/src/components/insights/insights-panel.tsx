'use client'

import ReactMarkdown from 'react-markdown'
import { TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'

interface InsightsPanelProps {
  insights: any
}

export function InsightsPanel({ insights }: InsightsPanelProps) {
  if (!insights) return null

  const { narrative, statistics, patterns } = insights

  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
        Insights & Analysis
      </h3>

      {/* Narrative Insights */}
      {narrative && (
        <div className="mb-6 prose prose-sm max-w-none">
          <ReactMarkdown>{narrative}</ReactMarkdown>
        </div>
      )}

      {/* Key Metrics */}
      {statistics && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold mb-3">Key Metrics</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-gray-600">Total Rows</p>
              <p className="text-2xl font-bold text-blue-600">
                {statistics.row_count?.toLocaleString()}
              </p>
            </div>
            
            {Object.entries(statistics.numeric || {}).slice(0, 5).map(([key, value]: [string, any]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600">{key}</p>
                <p className="text-lg font-semibold">
                  {value.sum?.toLocaleString() || value.mean?.toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns */}
      {patterns && (
        <div className="space-y-4">
          {patterns.trends && patterns.trends.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 flex items-center">
                <TrendingUp className="h-4 w-4 mr-2 text-green-600" />
                Trends Detected
              </h4>
              <div className="space-y-2">
                {patterns.trends.map((trend: any, idx: number) => (
                  <div key={idx} className="flex items-center text-sm bg-green-50 rounded p-2">
                    <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                    <span>
                      <strong>{trend.column}</strong> is {trend.direction} (strength: {(trend.strength * 100).toFixed(0)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {patterns.anomalies && patterns.anomalies.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 flex items-center">
                <AlertCircle className="h-4 w-4 mr-2 text-orange-600" />
                Anomalies Found
              </h4>
              <div className="space-y-2">
                {patterns.anomalies.map((anomaly: any, idx: number) => (
                  <div key={idx} className="flex items-center text-sm bg-orange-50 rounded p-2">
                    <AlertCircle className="h-4 w-4 mr-2 text-orange-600" />
                    <span>
                      <strong>{anomaly.column}</strong> has {anomaly.count} outliers ({anomaly.percentage.toFixed(1)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {patterns.correlations && patterns.correlations.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Correlations</h4>
              <div className="space-y-2">
                {patterns.correlations.map((corr: any, idx: number) => (
                  <div key={idx} className="text-sm bg-blue-50 rounded p-2">
                    <strong>{corr.column1}</strong> and <strong>{corr.column2}</strong> have a {corr.strength} correlation ({(corr.correlation * 100).toFixed(0)}%)
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
