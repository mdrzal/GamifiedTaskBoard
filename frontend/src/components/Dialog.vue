<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { dialog, answer } from '../composables/useDialog'

const input = ref(null)
const cancelButton = ref(null)
const okButton = ref(null)

// Capture phase, so Esc / Enter go to the dialog and not to the board behind it.
function onKey(e) {
  if (!dialog.open) return
  if (e.key === 'Escape') {
    e.preventDefault()
    e.stopImmediatePropagation()
    answer(false)
  } else if (e.key === 'Enter' && dialog.kind === 'text') {
    e.preventDefault()
    e.stopImmediatePropagation()
    if (dialog.value.trim()) answer(true)
  }
}
window.addEventListener('keydown', onKey, true)
onUnmounted(() => window.removeEventListener('keydown', onKey, true))

// Start on the safe choice: the text box, or Cancel for a destructive question.
watch(
  () => dialog.open,
  async (open) => {
    if (!open) return
    await nextTick()
    if (dialog.kind === 'text') {
      input.value?.focus()
      input.value?.select()
    } else (dialog.danger ? cancelButton : okButton).value?.focus()
  },
)
</script>

<template>
  <div v-if="dialog.open" class="dialog-scrim" @click.self="answer(false)">
    <div class="dialog" :class="{ danger: dialog.danger }" role="dialog" aria-modal="true" :aria-label="dialog.title">
      <h2>{{ dialog.title }}</h2>
      <p v-if="dialog.message">{{ dialog.message }}</p>
      <input v-if="dialog.kind === 'text'" ref="input" v-model="dialog.value" :placeholder="dialog.placeholder" maxlength="80" />
      <div class="dialog-actions">
        <button ref="cancelButton" class="btn" @click="answer(false)">Cancel</button>
        <button ref="okButton" class="btn" :class="dialog.danger ? 'danger solid' : 'primary'"
          :disabled="dialog.kind === 'text' && !dialog.value.trim()" @click="answer(true)">
          {{ dialog.confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>
