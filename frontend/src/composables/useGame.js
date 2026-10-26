import { ref, watch, nextTick } from 'vue'
import api from '../api'
import { confetti, fireworks, floatText, playSound, soundOn, setSound } from '../effects'

const store = {
  get(key) {
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value)
    } catch {
      /* storage can be unavailable; the choice then only lasts for this page view */
    }
  },
}

const unlockedIds = (stats) => new Set(stats.achievements.filter((a) => a.unlocked).map((a) => a.id))

// XP, streak, daily goal, sound, and the toasts / level-up banner that announce what you earned.
export function useGame() {
  const stats = ref(null)
  const sound = ref(soundOn())
  const toasts = ref([])
  const levelUp = ref(null)
  let toastId = 0

  const savedGoal = Number(store.get('goal'))
  const goal = ref(savedGoal >= 1 && savedGoal <= 20 ? savedGoal : 3)
  watch(goal, (g) => store.set('goal', String(g)))

  function setSoundOn(on) {
    sound.value = on
    setSound(on)
    if (on) playSound('xp')
  }

  function toast(text, kind = '') {
    const id = ++toastId
    toasts.value.push({ id, text, kind })
    setTimeout(() => (toasts.value = toasts.value.filter((t) => t.id !== id)), 4200)
  }

  // Milestones already announced in this browser; null means none were ever recorded.
  function seenMilestones() {
    const raw = store.get('seenAchievements')
    try {
      return raw === null ? null : new Set(JSON.parse(raw))
    } catch {
      return null
    }
  }
  const rememberMilestones = (seen) => store.set('seenAchievements', JSON.stringify([...seen]))

  async function loadStats() {
    try {
      stats.value = await api.stats()
    } catch {
      /* the board works fine without the HUD */
    }
    return stats.value
  }

  // First load: fetch stats and remember what is already unlocked so old milestones are not announced.
  async function initStats() {
    const first = await loadStats()
    if (first && seenMilestones() === null) rememberMilestones(unlockedIds(first))
  }

  function showLevelUp(next) {
    levelUp.value = { level: next.level, name: next.level_name }
    playSound('level')
    nextTick(() => fireworks(document.querySelector('.lu-card')))
    setTimeout(() => (levelUp.value = null), 3400)
  }

  // Compare stats before and after an action and react to whatever it earned (or took back).
  // `el` is where the +/- XP should rise from.
  async function reward(prev, el) {
    const next = await loadStats()
    if (!next || !prev) return

    const gain = next.xp - prev.xp
    if (gain > 0) {
      floatText(el, `+${gain} XP`)
      playSound('xp')
    } else if (gain < 0) {
      floatText(el, `−${-gain} XP`, '#ff5577') // undoing progress takes its XP back
    }

    if (next.day === prev.day && next.level > prev.level) showLevelUp(next)

    if (prev.resolved_today < goal.value && next.resolved_today >= goal.value) {
      toast(`Daily goal hit: ${next.resolved_today} resolved today`, 'goal')
      confetti(el)
      playSound('achievement')
    }
    if (next.streak > prev.streak) toast(`🔥 ${next.streak}-day streak`, 'streak')

    for (const c of next.challenges) {
      const before = prev.challenges?.find((p) => p.id === c.id)
      if (c.done && before && !before.done) {
        toast(`🎯 Challenge complete: ${c.text} (+${c.reward} XP)`, 'goal')
        confetti(el)
        playSound('achievement')
      }
    }

    const seen = seenMilestones() ?? unlockedIds(prev)
    for (const a of next.achievements) {
      if (a.unlocked && !seen.has(a.id)) {
        toast(`🏆 Milestone unlocked: ${a.name}`, 'ach')
        seen.add(a.id)
        playSound('achievement')
      }
    }
    rememberMilestones(seen)
  }

  return { stats, goal, sound, toasts, levelUp, toast, setSoundOn, initStats, loadStats, reward }
}
