import { ref, computed, watchEffect } from 'vue'
import api from '../api'

// Task types come from the database (editable in Settings). Their colours reach the CSS as
// `--type-<key>` variables through one generated stylesheet: as picked in dark mode, a darker
// shade in light mode so they stay readable.
export function useTypes() {
  const typeList = ref([]) // [{ key, name, color, position, count }]
  const types = computed(() => typeList.value.map((t) => t.key))
  const typeName = (key) => typeList.value.find((t) => t.key === key)?.name || key

  const style = document.createElement('style')
  document.head.appendChild(style)
  watchEffect(() => {
    style.textContent = typeList.value
      .map(
        (t) =>
          `:root { --type-${t.key}: ${t.color}; }\n` +
          `:root[data-theme='light'] { --type-${t.key}: color-mix(in srgb, ${t.color} 70%, #000); }`,
      )
      .join('\n')
  })

  async function loadTypes() {
    typeList.value = await api.types()
  }

  return { typeList, types, typeName, loadTypes }
}
