<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { askConfirm } from '../composables/useDialog'

const props = defineProps({ lists: Array, typeList: Array, priorities: Array })
const emit = defineEmits(['tasks-changed'])

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const schedules = ref([])
const error = ref('')
const editingId = ref(null)
const blank = () => ({
  name: '', title: '', description: '', list_id: props.lists[0]?.id ?? null, type: '', priority: '',
  repeat: 'weekly', weekdays: [4], day_of_month: 1, on_date: '',
})
const form = reactive(blank())

const load = async () => (schedules.value = await api.schedules())
onMounted(load)

// Run an API change, show the server's message if it refuses, then refresh.
async function run(change) {
  error.value = ''
  try {
    await change()
    await load()
    emit('tasks-changed') // saving can create today's task straight away
  } catch (e) {
    error.value = e.message
  }
}

function reset() {
  editingId.value = null
  Object.assign(form, blank())
}

function toggleDay(index) {
  const at = form.weekdays.indexOf(index)
  if (at >= 0) form.weekdays.splice(at, 1)
  else form.weekdays.push(index)
}

function save() {
  const payload = {
    name: form.name.trim(),
    title: form.title.trim(),
    description: form.description,
    list_id: form.list_id ?? props.lists[0]?.id,
    type: form.type || null,
    priority: form.priority,
    repeat: form.repeat,
    weekdays: form.repeat === 'weekly' ? form.weekdays : [],
    day_of_month: form.day_of_month,
    on_date: form.repeat === 'once' ? form.on_date : '',
  }
  run(async () => {
    if (editingId.value) await api.updateSchedule(editingId.value, payload)
    else await api.addSchedule(payload)
    reset()
  })
}

function edit(s) {
  editingId.value = s.id
  Object.assign(form, { ...s, type: s.type, weekdays: [...s.weekdays] })
  window.scrollTo?.({ top: 0 })
}

async function remove(s) {
  const ok = await askConfirm({
    title: `Delete "${s.name || s.title}"?`,
    message: 'No more tasks will be created from it. Tasks it already made stay on the board.',
    confirmLabel: 'Delete schedule',
  })
  if (ok) run(() => api.deleteSchedule(s.id))
}

const toggle = (s) => run(() => api.updateSchedule(s.id, { enabled: !s.enabled }))
const runNow = (s) => run(() => api.runSchedule(s.id))

const ordinal = (n) => {
  const suffix = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (suffix[(v - 20) % 10] || suffix[v] || suffix[0])
}
const pretty = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })

function describe(s) {
  if (s.repeat === 'daily') return 'Every day'
  if (s.repeat === 'weekly') return `Every ${s.weekdays.map((d) => DAYS[d]).join(', ')}`
  if (s.repeat === 'monthly') return `Monthly on the ${ordinal(s.day_of_month)}`
  return `Once on ${s.on_date ? pretty(s.on_date) : '?'}`
}

const nextLabel = (s) => (!s.enabled ? 'Paused' : s.next_run ? `Next: ${pretty(s.next_run)}` : 'Finished')
</script>

