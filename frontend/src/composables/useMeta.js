import { ref } from 'vue'
import api from '../api'

// The fixed choices the server offers: statuses (board columns), environments and priorities.
export function useMeta() {
  const statuses = ref([])
  const envs = ref([])
  const priorities = ref([])

  async function loadMeta() {
    const meta = await api.meta()
    statuses.value = meta.statuses
    envs.value = meta.envs
    priorities.value = meta.priorities
  }

  return { statuses, envs, priorities, loadMeta }
}
