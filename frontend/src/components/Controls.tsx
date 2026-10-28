import { useState } from 'react'
import type { Meta, Period } from '../api/types'

interface ControlsProps {
  meta: Meta
  period: Period
  onChange: (period: Period) => void
}

/** Delivery-day range and decision time (gate closure) pickers. */
export function Controls({ meta, period, onChange }: ControlsProps) {
  const isPreset = meta.cutoff_presets.some((p) => p.time === period.cutoff)
  const [customOpen, setCustomOpen] = useState(!isPreset)
  const isFullPeriod = period.start === meta.delivery_first_day && period.end === meta.delivery_last_day

  const setDay = (field: 'start' | 'end', value: string) => {
    if (!value) return
    const next = { ...period, [field]: value }
    // Keep the range valid: moving one end past the other drags the other along.
    if (next.start > next.end) {
      if (field === 'start') next.end = value
      else next.start = value
    }
    onChange(next)
  }

  return (
    <div className="controls" role="group" aria-label="Analysis settings">
      <fieldset className="control">
        <legend>Delivery days</legend>
        <div className="control-row">
          <input
            type="date"
            aria-label="First delivery day"
            value={period.start}
            min={meta.delivery_first_day}
            max={meta.delivery_last_day}
            onChange={(e) => setDay('start', e.target.value)}
          />
          <span className="control-sep" aria-hidden="true">–</span>
          <input
            type="date"
            aria-label="Last delivery day"
            value={period.end}
            min={meta.delivery_first_day}
            max={meta.delivery_last_day}
            onChange={(e) => setDay('end', e.target.value)}
          />
          <button
            type="button"
            className="chip"
            disabled={isFullPeriod}
            onClick={() => onChange({ ...period, start: meta.delivery_first_day, end: meta.delivery_last_day })}
          >
            Full period
          </button>
        </div>
      </fieldset>

      <fieldset className="control">
        <legend>Decision time, day before delivery (UK)</legend>
        <div className="segmented">
          {meta.cutoff_presets.map((preset) => (
            <button
              key={preset.time}
              type="button"
              aria-pressed={!customOpen && period.cutoff === preset.time}
              onClick={() => {
                setCustomOpen(false)
                onChange({ ...period, cutoff: preset.time })
              }}
            >
              <span className="segment-time">{preset.time}</span>
              <span className="segment-label">{preset.label.split(' ')[0]}</span>
            </button>
          ))}
          <button type="button" aria-pressed={customOpen} onClick={() => setCustomOpen(true)}>
            <span className="segment-time">Custom</span>
            <span className="segment-label">any time</span>
          </button>
          {customOpen && (
            <input
              type="time"
              aria-label="Custom decision time"
              className="segment-input"
              value={period.cutoff}
              onChange={(e) => e.target.value && onChange({ ...period, cutoff: e.target.value })}
            />
          )}
        </div>
      </fieldset>
    </div>
  )
}
