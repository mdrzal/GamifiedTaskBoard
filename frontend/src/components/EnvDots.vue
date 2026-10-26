<script setup>
import { envColor, envLabel } from '../ui'

defineProps({ envs: Array, current: String, labels: Boolean })
defineEmits(['toggle'])
</script>

<template>
  <span class="dots">
    <button v-for="e in envs" :key="e" type="button" class="env" :class="{ on: current === e }"
      :style="{ '--c': envColor(e) }" :title="current === e ? `Currently in ${envLabel(e)} (click to clear)` : `Move to ${envLabel(e)}`"
      @click.stop="$emit('toggle', e)">
      <span class="circle">{{ envLabel(e)[0] }}</span>
      <span v-if="labels" class="label">{{ envLabel(e) }}</span>
    </button>
  </span>
</template>

<style scoped>
.dots { display: inline-flex; gap: 6px; }
.env { display: inline-flex; align-items: center; gap: 6px; padding: 0; border: 0; background: transparent; cursor: pointer; font-family: var(--mono); font-size: 11px; letter-spacing: 0.08em; color: var(--muted); }
.env.on .label { color: var(--text); }
.circle { position: relative; width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--c); color: var(--c); display: grid; place-items: center; font-size: 9px; font-weight: 700; opacity: 0.7; transition: all 0.15s; }
.env:hover .circle { opacity: 1; box-shadow: 0 0 10px color-mix(in srgb, var(--c) var(--glow), transparent); }
.env.on .circle { opacity: 1; background: var(--c); color: var(--on-env); box-shadow: 0 0 12px color-mix(in srgb, var(--c) var(--glow), transparent), 0 0 3px var(--c); animation: pop 0.5s cubic-bezier(.3, 1.6, .5, 1), breathe 2.6s ease-in-out 0.5s infinite; }
/* a ring keeps radiating from the environment the task is currently in */
.env.on .circle::after { content: ''; position: absolute; inset: -2px; border: 2px solid var(--c); border-radius: 50%; animation: ping 2.6s ease-out 0.5s infinite; pointer-events: none; }
@keyframes pop { 0% { transform: scale(0.5); } 60% { transform: scale(1.4); } 100% { transform: scale(1); } }
@keyframes breathe { 50% { box-shadow: 0 0 20px var(--c), 0 0 4px var(--c); } }
@keyframes ping { 0% { transform: scale(1); opacity: 0.8; } 70%, 100% { transform: scale(2.3); opacity: 0; } }
</style>
