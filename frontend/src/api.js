async function call(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    // FastAPI sends a human-readable message in `detail`; show that when there is one
    const detail = await res.json().then((j) => j.detail).catch(() => null)
    throw new Error(typeof detail === 'string' ? detail : `${method} ${url} failed: ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}

export default {
  meta: () => call('GET', '/api/meta'),
  types: () => call('GET', '/api/types'),
  addType: (name, color) => call('POST', '/api/types', { name, color }),
  updateType: (key, patch) => call('PATCH', `/api/types/${key}`, patch),
  deleteType: (key, moveTo) => call('DELETE', `/api/types/${key}${moveTo ? `?move_to=${encodeURIComponent(moveTo)}` : ''}`),
  reorderTypes: (keys) => call('POST', '/api/types/reorder', { keys }),
  stats: () => call('GET', `/api/stats?tz=${new Date().getTimezoneOffset()}`),
  schedules: () => call('GET', '/api/schedules'),
  addSchedule: (data) => call('POST', '/api/schedules', data),
  updateSchedule: (id, patch) => call('PATCH', `/api/schedules/${id}`, patch),
  deleteSchedule: (id) => call('DELETE', `/api/schedules/${id}`),
  runSchedule: (id) => call('POST', `/api/schedules/${id}/run`),
  lists: () => call('GET', '/api/lists'),
  addList: (name) => call('POST', '/api/lists', { name }),
  renameList: (id, name) => call('PATCH', `/api/lists/${id}`, { name }),
  deleteList: (id) => call('DELETE', `/api/lists/${id}`),
  tasks: (listId) => call('GET', `/api/lists/${listId}/tasks`),
  addTask: (listId, task) => call('POST', `/api/lists/${listId}/tasks`, task),
  updateTask: (id, patch) => call('PATCH', `/api/tasks/${id}`, patch),
  deleteTask: (id) => call('DELETE', `/api/tasks/${id}`),
  addNote: (taskId, body) => call('POST', `/api/tasks/${taskId}/notes`, { body }),
  deleteNote: (id) => call('DELETE', `/api/notes/${id}`),
  addItem: (taskId, text) => call('POST', `/api/tasks/${taskId}/items`, { text }),
  updateItem: (id, patch) => call('PATCH', `/api/items/${id}`, patch),
  deleteItem: (id) => call('DELETE', `/api/items/${id}`),
}
