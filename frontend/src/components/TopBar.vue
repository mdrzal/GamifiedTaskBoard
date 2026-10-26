<script setup>
import GameHud from './GameHud.vue'

defineProps({ search: String, stats: Object, goal: Number, sound: Boolean, theme: String, settingsOpen: Boolean })
defineEmits(['update:search', 'update:goal', 'toggle-sound', 'toggle-settings', 'toggle-theme'])
</script>

<template>
  <header class="topbar">
    <div class="brand"><span class="logo">◢◤</span> TASK<b>BOARD</b></div>
    <input :value="search" class="search" placeholder="Search tasks…" @input="$emit('update:search', $event.target.value)" />
    <GameHud :stats="stats" :goal="goal" :sound="sound" @update:goal="$emit('update:goal', $event)" @toggle-sound="$emit('toggle-sound', $event)" />
    <button class="theme gear" :class="{ on: settingsOpen }" title="Settings" @click="$emit('toggle-settings')">⚙</button>
    <button class="theme" :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'" @click="$emit('toggle-theme')">
      {{ theme === 'dark' ? '☀' : '☾' }}
    </button>
  </header>
</template>
