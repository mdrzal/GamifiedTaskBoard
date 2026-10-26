<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const glow = ref(null)
const SIZE = 460
const EASE = 0.14
const enabled = matchMedia('(pointer: fine)').matches
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

let tx = 0, ty = 0 // target (pointer)
let x = 0, y = 0 // rendered position, eased towards the target
let raf = 0

function place() {
  glow.value.style.transform = `translate(${x - SIZE / 2}px, ${y - SIZE / 2}px)`
}

// Only runs while the glow is still catching up with the pointer.
function tick() {
  x += (tx - x) * EASE
  y += (ty - y) * EASE
  place()
  raf = Math.abs(tx - x) + Math.abs(ty - y) > 0.5 ? requestAnimationFrame(tick) : 0
}

function onMove(e) {
  tx = e.clientX
  ty = e.clientY
  glow.value.style.opacity = 1
  if (reduced) {
    x = tx
    y = ty
    place()
  } else if (!raf) raf = requestAnimationFrame(tick)
}

const hide = () => glow.value && (glow.value.style.opacity = 0)

onMounted(() => {
  if (!enabled) return
  addEventListener('pointermove', onMove)
  document.documentElement.addEventListener('pointerleave', hide)
})
onUnmounted(() => {
  cancelAnimationFrame(raf)
  removeEventListener('pointermove', onMove)
  document.documentElement.removeEventListener('pointerleave', hide)
})
</script>

<template>
  <div v-if="enabled" ref="glow" class="cursor-glow" aria-hidden="true"></div>
</template>

<style scoped>
.cursor-glow { position: fixed; top: 0; left: 0; z-index: 0; width: 460px; height: 460px; border-radius: 50%; pointer-events: none; opacity: 0; transition: opacity 0.4s; will-change: transform; background: radial-gradient(circle, var(--cursor-core) 0%, var(--cursor-edge) 40%, transparent 70%); }
</style>
