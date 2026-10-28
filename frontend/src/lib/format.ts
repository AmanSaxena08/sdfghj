// All times are shown in UK local time, the clock the trading desk works to.
const UK = 'Europe/London'

const mwFormat = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })
const dayFormat = new Intl.DateTimeFormat('en-GB', { timeZone: UK, day: 'numeric', month: 'short' })
const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: UK,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export const formatMw = (value: number) => `${mwFormat.format(value)} MW`
export const formatSignedMw = (value: number) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${formatMw(Math.abs(value))}`
export const formatGw = (value: number) => `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)} GW`
export const formatPct = (value: number) => `${value.toFixed(1)}%`
export const formatDay = (value: string | number | Date) => dayFormat.format(new Date(value))
export const formatDateTime = (value: string | number | Date) => dateTimeFormat.format(new Date(value))

/** "2026-01-02" -> "2 Jan" without timezone surprises. */
export const formatIsoDay = (isoDay: string) => formatDay(`${isoDay}T12:00:00Z`)

export const formatHours = (hours: number) => `${Number.isInteger(hours) ? hours : hours.toFixed(1)} h`
