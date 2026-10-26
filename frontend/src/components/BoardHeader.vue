<script setup>
import { typeColor } from '../ui'

defineProps({ name: String, typeList: Array, typeFilter: String })
defineEmits(['set-type', 'rename', 'delete'])
</script>

<template>
  <div class="board-head">
    <h1>{{ name }}</h1>
    <div class="chips">
      <button v-for="t in typeList" :key="t.key" class="chip" :class="{ on: typeFilter === t.key }"
        :style="{ '--c': typeColor(t.key) }" @click="$emit('set-type', typeFilter === t.key ? '' : t.key)">
        <i></i>{{ t.name }}
      </button>
    </div>
    <span class="spacer"></span>
    <button class="btn" @click="$emit('rename')">Rename</button>
    <button class="btn danger" @click="$emit('delete')">Delete list</button>
  </div>
</template>
