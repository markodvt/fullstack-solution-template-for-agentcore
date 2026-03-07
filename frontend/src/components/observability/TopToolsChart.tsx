/**
 * Top Tools Chart Component
 * 
 * Displays a horizontal bar chart of the most frequently used tools.
 * Uses recharts library for visualization.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { ToolUsage } from '@/services/observabilityService'

interface TopToolsChartProps {
  tools: ToolUsage[]
}

const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
]

export default function TopToolsChart({ tools }: TopToolsChartProps) {
  if (tools.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No tool usage data available
      </div>
    )
  }

  // Take top 10 tools
  const topTools = tools.slice(0, 10)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={topTools}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="toolName" type="category" width={90} />
        <Tooltip />
        <Bar dataKey="usageCount" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]}>
          {topTools.map((_entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
