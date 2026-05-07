import React from 'react'
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from 'recharts'

/**
 * RiskGauge — displays a radial/gauge chart for scam risk percentage.
 * Props:
 *   score     : number  0–100
 *   riskLevel : string  LOW | MEDIUM | HIGH | CRITICAL
 *   confidence: number  0–100
 */

function getRiskColor(score) {
  if (score <= 30) return '#22c55e'   // green
  if (score <= 60) return '#eab308'   // yellow
  if (score <= 80) return '#f97316'   // orange
  return '#ef4444'                     // red
}

function getRiskBgColor(riskLevel) {
  switch (riskLevel) {
    case 'LOW':      return 'bg-green-100 text-green-800 border-green-300'
    case 'MEDIUM':   return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    case 'HIGH':     return 'bg-orange-100 text-orange-800 border-orange-300'
    case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300'
    default:         return 'bg-gray-100 text-gray-600 border-gray-300'
  }
}

function getRiskEmoji(riskLevel) {
  switch (riskLevel) {
    case 'LOW':      return '✅'
    case 'MEDIUM':   return '🔶'
    case 'HIGH':     return '⚠️'
    case 'CRITICAL': return '🚨'
    default:         return '❓'
  }
}

export default function RiskGauge({ score = 0, riskLevel = 'LOW', confidence = 0 }) {
  const color = getRiskColor(score)
  const data = [{ value: score, fill: color }]

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Radial gauge */}
      <div className="relative w-48 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="65%"
            outerRadius="90%"
            startAngle={225}
            endAngle={-45}
            data={data}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            {/* Background track */}
            <RadialBar
              background={{ fill: '#e5e7eb' }}
              dataKey="value"
              angleAxisId={0}
              data={data}
              cornerRadius={8}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>
            {score}
          </span>
          <span className="text-xs text-gray-500 font-medium">/ 100</span>
          <span className="text-xs text-gray-400 mt-0.5">Risk Score</span>
        </div>
      </div>

      {/* Risk level badge */}
      <div
        className={`flex items-center gap-2 px-4 py-2 rounded-full border font-bold text-sm ${getRiskBgColor(
          riskLevel
        )}`}
      >
        <span>{getRiskEmoji(riskLevel)}</span>
        <span>{riskLevel}</span>
      </div>

      {/* Confidence bar */}
      <div className="w-full">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Confidence / Keyakinan</span>
          <span className="font-semibold text-gray-700">{confidence}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-700"
            style={{ width: `${confidence}%`, backgroundColor: color }}
          />
        </div>
      </div>

      {/* Scale legend */}
      <div className="w-full grid grid-cols-4 gap-1 text-center text-xs">
        {[
          { label: 'LOW', color: 'bg-green-500', range: '0–30' },
          { label: 'MED', color: 'bg-yellow-500', range: '31–60' },
          { label: 'HIGH', color: 'bg-orange-500', range: '61–80' },
          { label: 'CRIT', color: 'bg-red-500', range: '81–100' },
        ].map((item) => (
          <div key={item.label} className="flex flex-col items-center gap-1">
            <div className={`w-full h-1.5 rounded-full ${item.color}`} />
            <span className="text-gray-500">{item.range}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
