// Celebration effects and sound. Everything is a short-lived fixed-position element animated with the
// Web Animations API, removed when it finishes. Nothing runs when the user prefers reduced motion.

const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches
const rand = (min, max) => min + Math.random() * (max - min)
const pick = (list) => list[Math.floor(Math.random() * list.length)]

// Centre and size of an element; falls back to the upper middle of the screen when it isn't on the page.
function where(el) {
  const r = el?.getBoundingClientRect?.()
  if (r && r.width) return { x: r.left + r.width / 2, y: r.top + r.height / 2, left: r.left, top: r.top, width: r.width, height: r.height }
  return { x: innerWidth / 2, y: innerHeight / 3, left: innerWidth / 2 - 120, top: innerHeight / 3 - 40, width: 240, height: 80 }
}

function particle(x, y, css, frames, options) {
  const p = document.createElement('i')
  p.style.cssText = `position:fixed;left:${x}px;top:${y}px;z-index:200;pointer-events:none;${css}`
  document.body.appendChild(p)
  p.animate(frames, options).onfinish = () => p.remove()
  return p
}

function ring(x, y, color, size = 70) {
  particle(
    x, y,
    `width:${size}px;height:${size}px;margin:${-size / 2}px 0 0 ${-size / 2}px;border:2px solid ${color};border-radius:50%;box-shadow:0 0 14px ${color}`,
    [{ transform: 'scale(0.1)', opacity: 0.9 }, { transform: 'scale(2.4)', opacity: 0 }],
    { duration: 700, easing: 'ease-out' },
  )
}

// DONE: neon confetti.
export function confetti(el) {
  if (reduced()) return
  const { x, y } = where(el)
  const palette = ['#00f0ff', '#ff2bd6', '#fcee0a', '#39ff14', '#b967ff']
  for (let i = 0; i < 32; i++) {
    const angle = rand(0, Math.PI * 2)
    const dist = rand(70, 210)
    particle(
      x, y,
      `width:6px;height:10px;border-radius:1px;background:${palette[i % palette.length]}`,
      [
        { transform: 'translate(0,0) rotate(0)', opacity: 1 },
        { transform: `translate(${Math.cos(angle) * dist}px,${Math.sin(angle) * dist + 90}px) rotate(${rand(0, 720)}deg)`, opacity: 0 },
      ],
      { duration: rand(900, 1400), easing: 'cubic-bezier(.2,.7,.3,1)' },
    )
  }
}

// PRD: three fireworks going off one after another around the card.
export function fireworks(el) {
  if (reduced()) return
  const { x, y, width } = where(el)
  const palettes = [['#39ff14', '#b6ff9e'], ['#fcee0a', '#fff7a1'], ['#ff2bd6', '#00f0ff']]
  const inView = (n, lo, hi) => Math.min(Math.max(n, lo), hi)
  const bursts = [[x, y - 50, 0], [x - width * 0.6, y - 130, 240], [x + width * 0.6, y - 100, 460]].map(
    ([bx, by, delay]) => [inView(bx, 80, innerWidth - 80), inView(by, 100, innerHeight - 80), delay],
  )
  bursts.forEach(([bx, by, delay], n) =>
    setTimeout(() => {
      ring(bx, by, palettes[n][0], 50)
      for (let i = 0; i < 30; i++) {
        const angle = (i / 30) * Math.PI * 2 + rand(-0.1, 0.1)
        const dist = rand(55, 135)
        const color = palettes[n][i % 2]
        particle(
          bx, by,
          `width:4px;height:4px;border-radius:50%;background:${color};box-shadow:0 0 8px ${color}`,
          [
            { transform: 'translate(0,0) scale(1.3)', opacity: 1 },
            { transform: `translate(${Math.cos(angle) * dist}px,${Math.sin(angle) * dist + 45}px) scale(0.2)`, opacity: 0 },
          ],
          { duration: rand(900, 1300), easing: 'cubic-bezier(.1,.7,.3,1)' },
        )
      }
    }, delay),
  )
}

// DEV: bits and code fragments spraying up off the card.
export function codeSparks(el) {
  if (reduced()) return
  const { x, y, width } = where(el)
  const glyphs = ['0', '1', '{', '}', '</>', '=>', '();', '#', '&&']
  ring(x, y, '#00f0ff')
  for (let i = 0; i < 24; i++) {
    const p = particle(
      x + rand(-width / 2, width / 2), y + rand(-8, 8),
      `font:700 ${rand(11, 17)}px ui-monospace,Consolas,monospace;color:#00f0ff;text-shadow:0 0 8px #00f0ff`,
      [
        { transform: 'translate(0,0)', opacity: 1 },
        { transform: `translate(${rand(-45, 45)}px,${-rand(70, 170)}px)`, opacity: 0 },
      ],
      { duration: rand(800, 1400), easing: 'ease-out' },
    )
    p.textContent = pick(glyphs)
  }
}

