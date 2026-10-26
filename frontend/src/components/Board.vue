<script setup>
import { ref, watch } from 'vue'
import TaskCard from './TaskCard.vue'
import { statusLabel } from '../ui'

const props = defineProps({ columns: Array, typeList: Array, envs: Array, selectedId: Number })
const emit = defineEmits(['select', 'move', 'add', 'toggle-env'])

const vFocus = { mounted: (el) => el.focus() }

const dragId = ref(null)
const dropOn = ref(null)
const addingIn = ref(null) // status of the column whose "new task" form is open
const draftTitle = ref('')
const draftType = ref('')

const typeName = (key) => props.typeList.find((t) => t.key === key)?.name || key

// the type new tasks start with: the first one, until you pick another (or it gets deleted)
watch(
  () => props.typeList,
  (list) => {
    if (!list.some((t) => t.key === draftType.value)) draftType.value = list[0]?.key || ''
  },
  { immediate: true },
)

function startAdd(status) {
  addingIn.value = status
  draftTitle.value = ''
}

function submitAdd() {
  const title = draftTitle.value.trim()
  const status = addingIn.value
  if (!title) return (addingIn.value = null)
  draftTitle.value = ''
  addingIn.value = null
  emit('add', { title, type: draftType.value, status })
}

function onDragStart(event, task) {
  dragId.value = task.id
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', String(task.id))
}

function onDrop(status) {
  const id = dragId.value
  dragId.value = dropOn.value = null
  if (id !== null) emit('move', id, status)
}
</script>

<template>
  <div class="board">
    <section v-for="col in columns" :key="col.key" class="column" :class="[col.key, { over: dropOn === col.key }]"
      @dragover.prevent="dropOn = col.key" @dragleave.self="dropOn = null" @drop.prevent="onDrop(col.key)">
      <div class="col-head">
        <span class="col-title">{{ statusLabel(col.key) }}</span>
        <span class="badge">{{ col.tasks.length }}</span>
        <button class="icon-btn" title="Add task" @click="startAdd(col.key)">+</button>
      </div>

      <form v-if="addingIn === col.key" class="add-card" @submit.prevent="submitAdd">
        <input v-model="draftTitle" v-focus placeholder="Task title, Enter to add" @keydown.esc="addingIn = null" />
        <div class="add-row">
          <select v-model="draftType">
            <option v-for="t in typeList" :key="t.key" :value="t.key">{{ t.name }}</option>
          </select>
          <button class="btn primary">Add</button>
          <button type="button" class="btn" @click="addingIn = null">Cancel</button>
        </div>
      </form>

      <TaskCard v-for="(t, i) in col.tasks" :key="t.id" :task="t" :index="i" :type-label="typeName(t.type)" :envs="envs"
        :selected="t.id === selectedId" :dragging="t.id === dragId"
        @select="emit('select', t.id)" @toggle-env="emit('toggle-env', t, $event)"
        @dragstart="onDragStart($event, t)" @dragend="dragId = dropOn = null" />

      <p v-if="!col.tasks.length && addingIn !== col.key" class="empty">Drop tasks here</p>
    </section>
  </div>
</template>
