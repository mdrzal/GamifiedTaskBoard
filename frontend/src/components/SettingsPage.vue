<script setup>
import { ref } from 'vue'
import api from '../api'
import SchedulesSection from './SchedulesSection.vue'
import { askConfirm } from '../composables/useDialog'

const props = defineProps({ typeList: Array, lists: Array, priorities: Array, goal: Number, sound: Boolean, theme: String, dayStart: String })
const emit = defineEmits(['close', 'changed', 'tasks-changed', 'update:goal', 'toggle-sound', 'set-theme'])

const error = ref('')
const newName = ref('')
const newColor = ref('#00f0ff')
const removing = ref(null) // key of the type whose tasks we are about to move
const moveTo = ref('')

// Run an API change, show any server message (like "name already exists"), then tell the app to reload.
async function run(change) {
  error.value = ''
  try {
    await change()
    emit('changed')
  } catch (e) {
    error.value = e.message
    emit('changed') // re-sync the list so inputs don't keep a rejected value
  }
}

function add() {
  const name = newName.value.trim()
  if (!name) return
  run(async () => {
    await api.addType(name, newColor.value)
    newName.value = ''
  })
}

function rename(type, input) {
  const name = input.value.trim()
  if (!name) return (input.value = type.name)
  if (name !== type.name) run(() => api.updateType(type.key, { name }))
}

const recolor = (type, color) => run(() => api.updateType(type.key, { color }))

function shift(index, step) {
  const keys = props.typeList.map((t) => t.key)
  const to = index + step
  if (to < 0 || to >= keys.length) return
  ;[keys[index], keys[to]] = [keys[to], keys[index]]
  run(() => api.reorderTypes(keys))
}

async function askDelete(type) {
  error.value = ''
  if (!type.count) {
    const ok = await askConfirm({ title: `Delete the "${type.name}" type?`, message: 'No task uses it.', confirmLabel: 'Delete type' })
    if (ok) run(() => api.deleteType(type.key))
    return
  }
  removing.value = type.key
  moveTo.value = props.typeList.find((t) => t.key !== type.key)?.key || ''
}

const confirmDelete = (type) =>
  run(async () => {
    await api.deleteType(type.key, moveTo.value)
    removing.value = null
  })
</script>

<template>
  <div class="settings">
    <div class="s-head">
      <h1>Settings</h1>
      <button class="btn" @click="emit('close')">← Back to board</button>
    </div>

    <section>
      <h2>Task types</h2>
      <p class="hint">
        Rename them, pick a colour, put them in the order you like. The colour is used on cards and filters
        (light mode shows a slightly darker shade so it stays readable).
      </p>
      <p v-if="error" class="error">{{ error }}</p>

      <ul class="types">
        <li v-for="(t, i) in typeList" :key="t.key" :style="{ '--c': t.color }">
          <div class="row">
            <span class="arrows">
              <button title="Move up" :disabled="i === 0" @click="shift(i, -1)">▲</button>
              <button title="Move down" :disabled="i === typeList.length - 1" @click="shift(i, 1)">▼</button>
            </span>
            <input type="color" class="swatch" :value="t.color" title="Colour" @change="recolor(t, $event.target.value)" />
            <input class="name" :value="t.name" maxlength="30" @blur="rename(t, $event.target)" @keydown.enter="$event.target.blur()" />
            <span class="used">{{ t.count }} {{ t.count === 1 ? 'task' : 'tasks' }}</span>
            <button class="btn danger" :disabled="typeList.length === 1" @click="askDelete(t)">Delete</button>
          </div>
          <div v-if="removing === t.key" class="confirm">
            <span>{{ t.count }} {{ t.count === 1 ? 'task uses' : 'tasks use' }} this type. Move them to</span>
            <select v-model="moveTo">
              <option v-for="o in typeList.filter((x) => x.key !== t.key)" :key="o.key" :value="o.key">{{ o.name }}</option>
            </select>
            <button class="btn danger" @click="confirmDelete(t)">Move &amp; delete</button>
            <button class="btn" @click="removing = null">Cancel</button>
          </div>
        </li>
      </ul>

      <form class="add" @submit.prevent="add">
        <input type="color" class="swatch" v-model="newColor" title="Colour" />
        <input v-model="newName" maxlength="30" placeholder="New type name…" />
        <button class="btn primary" :disabled="!newName.trim()">Add type</button>
      </form>
    </section>

    <SchedulesSection :lists="lists" :type-list="typeList" :priorities="priorities" @tasks-changed="emit('tasks-changed')" />

    <section>
      <h2>Game</h2>
      <div class="line">
        <span>Daily goal <small>tasks to resolve each day</small></span>
        <span class="stepper">
          <button :disabled="goal <= 1" @click="emit('update:goal', goal - 1)">−</button>
          <b>{{ goal }}</b>
          <button :disabled="goal >= 20" @click="emit('update:goal', goal + 1)">+</button>
        </span>
      </div>
      <label class="line">
        <span>Sound effects <small>short blips when you earn XP</small></span>
        <input type="checkbox" :checked="sound" @change="emit('toggle-sound', $event.target.checked)" />
      </label>
      <p class="hint">
        A game day starts at {{ dayStart }}, so working past midnight still counts for the same day. Your level,
        silly level name and the three random daily challenges reset then. Streaks and totals carry on.
      </p>
    </section>

    <section>
      <h2>Appearance</h2>
      <div class="line">
        <span>Theme</span>
        <span class="seg">
          <button :class="{ on: theme === 'dark' }" @click="emit('set-theme', 'dark')">☾ Dark</button>
          <button :class="{ on: theme === 'light' }" @click="emit('set-theme', 'light')">☀ Light</button>
        </span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.settings { max-width: 760px; padding-bottom: 40px; overflow-y: auto; }
