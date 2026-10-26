<script setup>
import { ref, computed, defineAsyncComponent, onMounted, onUnmounted } from 'vue'
import { useTheme } from './composables/useTheme'
import { useMeta } from './composables/useMeta'
import { useTypes } from './composables/useTypes'
import { useGame } from './composables/useGame'
import { useBoard } from './composables/useBoard'
import { useFilters } from './composables/useFilters'
import TopBar from './components/TopBar.vue'
import Sidebar from './components/Sidebar.vue'
import BoardHeader from './components/BoardHeader.vue'
import FilterBar from './components/FilterBar.vue'
import Board from './components/Board.vue'
import TaskDrawer from './components/TaskDrawer.vue'
import Dialog from './components/Dialog.vue'
import Toasts from './components/Toasts.vue'
import CursorGlow from './components/CursorGlow.vue'

// Settings is rarely opened, so it (and the schedules form) load only when you first visit it.
const SettingsPage = defineAsyncComponent(() => import('./components/SettingsPage.vue'))

const theme = useTheme()
const view = ref('board') // 'board' | 'settings'
const { statuses, envs, priorities, loadMeta } = useMeta()
const { typeList, types, loadTypes } = useTypes()
const game = useGame()
const board = useBoard({ game })
const { stats, goal, sound, toasts, levelUp } = game
const { lists, currentId, current, tasks, selectedId, selected } = board
const { filters, allTags, activeFilters, clearFilters, filtered } = useFilters(tasks, currentId)

const columns = computed(() =>
  statuses.value.map((status) => ({ key: status, tasks: filtered.value.filter((t) => t.status === status) })),
)

function openList(id) {
  view.value = 'board'
  return board.select(id)
}

async function addList(name) {
  view.value = 'board'
  await board.addList(name)
}

// Settings changed the task types: reload them and the tasks (deleting a type moves its tasks).
async function onTypesChanged() {
  await loadTypes()
  if (filters.type && !types.value.includes(filters.type)) filters.type = ''
  await board.reloadTasks()
}

async function refreshTasks() {
  await board.loadLists()
  await board.reloadTasks()
}

const toggleDay = (day) => (filters.dueOn = filters.dueOn === day ? '' : day)
const toggleOverdue = () => (filters.due = filters.due === 'overdue' ? '' : 'overdue')

const onKey = (e) => e.key === 'Escape' && (selectedId.value = null)

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  await loadMeta()
  await loadTypes()
  await board.loadLists()
  await board.select(lists.value[0]?.id ?? null)
  await game.initStats()
})
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="app">
    <CursorGlow />
    <TopBar v-model:search="filters.search" v-model:goal="goal" :stats="stats" :sound="sound" :theme="theme"
      :settings-open="view === 'settings'" @toggle-sound="game.setSoundOn"
      @toggle-settings="view = view === 'settings' ? 'board' : 'settings'"
      @toggle-theme="theme = theme === 'dark' ? 'light' : 'dark'" />

    <div class="body">
      <Sidebar :lists="lists" :current-id="currentId" :tasks="tasks" :due-on="filters.dueOn" :overdue-on="filters.due === 'overdue'"
        @select="openList" @add="addList" @pick-day="toggleDay" @pick-overdue="toggleOverdue" />

      <main v-if="view === 'settings'">
        <SettingsPage :type-list="typeList" :lists="lists" :priorities="priorities" v-model:goal="goal" :sound="sound" :theme="theme"
          :day-start="stats?.day_starts_at || '01:00'" @close="view = 'board'" @changed="onTypesChanged" @tasks-changed="refreshTasks"
          @toggle-sound="game.setSoundOn" @set-theme="theme = $event" />
      </main>
      <main v-else-if="current">
        <BoardHeader :name="current.name" :type-list="typeList" :type-filter="filters.type"
          @set-type="filters.type = $event" @rename="board.renameList" @delete="board.removeList" />
        <FilterBar :filters="filters" :type-list="typeList" :priorities="priorities" :envs="envs" :tags="allTags"
          :active="activeFilters" :shown="filtered.length" :total="tasks.length" @clear="clearFilters" />
        <Board :columns="columns" :type-list="typeList" :envs="envs" :selected-id="selectedId"
          @select="selectedId = $event" @move="board.moveTask" @add="board.addTask" @toggle-env="board.toggleEnv" />
      </main>
      <main v-else class="blank">Create a list to get started.</main>
    </div>

    <TaskDrawer v-if="selected" :task="selected" :type-list="typeList" :statuses="statuses" :envs="envs"
      :priorities="priorities" @close="selectedId = null" @patch="board.patch(selected, $event)"
      @delete="board.removeTask(selected)" @add-note="board.addNote(selected, $event)"
      @delete-note="board.removeNote(selected, $event)" @toggle-env="board.toggleEnv(selected, $event)"
      @add-item="board.addItem(selected, $event)" @toggle-item="board.toggleItem"
      @delete-item="board.removeItem(selected, $event)" />

    <Toasts :toasts="toasts" :level-up="levelUp" @dismiss-level-up="levelUp = null" />
    <Dialog />
  </div>
</template>
