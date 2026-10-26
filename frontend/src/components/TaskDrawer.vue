<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import EnvDots from './EnvDots.vue'
import { askConfirm } from '../composables/useDialog'
import { statusLabel, typeColor, when, isUrl } from '../ui'

const props = defineProps({ task: Object, typeList: Array, statuses: Array, envs: Array, priorities: Array })
const emit = defineEmits(['close', 'patch', 'delete', 'add-note', 'delete-note', 'toggle-env', 'add-item', 'toggle-item', 'delete-item'])

const title = ref(props.task.title)
const description = ref(props.task.description)
const link = ref(props.task.link)
const showLink = ref(!!props.task.link) // the Link field is opt-in, like environments
const linkInput = ref(null)
const tagDraft = ref('')
const itemDraft = ref('')
const noteDraft = ref('')

watch(() => props.task.id, () => {
  title.value = props.task.title
  description.value = props.task.description
  link.value = props.task.link
  showLink.value = !!props.task.link
  tagDraft.value = itemDraft.value = noteDraft.value = ''
})

const typeName = computed(() => props.typeList.find((t) => t.key === props.task.type)?.name || props.task.type)
const checked = computed(() => props.task.items.filter((i) => i.done).length)

function saveTitle() {
  const t = title.value.trim()
  if (!t) title.value = props.task.title
  else if (t !== props.task.title) emit('patch', { title: t })
}

// Text fields save when you leave them, and only if they changed.
const saveText = (field, value) => value.trim() !== props.task[field] && emit('patch', { [field]: value.trim() })

async function toggleLink(e) {
  const box = e.target
  if (box.checked) {
    showLink.value = true
    nextTick(() => linkInput.value?.focus())
    return
  }
  if (props.task.link) {
    box.checked = true // stays ticked until the removal is confirmed
    const ok = await askConfirm({ title: 'Remove the link?', message: 'It will be cleared from this task.', confirmLabel: 'Remove link' })
    if (!ok) return
    box.checked = false
  }
  showLink.value = false
  link.value = ''
  if (props.task.link) emit('patch', { link: '' })
}

function addTags() {
  const added = tagDraft.value.split(',').map((t) => t.trim()).filter(Boolean)
  tagDraft.value = ''
  if (added.length) emit('patch', { tags: [...props.task.tags, ...added] })
}

const removeTag = (tag) => emit('patch', { tags: props.task.tags.filter((t) => t !== tag) })

function addItem() {
  const text = itemDraft.value.trim()
  if (!text) return
  itemDraft.value = ''
  emit('add-item', text)
}

function submitNote() {
  const body = noteDraft.value.trim()
  if (!body) return
  noteDraft.value = ''
  emit('add-note', body)
}
</script>

