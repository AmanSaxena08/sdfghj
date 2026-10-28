import { useMemo } from 'react'
import { Brush, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { SeriesPoint } from '../api/types'
import type { ChartColors } from '../hooks/useChartColors'
import { formatDateTime, formatDay, formatGw, formatHours, formatMw, formatSignedMw } from '../lib/format'
import { LegendItem, Panel } from './Panel'
import type { TooltipProps } from '../lib/chart'

interface ChartPoint {
  t: number
  actual: number
  forecast: number | null
  error: number | null
  published: string | null
  horizon: number | null
}

/** Ticks at midnight, thinned out so the axis never shows more than ~8 labels. */
function dayTicks(points: ChartPoint[]): number[] {
  const midnights = points.filter((p) => new Date(p.t).getUTCHours() === 0).map((p) => p.t)
  const step = Math.max(1, Math.ceil(midnights.length / 8))
  return midnights.filter((_, i) => i % step === 0)
}

function ForecastTooltip({ active, payload }: TooltipProps<ChartPoint>) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  return (
    <div className="tooltip">
      <p className="tooltip-title">{formatDateTime(point.t)}</p>
      <dl>
        <dt>Actual</dt>
        <dd>{formatMw(point.actual)}</dd>
        <dt>Forecast</dt>
        <dd>{point.forecast === null ? 'none available' : formatMw(point.forecast)}</dd>
        {point.error !== null && (
          <>
            <dt>Error</dt>
            <dd className={point.error > 0 ? 'over' : 'under'}>{formatSignedMw(point.error)}</dd>
          </>
        )}
      </dl>
      {point.published && point.horizon !== null && (
        <p className="tooltip-note">
          Forecast published {formatDateTime(point.published)}, {formatHours(point.horizon)} ahead
        </p>
      )}
    </div>
  )
}

export function ForecastChart({ points, cutoff, colors }: { points: SeriesPoint[]; cutoff: string; colors: ChartColors }) {
  const data = useMemo<ChartPoint[]>(
    () =>
      points.map((p) => ({
        t: Date.parse(p.time),
        actual: p.actual_mw,
        forecast: p.forecast_mw,
        error: p.error_mw,
        published: p.publish_time,
        horizon: p.horizon_hours,
      })),
    [points],
  )
  const ticks = useMemo(() => dayTicks(data), [data])

  return (
    <Panel
      className="span-2"
      title="Forecast at decision time vs what the wind delivered"
      hint={`Each hour shows the newest forecast published before ${cutoff} UK on the day before delivery. Drag the handles below to zoom.`}
      legend={
        <>
          <LegendItem color={colors.ink} label="Actual" />
          <LegendItem color={colors.accent} label="Forecast" />
        </>
      }
    >
      <div className="chart chart-tall">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={colors.line} vertical={false} />
            <XAxis
              dataKey="t"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              ticks={ticks}
              tickFormatter={formatDay}
              stroke={colors.muted}
              tickLine={false}
              fontSize={12}
            />
            <YAxis tickFormatter={formatGw} tickCount={6} stroke={colors.muted} tickLine={false} axisLine={false} fontSize={12} width={60} />
            <Tooltip content={ForecastTooltip} cursor={{ stroke: colors.muted, strokeDasharray: '3 3' }} />
            <Line dataKey="actual" stroke={colors.ink} strokeWidth={1.6} dot={false} isAnimationActive={false} />
            <Line
              dataKey="forecast"
              stroke={colors.accent}
              strokeWidth={1.6}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
            <Brush
              dataKey="t"
              height={26}
              travellerWidth={8}
              stroke={colors.muted}
              fill={colors.surface}
              tickFormatter={formatDay}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  )
}
