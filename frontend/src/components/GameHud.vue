<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { when } from '../ui'

const props = defineProps({ stats: Object, goal: Number, sound: Boolean })
const emit = defineEmits(['update:goal', 'toggle-sound'])

const open = ref(false)
const bump = ref(false)
const root = ref(null)

const pct = computed(() => {
  const s = props.stats
  return s ? Math.min(100, ((s.xp - s.level_floor) / (s.level_next - s.level_floor)) * 100) : 0
})
const goalPct = computed(() => Math.min(1, (props.stats?.resolved_today || 0) / props.goal))
const goalMet = computed(() => (props.stats?.resolved_today || 0) >= props.goal)
const RING = 2 * Math.PI * 9
const doneChallenges = computed(() => props.stats?.challenges.filter((c) => c.done).length || 0)
const unlocked = computed(() => props.stats?.achievements.filter((a) => a.unlocked).length || 0)

const kindLabel = (k) => ({ done: 'Resolved', env_dev: 'Shipped to DEV', env_qa: 'Passed QA', env_prd: 'Live in PRD', challenge: 'Challenge complete' })[k] || k
const kindIcon = (k) => ({ done: '✔', env_dev: '⌁', env_qa: '✓', env_prd: '🚀', challenge: '🎯' })[k] || '•'

// the XP number flashes whenever it goes up
watch(() => props.stats?.xp, (now, before) => {
  if (before === undefined || now <= before) return
  bump.value = true
  setTimeout(() => (bump.value = false), 800)
})

const outside = (e) => open.value && !root.value?.contains(e.target) && (open.value = false)
const esc = (e) => e.key === 'Escape' && (open.value = false)
onMounted(() => {
  addEventListener('click', outside)
  addEventListener('keydown', esc)
})
onUnmounted(() => {
  removeEventListener('click', outside)
  removeEventListener('keydown', esc)
})
</script>

<template>
  <div v-if="stats" ref="root" class="hud-wrap">
    <button class="hud" :class="{ bump }" title="Your progress" @click="open = !open">
      <span class="lvl"><small>LVL</small>{{ stats.level }}</span>
      <span class="xp">
        <span class="xp-top"><b>{{ stats.level_name }}</b><em>{{ stats.xp }} / {{ stats.level_next }} XP</em></span>
        <span class="bar"><i :style="{ width: pct + '%' }"></i></span>
      </span>
      <span class="streak" :class="{ hot: stats.streak > 0 }" title="Day streak">🔥 {{ stats.streak }}</span>
      <span class="goal" :class="{ met: goalMet }" :title="`Resolved today: ${stats.resolved_today} of ${goal}`">
        <svg viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" class="track" />
          <circle cx="12" cy="12" r="9" class="fill" :stroke-dasharray="RING" :stroke-dashoffset="RING * (1 - goalPct)" />
        </svg>
        <span>{{ stats.resolved_today }}/{{ goal }}</span>
      </span>
    </button>

    <div v-if="open" class="panel">
      <div class="p-head">
        <span class="p-lvl">LVL {{ stats.level }} · {{ stats.level_name }}</span>
        <span class="p-xp">{{ stats.xp }} XP today · {{ stats.level_next - stats.xp }} to next level</span>
        <span class="p-xp">Level resets daily at {{ stats.day_starts_at }} · lifetime {{ stats.total_xp }} XP</span>
      </div>

      <div class="grid">
        <div><b>{{ stats.resolved_today }}</b><span>resolved today</span></div>
        <div><b>{{ stats.resolved_week }}</b><span>last 7 days</span></div>
        <div><b>{{ stats.streak }}🔥</b><span>day streak</span></div>
        <div><b>{{ stats.best_streak }}</b><span>best streak</span></div>
        <div><b>{{ stats.total_done }}</b><span>all time</span></div>
      </div>

      <div class="row">
        <span>Daily goal</span>
        <span class="stepper">
          <button :disabled="goal <= 1" @click="emit('update:goal', goal - 1)">−</button>
          <b>{{ goal }}</b>
          <button :disabled="goal >= 20" @click="emit('update:goal', goal + 1)">+</button>
        </span>
      </div>
      <label class="row sound">
        <span>Sound effects</span>
        <input type="checkbox" :checked="sound" @change="emit('toggle-sound', $event.target.checked)" />
      </label>

      <h4>Daily challenges <span class="count">{{ doneChallenges }}/{{ stats.challenges.length }}</span></h4>
      <ul class="chal">
        <li v-for="c in stats.challenges" :key="c.id" :class="{ done: c.done }">
          <span class="ck">{{ c.done ? '✔' : '◇' }}</span>
          <span class="ct">
            <b>{{ c.text }}</b>
            <span class="pb"><i :style="{ width: (c.progress / c.target) * 100 + '%' }"></i></span>
          </span>
          <span class="cr">{{ c.progress }}/{{ c.target }} · +{{ c.reward }}</span>
        </li>
      </ul>

      <h4>Recent wins</h4>
      <p v-if="!stats.recent.length" class="none">Resolve a task or push one through an environment to start earning XP.</p>
      <ul class="wins">
        <li v-for="(w, i) in stats.recent" :key="i">
          <span class="ico">{{ kindIcon(w.kind) }}</span>
          <span class="t"><b>{{ w.title }}</b><small>{{ kindLabel(w.kind) }} · {{ when(w.created_at) }}</small></span>
          <span class="pts">+{{ w.points }}</span>
        </li>
      </ul>

      <h4>Milestones <span class="count">{{ unlocked }}/{{ stats.achievements.length }}</span></h4>
      <ul class="ach">
        <li v-for="a in stats.achievements" :key="a.id" :class="{ on: a.unlocked }">
          <span class="medal">{{ a.unlocked ? '🏆' : '🔒' }}</span>
          <span><b>{{ a.name }}</b><small>{{ a.desc }}</small></span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.hud-wrap { position: relative; margin-left: auto; }
