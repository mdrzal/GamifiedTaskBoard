<script setup>
import { computed } from 'vue'
import EnvDots from './EnvDots.vue'
import { typeColor, prioColor, dueState, shortDate, isUrl, linkHost } from '../ui'

const props = defineProps({ task: Object, index: Number, typeLabel: String, envs: Array, selected: Boolean, dragging: Boolean })
defineEmits(['select', 'toggle-env', 'dragstart', 'dragend'])

// The details row only appears for tasks that actually use the optional fields.
const hasMeta = computed(() => {
  const t = props.task
  return t.priority || t.due_date || t.items.length || t.link || t.tags.length || t.is_pr || t.schedule_id
})
const itemsDone = computed(() => props.task.items.filter((i) => i.done).length)
const dueClass = computed(() => (props.task.status === 'done' ? '' : dueState(props.task.due_date)))
</script>

<template>
  <article class="card" :data-id="task.id" :class="{ done: task.status === 'done', sel: selected, dragging }"
    :style="{ '--c': typeColor(task.type), '--i': index }" draggable="true"
    @dragstart="$emit('dragstart', $event)" @dragend="$emit('dragend')" @click="$emit('select')">
    <div class="card-title">{{ task.title }}</div>
    <p v-if="task.description" class="card-desc">{{ task.description }}</p>

    <div v-if="hasMeta" class="card-meta">
      <span v-if="task.priority" class="pill prio" :style="{ '--c': prioColor(task.priority) }" :title="`Priority: ${task.priority}`">▲ {{ task.priority }}</span>
      <span v-if="task.due_date" class="pill due" :class="dueClass" title="Due date">◷ {{ shortDate(task.due_date) }}</span>
      <span v-if="task.items.length" class="pill check" :style="{ '--p': (itemsDone / task.items.length) * 100 + '%' }" title="Checklist">☑ {{ itemsDone }}/{{ task.items.length }}</span>
      <a v-if="task.is_pr && isUrl(task.link)" class="pill pr" :href="task.link" target="_blank" rel="noopener noreferrer" :title="`Open pull request: ${task.link}`" @click.stop>⑂ PR · {{ linkHost(task.link) }} ↗</a>
      <span v-else-if="task.is_pr" class="pill pr" title="Pull request">⑂ PR</span>
      <a v-if="!task.is_pr && isUrl(task.link)" class="pill link" :href="task.link" target="_blank" rel="noopener noreferrer" :title="`Open ${task.link}`" @click.stop>↗ {{ linkHost(task.link) }}</a>
      <span v-if="task.schedule_id" class="pill" title="Created by a schedule">↻ scheduled</span>
      <span v-for="tag in task.tags" :key="tag" class="tag">#{{ tag }}</span>
    </div>

    <div class="card-foot">
      <span class="type"><i></i>{{ typeLabel }}</span>
      <span class="right">
        <EnvDots v-if="task.track_envs" :envs="envs" :current="task.env" @toggle="$emit('toggle-env', $event)" />
        <span v-if="task.notes.length" class="notes" title="Notes">💬 {{ task.notes.length }}</span>
      </span>
    </div>
  </article>
</template>
