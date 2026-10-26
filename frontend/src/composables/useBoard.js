import { ref, computed, nextTick } from 'vue'
import api from '../api'
import { confetti, envBurst, playSound } from '../effects'
import { askConfirm, askText } from './useDialog'

// Lists, the tasks of the open list, the selected task, and every action that changes them.
// `game` (from useGame) is told about changes so it can hand out or take back XP.
export function useBoard({ game }) {
  const lists = ref([])
  const currentId = ref(null)
  const tasks = ref([])
  const selectedId = ref(null)

  const current = computed(() => lists.value.find((l) => l.id === currentId.value))
  const selected = computed(() => tasks.value.find((t) => t.id === selectedId.value))

  // Run a user action; if the server refuses, say why instead of silently doing nothing.
  async function guard(action) {
    try {
      return await action()
    } catch (e) {
      game.toast(e.message, 'error')
    }
  }

  // ---- lists ----
  async function loadLists() {
    lists.value = await api.lists()
  }

  async function select(id) {
    currentId.value = id
    selectedId.value = null
    tasks.value = id ? await api.tasks(id) : []
  }

  async function reloadTasks() {
    if (currentId.value) tasks.value = await api.tasks(currentId.value)
  }

  const addList = (name) =>
    guard(async () => {
      const list = await api.addList(name)
      await loadLists()
      await select(list.id)
    })

  async function renameList() {
    const list = current.value
    const name = await askText({ title: 'Rename list', value: list.name, placeholder: 'List name', confirmLabel: 'Rename' })
    if (!name || name === list.name) return
    await guard(async () => {
      await api.renameList(list.id, name)
      await loadLists()
    })
  }

  async function removeList() {
    const list = current.value
    const ok = await askConfirm({
      title: `Delete "${list.name}"?`,
      message: `This permanently deletes the list and its ${list.total} task${list.total === 1 ? '' : 's'}, including their notes and checklists. This can't be undone.`,
      confirmLabel: 'Delete list',
    })
    if (!ok) return
    await guard(async () => {
      await api.deleteList(list.id)
      await loadLists()
      await select(lists.value[0]?.id ?? null)
    })
  }

  // ---- tasks ----

  // Where a task's effects should appear: inside the side panel while it is open for that task (the
  // board behind it is blurred and covered), otherwise on the card itself.
  function anchorFor(task, part = 'card') {
    if (selectedId.value === task.id) {
      const panel = document.querySelector('.drawer')
      if (panel) {
        const spot = { env: '.d-envs', state: '.d-fields' }[part] || '.d-head'
        return panel.querySelector(spot) || panel
      }
    }
    return document.querySelector(`[data-id="${task.id}"]`)
  }

  async function patch(task, change) {
    const prev = game.stats.value
    const statusChanged = 'status' in change && change.status !== task.status
    const envChanged = 'env' in change && change.env !== task.env
    const toDone = statusChanged && change.status === 'done'
    const toEnv = envChanged ? change.env : ''

    Object.assign(task, change) // optimistic
    await nextTick()
    if (toDone) {
      confetti(anchorFor(task, 'state'))
      playSound('done')
    }
    if (toEnv) {
      envBurst(toEnv, anchorFor(task, 'env'))
      playSound(toEnv)
    }

    Object.assign(task, await api.updateTask(task.id, change))
    loadLists()
    // the +/- XP rises from the control that was used; it also runs when XP was taken back
    if (statusChanged || envChanged) await game.reward(prev, anchorFor(task, envChanged ? 'env' : 'state'))
  }

  async function addTask({ title, type, status }) {
    const task = await api.addTask(currentId.value, { title, type })
    tasks.value.unshift(task)
    if (status !== 'todo') await patch(task, { status })
    loadLists()
  }

  const moveTask = (id, status) => {
    const task = tasks.value.find((t) => t.id === id)
    if (task && task.status !== status) patch(task, { status })
  }

  async function removeTask(task) {
    const ok = await askConfirm({
      title: `Delete "${task.title}"?`,
      message: 'The task, its notes and its checklist are removed for good.',
      confirmLabel: 'Delete task',
    })
    if (!ok) return
    await guard(async () => {
      await api.deleteTask(task.id)
      tasks.value = tasks.value.filter((t) => t.id !== task.id)
      selectedId.value = null
      loadLists()
    })
  }

  // Clicking the environment a task is already in clears it. Reaching PRD means the work is finished,
  // so the task moves to Done in the same step (the server applies the same rule).
  function toggleEnv(task, env) {
    const next = task.env === env ? '' : env
    patch(task, next === 'prd' && task.status !== 'done' ? { env: next, status: 'done' } : { env: next })
  }

  // ---- notes and checklist ----
  async function addNote(task, body) {
    const prev = game.stats.value
    task.notes.push(await api.addNote(task.id, body))
    game.reward(prev, anchorFor(task)) // a note can complete a "leave notes" challenge
  }

  async function removeNote(task, note) {
    const prev = game.stats.value
    await api.deleteNote(note.id)
    task.notes = task.notes.filter((n) => n.id !== note.id)
    game.reward(prev, anchorFor(task))
  }

  async function addItem(task, text) {
    task.items.push(await api.addItem(task.id, text))
  }

  async function toggleItem(item) {
    item.done = !item.done
    Object.assign(item, await api.updateItem(item.id, { done: item.done }))
  }

  async function removeItem(task, item) {
    await api.deleteItem(item.id)
    task.items = task.items.filter((i) => i.id !== item.id)
  }

  return {
    lists, currentId, current, tasks, selectedId, selected,
    loadLists, select, reloadTasks, addList, renameList, removeList,
    patch, addTask, moveTask, removeTask, toggleEnv,
    addNote, removeNote, addItem, toggleItem, removeItem,
  }
}
