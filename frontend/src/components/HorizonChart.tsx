import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HorizonBucket } from '../api/types'
import type { ChartColors } from '../hooks/useChartColors'
import { formatGw, formatMw, formatPct } from '../lib/format'
import { Panel } from './Panel'
import type { TooltipProps } from '../lib/chart'

function HorizonTooltip({ active, payload }: TooltipProps<HorizonBucket>) {
  const bucket = payload?.[0]?.payload
  if (!active || !bucket) return null
  return (
    <div className="tooltip">
      <p className="tooltip-title">
        Made {bucket.from_hours}–{bucket.to_hours} h ahead
      </p>
      <dl>
        <dt>Typical miss</dt>
        <dd>{formatMw(bucket.mae_mw)}</dd>
        <dt>Relative</dt>
        <dd>{formatPct(bucket.mae_pct_of_mean)}</dd>
        <dt>Forecasts</dt>
        <dd>{bucket.count.toLocaleString('en-GB')}</dd>
      </dl>
    </div>
  )
}

interface HorizonChartProps {
  buckets: HorizonBucket[]
  /** Range of lead times used by the decision-time forecasts, to highlight on the chart. */
  usedRange: [number, number] | null
  colors: ChartColors
}

export function HorizonChart({ buckets, usedRange, colors }: HorizonChartProps) {
  const isUsed = (b: HorizonBucket) => usedRange !== null && b.to_hours > usedRange[0] && b.from_hours < usedRange[1]

  return (
    <Panel
      title="Earlier forecasts miss more"
      hint="Typical miss of every published forecast, by how far ahead it was made. Highlighted: the lead times your decision time uses."
    >
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={buckets} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap={3}>
            <CartesianGrid stroke={colors.line} vertical={false} />
            <XAxis
              dataKey="from_hours"
              tickFormatter={(h: number) => `${h}h`}
              stroke={colors.muted}
              tickLine={false}
              fontSize={12}
            />
            <YAxis tickFormatter={formatGw} tickCount={6} stroke={colors.muted} tickLine={false} axisLine={false} fontSize={12} width={60} />
            <Tooltip content={HorizonTooltip} cursor={{ fill: colors.line, opacity: 0.5 }} />
            <Bar dataKey="mae_mw" radius={[2, 2, 0, 0]} isAnimationActive={false}>
              {buckets.map((b) => (
                <Cell key={b.from_hours} fill={isUsed(b) ? colors.accent : colors.muted} fillOpacity={isUsed(b) ? 0.9 : 0.35} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  )
}
