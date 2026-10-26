import { reactive } from 'vue'

// In-app replacements for the browser's confirm() and prompt(), which can be blocked or silently
// ignored (for example inside an embedded browser). Both return a promise:
//   askConfirm(...) -> true / false      askText(...) -> the typed text, or null if cancelled
// <Dialog> (mounted once in App.vue) shows whichever one is open.
export const dialog = reactive({
  open: false,
  kind: 'confirm', // 'confirm' | 'text'
  title: '',
  message: '',
  confirmLabel: 'OK',
  danger: false,
  value: '',
  placeholder: '',
})

let finish = null

function show(config) {
  if (finish) answer(false) // a new question replaces one that was still open
  return new Promise((resolve) => {
    Object.assign(dialog, { message: '', value: '', placeholder: '', danger: false, ...config, open: true })
    finish = resolve
  })
}

export const askConfirm = ({ title, message = '', confirmLabel = 'Delete', danger = true }) =>
  show({ kind: 'confirm', title, message, confirmLabel, danger })

export const askText = ({ title, value = '', placeholder = '', confirmLabel = 'Save' }) =>
  show({ kind: 'text', title, value, placeholder, confirmLabel })

export function answer(ok) {
  if (!finish) return
  const resolve = finish
  finish = null
  dialog.open = false
  resolve(dialog.kind === 'text' ? (ok ? dialog.value.trim() : null) : ok)
}