.hud { display: flex; align-items: center; gap: 14px; padding: 4px 12px 4px 4px; border: 1px solid var(--field-line); border-radius: 3px; background: transparent; cursor: pointer; font-family: var(--mono); transition: all 0.15s; }
.hud:hover { border-color: var(--accent); box-shadow: 0 0 14px color-mix(in srgb, var(--accent) var(--glow), transparent); }
.lvl { display: grid; place-items: center; width: 34px; height: 34px; clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%); background: linear-gradient(135deg, var(--accent2), var(--accent)); color: #07060f; font-size: 15px; font-weight: 800; line-height: 1; }
.lvl small { display: block; font-size: 7px; letter-spacing: 0.1em; margin-bottom: -2px; }
.xp { display: flex; flex-direction: column; gap: 3px; min-width: 150px; }
.xp-top { display: flex; justify-content: space-between; gap: 10px; font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; }
.xp-top b { color: var(--text); font-weight: 700; }
.xp-top em { font-style: normal; color: var(--muted); transition: color 0.3s; }
.bump .xp-top em { color: var(--st-todo); animation: flash 0.8s; }
@keyframes flash { 30% { transform: scale(1.18); text-shadow: 0 0 10px currentColor; } }
.bar { display: block; height: 5px; background: var(--line); border-radius: 1px; overflow: hidden; }
.bar i { display: block; height: 100%; background: linear-gradient(90deg, var(--accent2), var(--accent)); box-shadow: 0 0 10px color-mix(in srgb, var(--accent) var(--glow), transparent); transition: width 0.9s cubic-bezier(.2, .8, .2, 1); }
.bump .bar i { animation: shine 0.8s; }
@keyframes shine { 50% { filter: brightness(1.8); } }
.streak { font-size: 12px; color: var(--muted); filter: grayscale(1); opacity: 0.7; }
.streak.hot { color: var(--prio-high); filter: none; opacity: 1; font-weight: 700; }
.goal { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); }
.goal svg { width: 24px; height: 24px; transform: rotate(-90deg); }
.goal circle { fill: none; stroke-width: 3; }
.goal .track { stroke: var(--line); }
.goal .fill { stroke: var(--accent); stroke-linecap: round; transition: stroke-dashoffset 0.8s cubic-bezier(.2, .8, .2, 1); }
.goal.met { color: var(--st-done); }
.goal.met .fill { stroke: var(--st-done); filter: drop-shadow(0 0 4px var(--st-done)); }
.goal.met svg { animation: pulse-ring 2.4s ease-in-out infinite; }
@keyframes pulse-ring { 50% { transform: rotate(-90deg) scale(1.15); } }

