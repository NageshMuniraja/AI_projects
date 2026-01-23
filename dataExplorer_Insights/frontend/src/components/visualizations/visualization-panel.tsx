'use client'

import { useState } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface VisualizationPanelProps {
  data: any[]
  visualizations: any[]
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export function VisualizationPanel({ data, visualizations }: VisualizationPanelProps) {
  const [selectedViz, setSelectedViz] = useState(0)

  if (!visualizations || visualizations.length === 0) return null

  const currentViz = visualizations[selectedViz]

  const renderVisualization = () => {
    switch (currentViz.type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={currentViz.x_axis} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={currentViz.y_axis} stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={currentViz.x_axis} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={currentViz.y_axis} fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        )

      case 'pie':
        const pieData = data.slice(0, 10).map((item: any) => ({
          name: item[currentViz.category],
          value: parseFloat(item[currentViz.value]) || 0,
        }))

        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={currentViz.x_axis} />
              <YAxis dataKey={currentViz.y_axis} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Legend />
              <Scatter name="Data Points" data={data} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>
        )

      default:
        return <div className="text-gray-500">Visualization type not supported</div>
    }
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Visualizations</h3>
        
        {visualizations.length > 1 && (
          <div className="flex space-x-2">
            {visualizations.map((viz, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedViz(idx)}
                className={`px-3 py-1 text-sm rounded ${
                  selectedViz === idx
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {viz.title || viz.type}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mb-2">
        <h4 className="text-sm font-medium">{currentViz.title}</h4>
        <p className="text-xs text-gray-500">{currentViz.description}</p>
      </div>

      <div className="mt-4">
        {renderVisualization()}
      </div>
    </div>
  )
}
