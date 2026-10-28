import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  hint: ReactNode
  legend?: ReactNode
  children: ReactNode
  className?: string
}

/** A titled card with a one-line "how to read this" hint. */
export function Panel({ title, hint, legend, children, className = '' }: PanelProps) {
  return (
    <section className={`panel ${className}`}>
      <header className="panel-header">
        <div>
          <h2>{title}</h2>
          <p className="panel-hint">{hint}</p>
        </div>
        {legend && <div className="legend">{legend}</div>}
      </header>
      {children}
    </section>
  )
}

export function LegendItem({ color, label, dashed = false }: { color: string; label: string; dashed?: boolean }) {
  return (
    <span className="legend-item">
      <svg width="18" height="8" aria-hidden="true">
        <line x1="0" y1="4" x2="18" y2="4" stroke={color} strokeWidth="2" strokeDasharray={dashed ? '4 3' : undefined} />
      </svg>
      {label}
    </span>
  )
}
