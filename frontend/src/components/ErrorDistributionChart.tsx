import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HistogramBin } from '../api/types'
import type { ChartColors } from '../hooks/useChartColors'
import { formatGw, formatSignedMw } from '../lib/format'
import { Panel } from './Panel'
import type { TooltipProps } from '../lib/chart'

interface BinPoint extends HistogramBin {
  mid: number
  share: number
}

function BinTooltip({ active, payload }: TooltipProps<BinPoint>) {
  const bin = payload?.[0]?.payload
  if (!active || !bin) return null
  return (
    <div className="tooltip">
      <p className="tooltip-title">
        {formatSignedMw(bin.from_mw)} to {formatSignedMw(bin.to_mw)}
      </p>
      <p className="tooltip-note">
        {bin.count} hours ({(bin.share * 100).toFixed(1)}%)
      </p>
    </div>
  )
}

export function ErrorDistributionChart({ bins, colors }: { bins: HistogramBin[]; colors: ChartColors }) {
  const total = bins.reduce((sum, b) => sum + b.count, 0)
  const data: BinPoint[] = bins.map((b) => ({ ...b, mid: (b.from_mw + b.to_mw) / 2, share: total ? b.count / total : 0 }))
  const domain: [number, number] = [bins[0]?.from_mw ?? 0, bins.at(-1)?.to_mw ?? 0]
  // Whole-gigawatt ticks read better than the bin centres.
  const ticks: number[] = []
  for (let mw = Math.ceil(domain[0] / 2000) * 2000; mw <= domain[1]; mw += 2000) ticks.push(mw)

  return (
    <Panel
      title="How big the misses are"
      hint="Hours grouped by forecast error (forecast minus actual). Right of zero: forecast too high."
    >
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap={1}>
            <CartesianGrid stroke={colors.line} vertical={false} />
            <XAxis
              dataKey="mid"
              type="number"
              domain={domain}
              ticks={ticks}
              tickFormatter={formatGw}
              stroke={colors.muted}
              tickLine={false}
              fontSize={12}
            />
            <YAxis stroke={colors.muted} tickLine={false} axisLine={false} fontSize={12} width={36} allowDecimals={false} />
            <Tooltip content={BinTooltip} cursor={{ fill: colors.line, opacity: 0.5 }} />
            <Bar dataKey="count" isAnimationActive={false}>
              {data.map((b) => (
                <Cell key={b.from_mw} fill={b.mid > 0 ? colors.over : colors.under} fillOpacity={0.75} />
              ))}
            </Bar>
            <ReferenceLine x={0} stroke={colors.ink} strokeDasharray="3 3" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  )
}
