import type { HorizonResponse, Meta, MetricsResponse, Period, SeriesResponse } from './types'

// Same-origin in every environment: Vite proxy (dev), nginx (Docker), rewrites (Vercel).
const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {}

async function getJson<T>(path: string, params: Record<string, string> = {}, signal?: AbortSignal): Promise<T> {
  const query = new URLSearchParams(params).toString()
  const response = await fetch(`${API_BASE}${path}${query ? `?${query}` : ''}`, { signal })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`
    throw new ApiError(detail)
  }
  return response.json() as Promise<T>
}

export const api = {
  meta: (signal?: AbortSignal) => getJson<Meta>('/meta', {}, signal),
  series: (period: Period, signal?: AbortSignal) => getJson<SeriesResponse>('/series', { ...period }, signal),
  metrics: (period: Period, signal?: AbortSignal) => getJson<MetricsResponse>('/metrics', { ...period }, signal),
  horizon: ({ start, end }: Period, signal?: AbortSignal) => getJson<HorizonResponse>('/horizon', { start, end }, signal),
}
