// Mirrors backend/app/schemas.py. Times are ISO strings in UTC, days are YYYY-MM-DD.

export interface CutoffPreset {
  label: string
  time: string
}

export interface Meta {
  timezone: string
  delivery_first_day: string
  delivery_last_day: string
  decision_first_day: string
  decision_last_day: string
  default_cutoff: string
  cutoff_presets: CutoffPreset[]
  data: { source: string; fetched_at: string | null; actual_rows: number; forecast_rows: number }
}

export interface Period {
  start: string
  end: string
  cutoff: string
}

export interface SeriesPoint {
  time: string
  actual_mw: number
  forecast_mw: number | null
  error_mw: number | null
  publish_time: string | null
  horizon_hours: number | null
  decision_time: string
}

export interface SeriesResponse {
  period: Period
  points: SeriesPoint[]
}

export interface Summary {
  count: number
  mae_mw: number
  rmse_mw: number
  bias_mw: number
  p90_abs_error_mw: number
  max_abs_error_mw: number
  shortfall_p90_mw: number
  mean_actual_mw: number
  mae_pct_of_mean: number
}

export interface HistogramBin {
  from_mw: number
  to_mw: number
  count: number
}

export interface DailyError {
  day: string
  hours: number
  mae_mw: number
  bias_mw: number
  mean_actual_mw: number
  mean_forecast_mw: number
}

export interface MetricsResponse {
  period: Period
  summary: Summary | null
  coverage: { hours: number; hours_with_forecast: number }
  histogram: HistogramBin[]
  daily: DailyError[]
}

export interface HorizonBucket {
  from_hours: number
  to_hours: number
  count: number
  mae_mw: number
  rmse_mw: number
  bias_mw: number
  mae_pct_of_mean: number
}

export interface HorizonResponse {
  start: string
  end: string
  bucket_hours: number
  buckets: HorizonBucket[]
}
