import { reactive, computed, watch } from 'vue'
import { matchesDue } from '../ui'

const EMPTY = { search: '', type: '', priority: '', due: '', dueOn: '', env: '', tag: '', pr: false }

// Search and filters over the tasks of the open list. `filters` is one shared state object that the
// search box, the type chips and the filter bar all read and write.
export function useFilters(tasks, listId) {
  const filters = reactive({ ...EMPTY })

  const allTags = computed(() => [...new Set(tasks.value.flatMap((t) => t.tags))].sort())
  const activeFilters = computed(() => Object.values(filters).filter((v) => (typeof v === 'string' ? v.trim() : v)).length)

  const clearFilters = () => Object.assign(filters, EMPTY)
  watch(listId, () => (filters.tag = '')) // tags belong to a list

  const matchesEnv = (t) =>
    !filters.env || (filters.env === 'none' ? !(t.track_envs && t.env) : t.track_envs && t.env === filters.env)
  const matchesPriority = (t) =>
    !filters.priority || (filters.priority === 'none' ? !t.priority : t.priority === filters.priority)

  const filtered = computed(() => {
    const q = filters.search.trim().toLowerCase()
    return tasks.value.filter(
      (t) =>
        (!filters.type || t.type === filters.type) &&
        (!q || [t.title, t.description, ...t.tags].some((s) => s.toLowerCase().includes(q))) &&
        matchesPriority(t) &&
        matchesDue(t, filters.due) &&
        (!filters.dueOn || t.due_date === filters.dueOn) &&
        matchesEnv(t) &&
        (!filters.tag || t.tags.includes(filters.tag)) &&
        (!filters.pr || t.is_pr),
    )
  })

  return { filters, allTags, activeFilters, clearFilters, filtered }
}
