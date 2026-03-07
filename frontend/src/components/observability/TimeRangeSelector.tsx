/**
 * Time Range Selector Component
 * 
 * Allows users to select a time range for metrics:
 * - 1 hour
 * - 24 hours (1 day)
 * - 168 hours (7 days)
 * - 720 hours (30 days)
 */

import { Button } from '@/components/ui/button'

interface TimeRangeSelectorProps {
  value: number
  onChange: (timeRange: number) => void
}

const TIME_RANGES = [
  { label: '1h', value: 1 },
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 },
]

export default function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium">Time Range:</span>
      <div className="flex gap-1">
        {TIME_RANGES.map((range) => (
          <Button
            key={range.value}
            variant={value === range.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => onChange(range.value)}
          >
            {range.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