<template>
  <div class="scrim" @click="emit('close')"></div>
  <aside class="drawer" :style="{ '--c': typeColor(task.type) }">
    <div class="d-head">
      <span class="d-type"><i></i>{{ typeName }} #{{ task.id }}</span>
      <button class="icon-btn" title="Close (Esc)" @click="emit('close')">✕</button>
    </div>

    <input v-model="title" class="d-title" @blur="saveTitle" @keydown.enter="$event.target.blur()" />

    <div class="d-fields">
      <label>State
        <select :value="task.status" @change="emit('patch', { status: $event.target.value })">
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
        </select>
      </label>
      <label>Type
        <select :value="task.type" @change="emit('patch', { type: $event.target.value })">
          <option v-for="t in typeList" :key="t.key" :value="t.key">{{ t.name }}</option>
        </select>
      </label>
    </div>
    <div class="d-fields">
      <label>Priority
        <select :value="task.priority" @change="emit('patch', { priority: $event.target.value })">
          <option value="">none</option>
          <option v-for="p in priorities" :key="p">{{ p }}</option>
        </select>
      </label>
      <label>Due date
        <input type="date" :value="task.due_date" @change="emit('patch', { due_date: $event.target.value })" />
      </label>
    </div>

    <div class="d-envs">
      <label class="track">
        <input type="checkbox" :checked="task.track_envs" @change="emit('patch', { track_envs: $event.target.checked })" />
        Track environments
      </label>
      <EnvDots v-if="task.track_envs" :envs="envs" :current="task.env" labels @toggle="emit('toggle-env', $event)" />
    </div>

    <div class="field">
      <span class="lbl">Tags</span>
      <div class="tags">
        <button v-for="tag in task.tags" :key="tag" class="chip-tag" title="Remove tag" @click="removeTag(tag)">#{{ tag }} ✕</button>
        <input v-model="tagDraft" class="tag-in" placeholder="add tag…" @keydown.enter.prevent="addTags" @keydown.,.prevent="addTags" @blur="addTags" />
      </div>
    </div>

    <div class="d-envs">
      <label class="track">
        <input type="checkbox" :checked="task.is_pr" @change="emit('patch', { is_pr: $event.target.checked })" />
        Is a pull request (PR)
      </label>
    </div>

    <div class="d-envs d-link">
      <label class="track">
        <input type="checkbox" :checked="showLink" @change="toggleLink" />
        Link
      </label>
      <div v-if="showLink" class="link-row">
        <input ref="linkInput" v-model="link" placeholder="PR, issue or doc URL — https://…" @blur="saveText('link', link)" @keydown.enter="$event.target.blur()" />
        <a v-if="isUrl(task.link)" class="btn open" :href="task.link" target="_blank" rel="noopener noreferrer">Open page ↗</a>
      </div>
    </div>

    <h3>Description</h3>
    <textarea v-model="description" class="desc" rows="4" placeholder="What needs doing, and why? (optional)" @blur="saveText('description', description)"></textarea>

    <h3>Checklist <span class="n">{{ task.items.length ? `${checked}/${task.items.length}` : 0 }}</span></h3>
    <div v-if="task.items.length" class="progress"><i :style="{ width: (checked / task.items.length) * 100 + '%' }"></i></div>
    <ul class="items">
      <li v-for="i in task.items" :key="i.id" :class="{ done: i.done }">
        <input type="checkbox" :checked="i.done" @change="emit('toggle-item', i)" />
        <span>{{ i.text }}</span>
        <button class="icon-btn" title="Remove item" @click="emit('delete-item', i)">✕</button>
      </li>
    </ul>
    <form class="add-item" @submit.prevent="addItem">
      <input v-model="itemDraft" placeholder="Add a subtask…" />
    </form>

    <h3>Notes <span class="n">{{ task.notes.length }}</span></h3>
    <div class="thread">
      <p v-if="!task.notes.length" class="none">No notes yet. Add progress updates below.</p>
      <div v-for="n in task.notes" :key="n.id" class="note">
        <div class="avatar">N</div>
        <div class="bubble">
          <div class="meta">
            <span>{{ when(n.created_at) }}</span>
            <button class="icon-btn" title="Delete note" @click="emit('delete-note', n)">✕</button>
          </div>
          <p>{{ n.body }}</p>
        </div>
      </div>
    </div>

    <form class="composer" @submit.prevent="submitNote">
      <textarea v-model="noteDraft" rows="3" placeholder="Add a note… (Ctrl+Enter to post)" @keydown.ctrl.enter="submitNote"></textarea>
      <button class="btn primary">Add note</button>
    </form>

    <div class="d-foot">
      <button class="btn danger" @click="emit('delete')">Delete task</button>
    </div>
  </aside>
</template>

