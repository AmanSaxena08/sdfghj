import { Bar, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DailyError } from '../api/types'
import type { ChartColors } from '../hooks/useChartColors'
import { formatGw, formatIsoDay, formatMw, formatSignedMw } from '../lib/format'
import { LegendItem, Panel } from './Panel'
import type { TooltipProps } from '../lib/chart'

function DailyTooltip({ active, payload }: TooltipProps<DailyError>) {
  const day = payload?.[0]?.payload
  if (!active || !day) return null
  return (
    <div className="tooltip">
      <p className="tooltip-title">{formatIsoDay(day.day)}</p>
      <dl>
        <dt>Typical miss</dt>
        <dd>{formatMw(day.mae_mw)}</dd>
        <dt>Lean</dt>
        <dd className={day.bias_mw > 0 ? 'over' : 'under'}>{formatSignedMw(day.bias_mw)}</dd>
        <dt>Avg actual</dt>
        <dd>{formatMw(day.mean_actual_mw)}</dd>
        <dt>Avg forecast</dt>
        <dd>{formatMw(day.mean_forecast_mw)}</dd>
      </dl>
    </div>
  )
}

export function DailyErrorChart({ daily, colors }: { daily: DailyError[]; colors: ChartColors }) {
  return (
    <Panel
      className="span-2"
      title="Day by day"
      hint="Bars show whether the forecast ran high (above zero) or low that day; the line is the typical size of the miss."
      legend={
        <>
          <LegendItem color={colors.over} label="Ran high" />
          <LegendItem color={colors.under} label="Ran low" />
          <LegendItem color={colors.ink} label="Typical miss" dashed />
        </>
      }
    >
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={daily} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={colors.line} vertical={false} />
            <XAxis dataKey="day" tickFormatter={formatIsoDay} stroke={colors.muted} tickLine={false} fontSize={12} minTickGap={16} />
            <YAxis tickFormatter={formatGw} tickCount={6} stroke={colors.muted} tickLine={false} axisLine={false} fontSize={12} width={60} />
            <Tooltip content={DailyTooltip} cursor={{ fill: colors.line, opacity: 0.5 }} />
            <ReferenceLine y={0} stroke={colors.muted} />
            <Bar dataKey="bias_mw" radius={[2, 2, 2, 2]} maxBarSize={18} isAnimationActive={false}>
              {daily.map((d) => (
                <Cell key={d.day} fill={d.bias_mw > 0 ? colors.over : colors.under} fillOpacity={0.75} />
              ))}
            </Bar>
            <Line dataKey="mae_mw" stroke={colors.ink} strokeDasharray="4 3" strokeWidth={1.4} dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  )
}
