import { ref, watchEffect } from 'vue'

// Light/dark theme, remembered in the browser. Dark (the neon look) is the default.
export function useTheme() {
  const saved = (() => {
    try {
      return localStorage.getItem('theme')
    } catch {
      return null
    }
  })()
  const theme = ref(saved || 'dark')

  watchEffect(() => {
    document.documentElement.dataset.theme = theme.value
    try {
      localStorage.setItem('theme', theme.value)
    } catch {
      /* storage can be unavailable; the choice then only lasts for this page view */
    }
  })

  return theme
}
