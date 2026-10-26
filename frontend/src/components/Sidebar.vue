<script setup>
import { ref } from 'vue'
import WeekStrip from './WeekStrip.vue'

defineProps({ lists: Array, currentId: Number, tasks: Array, dueOn: String, overdueOn: Boolean })
const emit = defineEmits(['select', 'add', 'pick-day', 'pick-overdue'])

const name = ref('')

function submit() {
  const value = name.value.trim()
  if (!value) return
  name.value = ''
  emit('add', value)
}
</script>

<template>
  <nav class="sidebar">
    <WeekStrip :tasks="tasks" :due-on="dueOn" :overdue-on="overdueOn" @pick-day="emit('pick-day', $event)" @pick-overdue="emit('pick-overdue')" />
    <div class="side-title">Task lists</div>
    <a v-for="l in lists" :key="l.id" :class="{ active: l.id === currentId }" @click="emit('select', l.id)">
      <span class="name">{{ l.name }}</span>
      <span class="count">{{ l.done }}/{{ l.total }}</span>
      <i class="bar" :style="{ width: (l.total ? (l.done / l.total) * 100 : 0) + '%' }"></i>
    </a>
    <form @submit.prevent="submit">
      <input v-model="name" placeholder="New list name…" />
      <button class="btn primary" title="Create list" :disabled="!name.trim()">Add</button>
    </form>
  </nav>
</template>
