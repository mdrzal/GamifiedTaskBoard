// Colours are CSS variables (see style.css) so light and dark themes can each pick readable shades.
export const typeColor = (type) => `var(--type-${type})`

const labels = { todo: 'To Do', in_progress: 'In Progress', done: 'Done' }
export const statusLabel = (s) => labels[s] || s

export const envColor = (e) => `var(--env-${e})`
export const envLabel = (e) => e.toUpperCase()

export const prioColor = (p) => `var(--prio-${p})`

export const when = (ts) => new Date(ts + 'Z').toLocaleString()

// Only http(s) links are clickable, so a stored `javascript:` URL can never run.
export const isUrl = (s) => /^https?:\/\//i.test(s)

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
export const isoDate = iso

// Today's game day. It turns over at 01:00 local time, like levels, daily challenges and scheduled tasks.
export const gameToday = (now = new Date()) => iso(new Date(now.getTime() - 60 * 60 * 1000))

const plusDays = (day, n) => {
  const d = new Date(`${day}T00:00:00`)
  d.setDate(d.getDate() + n)
  return iso(d)
}

// 'overdue' | 'today' | 'soon' (within 2 days) | '' for a YYYY-MM-DD due date.
export function dueState(date) {
  if (!date) return ''
  const today = gameToday()
  if (date < today) return 'overdue'
  if (date === today) return 'today'
  return date <= plusDays(today, 2) ? 'soon' : ''
}

// 'github.com' for 'https://www.github.com/o/r/pull/1'; used as the visible label of a link.
export function linkHost(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return 'link'
  }
}

// Due-date filter: overdue / today / week (next 7 days) / none. Finished tasks are never "due".
export function matchesDue(task, mode) {
  if (!mode) return true
  if (mode === 'none') return !task.due_date
  if (!task.due_date || task.status === 'done') return false
  const today = gameToday()
  if (mode === 'overdue') return task.due_date < today
  if (mode === 'today') return task.due_date === today
  return task.due_date >= today && task.due_date <= plusDays(today, 7)
}

export const shortDate = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