// QA: a scan line sweeps the card, then a big check stamps down and stars pop.
export function qaStamp(el) {
  if (reduced()) return
  const { x, y, left, top, width, height } = where(el)
  const color = '#fcee0a'
  particle(
    left, top,
    `width:${width}px;height:2px;background:${color};box-shadow:0 0 14px ${color}`,
    [{ transform: 'translateY(0)', opacity: 1 }, { transform: `translateY(${height}px)`, opacity: 0.2 }],
    { duration: 500, easing: 'ease-in-out' },
  )
  const stamp = particle(
    x, y,
    `margin:-36px 0 0 -30px;font:900 62px system-ui,sans-serif;color:${color};text-shadow:0 0 20px ${color}`,
    [
      { transform: 'scale(2.6) rotate(-14deg)', opacity: 0 },
      { transform: 'scale(1) rotate(-14deg)', opacity: 1, offset: 0.3 },
      { transform: 'scale(1) rotate(-14deg)', opacity: 1, offset: 0.72 },
      { transform: 'scale(1.15) rotate(-14deg)', opacity: 0 },
    ],
    { duration: 1100, delay: 350, fill: 'both' },
  )
  stamp.textContent = '✓'
  for (let i = 0; i < 12; i++) {
    const angle = rand(0, Math.PI * 2)
    const dist = rand(50, 120)
    const star = particle(
      x, y,
      `font:700 ${rand(12, 20)}px system-ui;color:${color};text-shadow:0 0 8px ${color}`,
      [
        { transform: 'translate(0,0) scale(0.3)', opacity: 0 },
        { transform: `translate(${Math.cos(angle) * dist}px,${Math.sin(angle) * dist}px) scale(1.2)`, opacity: 1, offset: 0.4 },
        { transform: `translate(${Math.cos(angle) * dist * 1.2}px,${Math.sin(angle) * dist * 1.2}px) scale(0.4)`, opacity: 0 },
      ],
      { duration: 900, delay: 450, fill: 'both', easing: 'ease-out' },
    )
    star.textContent = '✦'
  }
}

export function envBurst(env, el) {
  if (env === 'prd') fireworks(el)
  else if (env === 'qa') qaStamp(el)
  else if (env === 'dev') codeSparks(el)
}

// "+15 XP" floating up from a card.
export function floatText(el, text, color = '#fcee0a') {
  if (reduced()) return
  const { x, top } = where(el)
  const p = particle(
    x, top,
    `transform:translateX(-50%);font:800 18px ui-monospace,Consolas,monospace;color:${color};text-shadow:0 0 12px ${color};white-space:nowrap`,
    [
      { transform: 'translate(-50%, 0) scale(0.6)', opacity: 0 },
      { transform: 'translate(-50%, -22px) scale(1.25)', opacity: 1, offset: 0.2 },
      { transform: 'translate(-50%, -70px) scale(1)', opacity: 0 },
    ],
    { duration: 1400, easing: 'ease-out' },
  )
  p.textContent = text
}

// ---- sound (off unless the user turns it on) ----
export const soundOn = () => {
  try {
    return localStorage.getItem('sound') === '1'
  } catch {
    return false
  }
}

export const setSound = (on) => {
  try {
    localStorage.setItem('sound', on ? '1' : '0')
  } catch {
    /* storage can be unavailable; the toggle then only lasts for this page view */
  }
}

// [frequency Hz, start s, length s]
const tunes = {
  xp: [[1200, 0, 0.05]],
  done: [[784, 0, 0.07], [1047, 0.08, 0.14]],
  dev: [[523, 0, 0.08], [659, 0.07, 0.12]],
  qa: [[659, 0, 0.08], [784, 0.08, 0.08], [988, 0.16, 0.14]],
  prd: [[523, 0, 0.09], [659, 0.09, 0.09], [784, 0.18, 0.09], [1047, 0.27, 0.09], [1319, 0.36, 0.3]],
  achievement: [[880, 0, 0.1], [1175, 0.1, 0.1], [1568, 0.2, 0.28]],
  level: [[523, 0, 0.1], [659, 0.1, 0.1], [784, 0.2, 0.1], [1047, 0.3, 0.1], [784, 0.4, 0.1], [1047, 0.5, 0.1], [1568, 0.6, 0.4]],
}

let audio
export function playSound(kind) {
  if (!soundOn() || reduced()) return
  try {
    audio ||= new AudioContext()
    const now = audio.currentTime
    for (const [freq, start, length] of tunes[kind] || []) {
      const osc = audio.createOscillator()
      const gain = audio.createGain()
      osc.type = 'square'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.035, now + start)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + length)
      osc.connect(gain).connect(audio.destination)
      osc.start(now + start)
      osc.stop(now + start + length + 0.02)
    }
  } catch {
    /* audio blocked or unsupported: celebrations just stay silent */
  }
}
