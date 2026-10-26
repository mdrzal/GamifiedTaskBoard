<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { gameToday, isoDate } from '../ui'

// The current week (Monday first) with how many open tasks of this list are due each day.
// Clicking a day filters the board to it. "Today" turns over at 01:00, like levels and challenges.
const props = defineProps({ tasks: Array, dueOn: String, overdueOn: Boolean })
defineEmits(['pick-day', 'pick-overdue'])

const clock = ref(Date.now())
let timer
onMounted(() => (timer = setInterval(() => (clock.value = Date.now()), 60_000)))
onUnmounted(() => clearInterval(timer))

const today = computed(() => gameToday(new Date(clock.value)))
const todayDate = computed(() => new Date(`${today.value}T00:00:00`))

const days = computed(() => {
  const monday = new Date(todayDate.value)
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(monday)
    date.setDate(monday.getDate() + i)
    const iso = isoDate(date)
    return {
      iso,
      name: date.toLocaleDateString(undefined, { weekday: 'short' }),
      num: date.getDate(),
      isToday: iso === today.value,
      past: iso < today.value,
    }
  })
})

const open = computed(() => props.tasks.filter((t) => t.status !== 'done' && t.due_date))
const countOn = (iso) => open.value.filter((t) => t.due_date === iso).length
const overdue = computed(() => open.value.filter((t) => t.due_date < today.value).length)

const weekday = computed(() => todayDate.value.toLocaleDateString(undefined, { weekday: 'long' }))
const dateLabel = computed(() => todayDate.value.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' }))
const plural = (n) => `${n} task${n === 1 ? '' : 's'} due`
</script>

<template>
  <section class="week">
    <div class="side-title">This week</div>
    <div class="wk-today"><b>{{ weekday }}</b><span>{{ dateLabel }}</span></div>
    <button v-if="overdue" class="wk-overdue" :class="{ on: overdueOn }" @click="$emit('pick-overdue')">⚠ {{ overdue }} overdue</button>
    <ul>
      <li v-for="d in days" :key="d.iso">
        <button class="wk-day" :class="{ today: d.isToday, sel: dueOn === d.iso, past: d.past }"
          :title="countOn(d.iso) ? plural(countOn(d.iso)) : 'Nothing due'" @click="$emit('pick-day', d.iso)">
          <span class="wk-name">{{ d.name }}</span>
          <span class="wk-num">{{ d.num }}</span>
          <span v-if="countOn(d.iso)" class="wk-count">{{ countOn(d.iso) }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>
