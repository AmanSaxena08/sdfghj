import { useEffect, useState } from 'react'

// SVG chart attributes can't use CSS variables, so read the theme tokens from :root
// and re-read them whenever the theme toggle changes <html data-theme>.
const TOKENS = ['--ink', '--muted', '--line', '--accent', '--over', '--under', '--surface'] as const

export type ChartColors = Record<'ink' | 'muted' | 'line' | 'accent' | 'over' | 'under' | 'surface', string>

function readColors(): ChartColors {
  const style = getComputedStyle(document.documentElement)
  const entries = TOKENS.map((token) => [token.slice(2), style.getPropertyValue(token).trim()])
  return Object.fromEntries(entries) as ChartColors
}

export function useChartColors(): ChartColors {
  const [colors, setColors] = useState(readColors)

  useEffect(() => {
    const observer = new MutationObserver(() => setColors(readColors()))
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [])

  return colors
}
