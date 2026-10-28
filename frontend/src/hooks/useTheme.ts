import { useState } from 'react'

// Light is the default; the choice is remembered per browser. index.html applies the stored
// theme before the first paint, so the page never flashes the wrong colours.
export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'theme'

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState(currentTheme)

  const toggle = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Storage can be blocked (private mode); the toggle still works for this visit.
    }
    setTheme(next)
  }

  return [theme, toggle]
}
