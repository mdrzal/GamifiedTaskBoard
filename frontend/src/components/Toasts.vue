<script setup>
defineProps({ toasts: Array, levelUp: Object })
defineEmits(['dismiss-level-up'])
</script>

<template>
  <div class="toasts">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="t.kind">{{ t.text }}</div>
  </div>
  <div v-if="levelUp" class="levelup" @click="$emit('dismiss-level-up')">
    <div class="lu-card"><small>LEVEL UP</small><b>LVL {{ levelUp.level }}</b><span>{{ levelUp.name }}</span></div>
  </div>
</template>