<style scoped>
.scrim { position: fixed; inset: 0; top: 48px; background: #0007; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); z-index: 9; animation: fade 0.2s; }
@keyframes fade { from { opacity: 0; } }
.drawer { position: fixed; top: 48px; right: 0; bottom: 0; z-index: 10; width: 480px; max-width: 100vw; display: flex; flex-direction: column; padding: 16px 20px; background: var(--glass-strong); backdrop-filter: blur(22px) saturate(160%); -webkit-backdrop-filter: blur(22px) saturate(160%); border-left: 2px solid var(--c); box-shadow: -8px 0 40px color-mix(in srgb, var(--c) var(--glow), transparent), -2px 0 0 var(--c); overflow-y: auto; animation: slide 0.18s ease-out; }
@keyframes slide { from { transform: translateX(40px); opacity: 0; } }
.d-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.d-type { display: flex; align-items: center; gap: 8px; text-transform: uppercase; font-family: var(--mono); font-size: 12px; letter-spacing: 0.14em; color: var(--c); }
.d-type i { width: 10px; height: 10px; border-radius: 1px; background: var(--c); box-shadow: 0 0 10px var(--c); }
.d-title { width: 100%; padding: 6px 8px; font-size: 20px; font-weight: 600; border-color: transparent; background: transparent; }
.d-title:hover { border-color: var(--line); }
.d-fields { display: flex; gap: 16px; margin: 10px 0 0; }
.d-fields label { flex: 1; }
.d-fields label, .field { display: flex; flex-direction: column; gap: 4px; }
.d-fields label, .lbl { font-family: var(--mono); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
.d-fields select, .d-fields input { font-family: var(--mono); font-size: 12px; text-transform: uppercase; }
.field { margin-top: 12px; }
.d-envs { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; padding: 8px 12px; background: color-mix(in srgb, var(--col) 60%, transparent); border: 1px solid var(--line); border-radius: 2px; }
.track { display: flex; align-items: center; gap: 8px; cursor: pointer; font-family: var(--mono); font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.chip-tag { padding: 1px 8px; border: 1px solid color-mix(in srgb, var(--accent2) 55%, transparent); border-radius: 2px; background: transparent; color: var(--accent2); font-family: var(--mono); font-size: 11px; cursor: pointer; }
.chip-tag:hover { background: var(--danger-bg); color: var(--danger); border-color: var(--danger); }
.tag-in { flex: 1; min-width: 90px; font-family: var(--mono); font-size: 12px; }
.link-row { flex: 1; display: flex; gap: 8px; min-width: 0; }
.link-row input { flex: 1; font-family: var(--mono); font-size: 12px; }
.open { text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; color: var(--accent); border-color: var(--accent); }
h3 { margin: 18px 0 10px; font-family: var(--mono); font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent2); border-bottom: 1px solid var(--line); padding-bottom: 6px; }
h3::before { content: '// '; opacity: 0.6; }
.n { margin-left: 6px; padding: 0 7px; border: 1px solid var(--line); border-radius: 2px; color: var(--muted); font-size: 11px; }
.desc { width: 100%; resize: vertical; line-height: 1.45; }
.progress { height: 3px; margin-bottom: 8px; background: var(--line); }
.progress i { display: block; height: 100%; background: linear-gradient(90deg, var(--accent2), var(--accent)); transition: width 0.3s; }
.items { list-style: none; margin: 0 0 8px; padding: 0; }
.items li { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.items li span { flex: 1; overflow-wrap: anywhere; }
.items li.done span { color: var(--muted); text-decoration: line-through; }
.items input { accent-color: var(--accent); }
.add-item input { width: 100%; font-size: 13px; }
.thread { flex: 1; }
.none { color: var(--faint); font-family: var(--mono); font-size: 12px; }
.note { display: flex; gap: 10px; margin-bottom: 12px; }
.avatar { flex: none; width: 28px; height: 28px; clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%); background: linear-gradient(135deg, var(--accent2), var(--accent)); color: #07060f; display: grid; place-items: center; font-family: var(--mono); font-size: 12px; font-weight: 700; }
.bubble { flex: 1; min-width: 0; padding: 8px 12px; background: color-mix(in srgb, var(--note) 65%, transparent); border: 1px solid var(--glass-line); border-left: 2px solid var(--accent); border-radius: 2px; }
.meta { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); font-size: 11px; color: var(--muted); }
.bubble p { margin: 4px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.composer { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; margin-top: 8px; }
.composer textarea { width: 100%; resize: vertical; }
.d-foot { margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--line); }
</style>