.panel { position: absolute; right: 0; top: calc(100% + 8px); z-index: 50; width: 380px; max-height: calc(100vh - 80px); overflow-y: auto; padding: 14px 16px; background: color-mix(in srgb, var(--panel) 96%, transparent); backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px); border: 1px solid var(--accent); border-radius: 3px; box-shadow: 0 12px 40px #0008, 0 0 24px color-mix(in srgb, var(--accent) var(--glow), transparent); color: var(--text); animation: drop 0.15s ease-out; }
@keyframes drop { from { opacity: 0; transform: translateY(-6px); } }
.p-head { display: flex; flex-direction: column; gap: 2px; margin-bottom: 12px; }
.p-lvl { font-family: var(--mono); font-size: 14px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.p-xp { font-family: var(--mono); font-size: 11px; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 12px; }
.grid div { display: flex; flex-direction: column; align-items: center; padding: 6px 2px; border: 1px solid var(--line); border-radius: 2px; text-align: center; }
.grid b { font-family: var(--mono); font-size: 16px; }
.grid span { font-size: 9px; letter-spacing: 0.05em; text-transform: uppercase; color: var(--muted); }
.row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; font-family: var(--mono); font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; border-top: 1px solid var(--line); }
.sound { cursor: pointer; }
.stepper { display: inline-flex; align-items: center; gap: 8px; }
.stepper button { width: 22px; height: 22px; padding: 0; border: 1px solid var(--field-line); border-radius: 2px; background: transparent; cursor: pointer; }
.stepper button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.stepper button:disabled { opacity: 0.35; cursor: default; }
h4 { margin: 14px 0 6px; font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent2); }
h4::before { content: '// '; opacity: 0.6; }
.count { margin-left: 6px; color: var(--muted); }
.none { margin: 0; font-size: 12px; color: var(--faint); }
ul { list-style: none; margin: 0; padding: 0; }
.wins li { display: flex; align-items: center; gap: 10px; padding: 5px 0; border-bottom: 1px solid var(--line); }
.ico { width: 22px; text-align: center; color: var(--accent); }
.t { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.t b { font-size: 13px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
small { font-size: 10px; color: var(--muted); }
.pts { font-family: var(--mono); font-weight: 700; color: var(--st-done); }
.chal li { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--line); }
.ck { width: 20px; text-align: center; color: var(--accent); }
.chal li.done .ck { color: var(--st-done); }
.chal li.done b { color: var(--muted); text-decoration: line-through; }
.ct { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.ct b { font-size: 13px; font-weight: 600; }
.pb { display: block; height: 4px; background: var(--line); border-radius: 1px; overflow: hidden; }
.pb i { display: block; height: 100%; background: linear-gradient(90deg, var(--accent2), var(--accent)); transition: width 0.5s; }
.chal li.done .pb i { background: var(--st-done); }
.cr { font-family: var(--mono); font-size: 11px; color: var(--muted); white-space: nowrap; }
.ach li { display: flex; align-items: center; gap: 10px; padding: 5px 0; opacity: 0.45; filter: grayscale(1); }
.ach li.on { opacity: 1; filter: none; }
.ach b { display: block; font-size: 13px; }
.medal { font-size: 18px; }
</style>
