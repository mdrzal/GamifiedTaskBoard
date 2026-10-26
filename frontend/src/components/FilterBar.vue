<script setup>
// `filters` is the shared filter state from useFilters; this bar edits its fields directly.
defineProps({
  filters: Object, typeList: Array, priorities: Array, envs: Array, tags: Array,
  active: Number, shown: Number, total: Number,
})
defineEmits(['clear'])

const pretty = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })
</script>

<template>
  <div class="filters">
    <span class="flabel">Filter</span>
    <select v-model="filters.type" :class="{ on: filters.type }">
      <option value="">Type: any</option>
      <option v-for="t in typeList" :key="t.key" :value="t.key">{{ t.name }}</option>
    </select>
    <select v-model="filters.priority" :class="{ on: filters.priority }">
      <option value="">Priority: any</option>
      <option v-for="p in priorities" :key="p" :value="p">{{ p }}</option>
      <option value="none">no priority</option>
    </select>
    <select v-model="filters.due" :class="{ on: filters.due }">
      <option value="">Due: any</option>
      <option value="overdue">overdue</option>
      <option value="today">due today</option>
      <option value="week">next 7 days</option>
      <option value="none">no due date</option>
    </select>
    <select v-model="filters.env" :class="{ on: filters.env }">
      <option value="">Env: any</option>
      <option v-for="e in envs" :key="e" :value="e">{{ e.toUpperCase() }}</option>
      <option value="none">no environment</option>
    </select>
    <select v-if="tags.length" v-model="filters.tag" :class="{ on: filters.tag }">
      <option value="">Tag: any</option>
      <option v-for="tag in tags" :key="tag" :value="tag">#{{ tag }}</option>
    </select>
    <button class="chip" :class="{ on: filters.pr }" :style="{ '--c': 'var(--accent2)' }" @click="filters.pr = !filters.pr">⑂ PRs only</button>
    <button v-if="filters.dueOn" class="chip on" :style="{ '--c': 'var(--accent)' }" title="Show all due dates"
      @click="filters.dueOn = ''">📅 due {{ pretty(filters.dueOn) }} ✕</button>
    <template v-if="active">
      <button class="btn" @click="$emit('clear')">Clear {{ active }}</button>
      <span class="fcount">{{ shown }} of {{ total }} tasks</span>
    </template>
  </div>
</template>
