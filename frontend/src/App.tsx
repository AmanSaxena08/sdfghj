import { useMemo, useState } from 'react'
import type { Meta, Period } from './api/types'
import { Controls } from './components/Controls'
import { DailyErrorChart } from './components/DailyErrorChart'
import { ErrorDistributionChart } from './components/ErrorDistributionChart'
import { ForecastChart } from './components/ForecastChart'
import { HorizonChart } from './components/HorizonChart'
import { KpiCards } from './components/KpiCards'
import { useChartColors } from './hooks/useChartColors'
import { useDashboardData, useMeta } from './hooks/useDashboardData'
import { useTheme } from './hooks/useTheme'
import { formatDateTime, formatIsoDay, formatMw, formatPct } from './lib/format'

export default function App() {
  const { meta, error } = useMeta()
  const [theme, toggleTheme] = useTheme()

  return (
    <div className="page">
      <nav className="topbar">
        <span className="brand">
          <span className="brand-mark" aria-hidden="true" />
          Wind Forecast Monitor
        </span>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
        >
          {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
      </nav>

      <header className="masthead">
        <p className="eyebrow">GB day-ahead · national wind · January 2026 decisions</p>
        <h1>
          How much wind can you <em>count on</em> tomorrow?
        </h1>
        <p className="lede">
          The latest wind forecast available when the day-ahead purchase is made, set against what the wind actually
          delivered, and how far that forecast can be trusted.
        </p>
      </header>

      {error && <p className="notice error">Could not reach the data service: {error}</p>}
      {!meta && !error && <p className="notice">Loading…</p>}
      {meta && <Dashboard meta={meta} />}
    </div>
  )
}

function Dashboard({ meta }: { meta: Meta }) {
  // State objects keep their identity between renders, so data is refetched only when the selection changes.
  const [period, setPeriod] = useState<Period>({
    start: meta.delivery_first_day,
    end: meta.delivery_last_day,
    cutoff: meta.default_cutoff,
  })
  const { data, loading, error } = useDashboardData(period)
  const colors = useChartColors()

  const usedHorizon = useMemo<[number, number] | null>(() => {
    const hours = data?.series.points.flatMap((p) => (p.horizon_hours === null ? [] : [p.horizon_hours])) ?? []
    return hours.length ? [Math.min(...hours), Math.max(...hours)] : null
  }, [data])

  const summary = data?.metrics.summary

  return (
    <main>
      <Controls meta={meta} period={period} onChange={setPeriod} />

      {error && <p className="notice error">{error}</p>}
      {!data && !error && <p className="notice">Loading…</p>}

      {data && (
        <div className={`results ${loading ? 'is-loading' : ''}`} aria-busy={loading}>
          {summary && (
            <p className="takeaway">
              For delivery {formatIsoDay(period.start)} – {formatIsoDay(period.end)}, the forecast available at{' '}
              {period.cutoff} the day before missed by <strong>{formatMw(summary.mae_mw)}</strong> in a typical hour (
              {formatPct(summary.mae_pct_of_mean)} of average wind output) and ran{' '}
              <strong>
                {formatMw(Math.abs(summary.bias_mw))} {summary.bias_mw >= 0 ? 'high' : 'low'}
              </strong>{' '}
              on average.
            </p>
          )}

          <KpiCards metrics={data.metrics} />

          <div className="grid">
            <ForecastChart points={data.series.points} cutoff={period.cutoff} colors={colors} />
            <DailyErrorChart daily={data.metrics.daily} colors={colors} />
            <ErrorDistributionChart bins={data.metrics.histogram} colors={colors} />
            <HorizonChart buckets={data.horizon.buckets} usedRange={usedHorizon} colors={colors} />
          </div>

          <Method meta={meta} coverage={data.metrics.coverage} />
        </div>
      )}
    </main>
  )
}

function Method({ meta, coverage }: { meta: Meta; coverage: { hours: number; hours_with_forecast: number } }) {
  return (
    <footer className="method">
      <div>
        <h2>How the numbers are made</h2>
        <ol>
          <li>
            Purchases for a delivery day are made the day before, at the auction gate closure (EPEX GB 09:20, N2EX
            09:50 UK time).
          </li>
          <li>
            For every delivery hour we take the newest forecast published at or before that moment. Later forecasts are
            ignored: the buyer could not have seen them.
          </li>
          <li>
            Error = forecast − actual, compared hour by hour. Positive means the forecast promised more wind than came.
          </li>
        </ol>
      </div>
      <dl className="method-facts">
        <dt>Hours compared</dt>
        <dd>
          {coverage.hours_with_forecast.toLocaleString('en-GB')} of {coverage.hours.toLocaleString('en-GB')}
        </dd>
        <dt>Sources</dt>
        <dd>Elexon BMRS · FUELHH (wind actuals), WINDFOR (forecasts)</dd>
        <dt>Data retrieved</dt>
        <dd>{meta.data.fetched_at ? formatDateTime(meta.data.fetched_at) : 'unknown'}</dd>
      </dl>
    </footer>
  )
}