<template>
  <section>
    <h2>Scheduled tasks</h2>
    <p class="hint">
      Create a task automatically on chosen days, such as a weekly time report spreadsheet. It appears in
      To Do on that day with the day as its due date. Titles can use
      <code>{date}</code> <code>{weekday}</code> <code>{month}</code> <code>{year}</code> <code>{week}</code>.
      A day starts at 01:00.
    </p>
    <p v-if="error" class="error">{{ error }}</p>

    <ul v-if="schedules.length" class="sched-list">
      <li v-for="s in schedules" :key="s.id" :class="{ paused: !s.enabled }">
        <div class="s-main">
          <b>{{ s.name || s.title }}</b>
          <span v-if="s.name" class="s-meta">Creates: {{ s.title }}</span>
          <span class="s-meta">{{ describe(s) }} · {{ s.list_name }} · <em>{{ nextLabel(s) }}</em></span>
        </div>
        <div class="s-actions">
          <button class="btn" title="Create the task now" @click="runNow(s)">Run now</button>
          <button class="btn" @click="toggle(s)">{{ s.enabled ? 'Pause' : 'Resume' }}</button>
          <button class="btn" @click="edit(s)">Edit</button>
          <button class="btn danger" @click="remove(s)">Delete</button>
        </div>
      </li>
    </ul>
    <p v-else class="hint none">Nothing scheduled yet.</p>

    <form class="s-form" @submit.prevent="save">
      <div class="s-head">
        <strong>{{ editingId ? 'Edit schedule' : 'New schedule' }}</strong>
      </div>

      <input v-model="form.name" class="wide" maxlength="80" placeholder="Schedule name (optional), e.g. Monday planning" />
      <input v-model="form.title" class="wide" maxlength="120" placeholder="Task title, e.g. Time report – week {week}" />
      <textarea v-model="form.description" rows="2" placeholder="Description (optional)"></textarea>

      <div class="row">
        <label>List
          <select v-model="form.list_id">
            <option v-for="l in lists" :key="l.id" :value="l.id">{{ l.name }}</option>
          </select>
        </label>
        <label>Type
          <select v-model="form.type">
            <option value="">default</option>
            <option v-for="t in typeList" :key="t.key" :value="t.key">{{ t.name }}</option>
          </select>
        </label>
        <label>Priority
          <select v-model="form.priority">
            <option value="">none</option>
            <option v-for="p in priorities" :key="p" :value="p">{{ p }}</option>
          </select>
        </label>
      </div>

      <div class="row">
        <span class="seg">
          <button v-for="r in ['once', 'daily', 'weekly', 'monthly']" :key="r" type="button" :class="{ on: form.repeat === r }" @click="form.repeat = r">{{ r }}</button>
        </span>
        <span v-if="form.repeat === 'weekly'" class="days">
          <button v-for="(d, i) in DAYS" :key="d" type="button" :class="{ on: form.weekdays.includes(i) }" @click="toggleDay(i)">{{ d }}</button>
        </span>
        <label v-if="form.repeat === 'monthly'">Day of month
          <input v-model.number="form.day_of_month" type="number" min="1" max="31" class="num" />
        </label>
        <label v-if="form.repeat === 'once'">Date
          <input v-model="form.on_date" type="date" />
        </label>
      </div>

      <div class="s-buttons">
        <button class="btn primary" :disabled="!form.title.trim() || !lists.length">{{ editingId ? 'Save changes' : 'Add schedule' }}</button>
        <button v-if="editingId" type="button" class="btn" @click="reset">Cancel</button>
      </div>
    </form>
  </section>
</template>

<style scoped>
section { margin-bottom: 20px; padding: 14px 18px; background: var(--glass); border: 1px solid var(--glass-line); border-radius: 3px; }
h2 { margin: 0 0 8px; font-family: var(--mono); font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent2); }
h2::before { content: '// '; opacity: 0.6; }
.hint { margin: 0 0 12px; font-size: 12.5px; line-height: 1.5; color: var(--muted); }
.hint.none { font-family: var(--mono); font-size: 12px; color: var(--faint); }
code { padding: 0 4px; border: 1px solid var(--line); border-radius: 2px; font-family: var(--mono); font-size: 11px; color: var(--accent); }
.error { margin: 0 0 10px; padding: 6px 10px; border: 1px solid var(--danger); border-radius: 2px; background: var(--danger-bg); color: var(--danger); font-size: 13px; }
.sched-list { list-style: none; margin: 0 0 14px; padding: 0; }
.sched-list li { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; padding: 8px 10px; border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 2px; background: color-mix(in srgb, var(--panel) 55%, transparent); }
.sched-list li.paused { opacity: 0.6; border-left-color: var(--faint); }
.s-main { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.s-meta { font-family: var(--mono); font-size: 11px; color: var(--muted); }
.s-meta em { font-style: normal; color: var(--accent); }
.s-actions { display: flex; gap: 6px; }
.s-actions .btn { padding: 3px 9px; font-size: 11px; }
.s-form { display: flex; flex-direction: column; gap: 10px; padding-top: 12px; border-top: 1px solid var(--line); }
.s-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: var(--mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
.wide { width: 100%; }
textarea { width: 100%; resize: vertical; }
.row { display: flex; align-items: flex-end; gap: 14px; flex-wrap: wrap; }
label { display: flex; flex-direction: column; gap: 4px; font-family: var(--mono); font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
label select, label input { font-size: 12px; }
.num { width: 70px; }
.seg, .days { display: inline-flex; }
.seg button, .days button { padding: 4px 12px; border: 1px solid var(--field-line); background: transparent; cursor: pointer; font-family: var(--mono); font-size: 12px; text-transform: capitalize; }
.seg button + button, .days button + button { border-left: 0; }
.seg button.on, .days button.on { background: var(--accent); border-color: var(--accent); color: var(--on-accent); font-weight: 700; }
.s-buttons { display: flex; gap: 8px; }
.s-buttons .btn:disabled { opacity: 0.4; cursor: default; }
</style>
