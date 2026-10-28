import type { MetricsResponse } from '../api/types'
import { formatMw, formatPct, formatSignedMw } from '../lib/format'

/** The headline accuracy numbers, each phrased as the question a buyer would ask. */
export function KpiCards({ metrics }: { metrics: MetricsResponse }) {
  const s = metrics.summary
  if (!s) return <p className="empty">No forecasts were available for this selection.</p>

  const biasDirection = Math.abs(s.bias_mw) < 50 ? 'no consistent lean' : s.bias_mw > 0 ? 'forecast runs high' : 'forecast runs low'

  const cards = [
    {
      label: 'Typical miss',
      value: formatMw(s.mae_mw),
      detail: `${formatPct(s.mae_pct_of_mean)} of average output · MAE`,
    },
    {
      label: 'Systematic lean',
      value: formatSignedMw(s.bias_mw),
      detail: `${biasDirection} · mean error`,
      tone: s.bias_mw > 0 ? 'over' : 'under',
    },
    {
      label: 'Wind shortfall to plan for',
      value: formatMw(s.shortfall_p90_mw),
      detail: 'in 9 of 10 hours, wind fell short of the forecast by no more than this',
    },
    {
      label: 'Large misses',
      value: formatMw(s.rmse_mw),
      detail: `RMSE · worst hour ${formatMw(s.max_abs_error_mw)}`,
    },
  ]

  return (
    <div className="kpis">
      {cards.map((card) => (
        <article key={card.label} className="kpi">
          <h3>{card.label}</h3>
          <p className={`kpi-value ${card.tone ?? ''}`}>{card.value}</p>
          <p className="kpi-detail">{card.detail}</p>
        </article>
      ))}
    </div>
  )
}
