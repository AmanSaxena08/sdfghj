import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { HorizonResponse, Meta, MetricsResponse, Period, SeriesResponse } from '../api/types'

export function useMeta() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    api.meta(controller.signal).then(setMeta).catch((e: Error) => {
      if (!controller.signal.aborted) setError(e.message)
    })
    return () => controller.abort()
  }, [])

  return { meta, error }
}

export interface DashboardData {
  series: SeriesResponse
  metrics: MetricsResponse
  horizon: HorizonResponse
}

interface Result {
  period: Period
  data?: DashboardData
  error?: string
}

/**
 * Loads everything the dashboard shows for a period and cancels stale requests when it changes.
 * `period` should be React state (or memoised) so a new object means a genuinely new selection.
 * The previous data stays on screen while the next selection loads.
 */
export function useDashboardData(period: Period) {
  const [latest, setLatest] = useState<Result | null>(null)
  const [data, setData] = useState<DashboardData | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      api.series(period, controller.signal),
      api.metrics(period, controller.signal),
      api.horizon(period, controller.signal),
    ])
      .then(([series, metrics, horizon]) => {
        const next = { series, metrics, horizon }
        setData(next)
        setLatest({ period, data: next })
      })
      .catch((e: Error) => {
        if (!controller.signal.aborted) setLatest({ period, error: e.message })
      })
    return () => controller.abort()
  }, [period])

  const settled = latest?.period === period
  return {
    data,
    loading: !settled,
    error: settled ? (latest?.error ?? null) : null,
  }
}