.s-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.s-head h1 { margin: 0; font-family: var(--mono); font-size: 22px; letter-spacing: 0.12em; text-transform: uppercase; }
.s-head h1::before { content: '> '; color: var(--accent2); }
section { margin-bottom: 20px; padding: 14px 18px; background: var(--glass); border: 1px solid var(--glass-line); border-radius: 3px; }
h2 { margin: 0 0 8px; font-family: var(--mono); font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent2); }
h2::before { content: '// '; opacity: 0.6; }
.hint { margin: 0 0 12px; font-size: 12.5px; line-height: 1.5; color: var(--muted); }
.error { margin: 0 0 10px; padding: 6px 10px; border: 1px solid var(--danger); border-radius: 2px; background: var(--danger-bg); color: var(--danger); font-size: 13px; }
.types { list-style: none; margin: 0 0 12px; padding: 0; }
.types li { margin-bottom: 6px; border: 1px solid var(--line); border-left: 4px solid var(--c); border-radius: 2px; background: color-mix(in srgb, var(--panel) 55%, transparent); }
.row { display: flex; align-items: center; gap: 10px; padding: 6px 10px; }
.arrows { display: inline-flex; flex-direction: column; gap: 1px; }
.arrows button { width: 20px; height: 13px; padding: 0; border: 0; background: transparent; color: var(--muted); font-size: 8px; line-height: 1; cursor: pointer; }
.arrows button:hover:not(:disabled) { color: var(--accent); }
.arrows button:disabled { opacity: 0.25; cursor: default; }
.swatch { width: 34px; height: 28px; padding: 1px; border: 1px solid var(--field-line); border-radius: 2px; background: transparent; cursor: pointer; }
.name { flex: 1; min-width: 0; }
.used { min-width: 70px; text-align: right; font-family: var(--mono); font-size: 11px; color: var(--muted); }
.confirm { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 8px 10px; border-top: 1px dashed var(--line); font-size: 12.5px; background: var(--danger-bg); }
.add { display: flex; align-items: center; gap: 10px; }
.add input:not(.swatch) { flex: 1; }
.line { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-top: 1px solid var(--line); font-family: var(--mono); font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; }
label.line { cursor: pointer; }
.line small { margin-left: 8px; text-transform: none; letter-spacing: 0; color: var(--faint); }
.stepper { display: inline-flex; align-items: center; gap: 10px; }
.stepper button { width: 24px; height: 24px; padding: 0; border: 1px solid var(--field-line); border-radius: 2px; background: transparent; cursor: pointer; }
.stepper button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.stepper button:disabled { opacity: 0.35; cursor: default; }
.seg { display: inline-flex; }
.seg button { padding: 4px 14px; border: 1px solid var(--field-line); background: transparent; cursor: pointer; font-family: var(--mono); font-size: 12px; }
.seg button + button { border-left: 0; }
.seg button.on { background: var(--accent); border-color: var(--accent); color: var(--on-accent); font-weight: 700; }
button:disabled { cursor: default; }
</style>
