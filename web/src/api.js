// Connection to the Laika back end: `python -m api.server --camera` (hub + camera + live diary).
// Every screen keeps its mock data as a fallback, so the app still works when the back end is off.
import { useCallback, useEffect, useRef, useState } from 'react'

// Same host as the page (so a phone on the same Wi-Fi reaches the laptop), port 5050 (5000 is taken by AirPlay on macOS).
// Override with VITE_LAIKA_API=http://host:port in web/.env.local.
export const API = import.meta.env.VITE_LAIKA_API || `http://${window.location.hostname}:5050`
export const STREAM_URL = `${API}/camera/stream`

export async function hubInput(msg) {
  const r = await fetch(`${API}/input`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(msg),
  })
  if (!r.ok) throw new Error(`hub input failed: ${r.status}`)
  return r.json()
}

export async function finishDay() {
  const r = await fetch(`${API}/diary/finish`, { method: 'POST' })
  if (!r.ok) throw new Error(`finish failed: ${r.status}`)
  return r.json()
}

// What the camera says the dog is doing, as the dashboard headline ("Pablo is …").
export const BEHAVIOUR_TEXT = {
  sleeping: 'sleeping', resting: 'resting', wandering: 'wandering around', zoomies: 'doing zoomies',
  playing: 'playing', tugging: 'tugging', eating: 'at the food bowl', waiting_at_door: 'waiting by the door',
  away: 'out of view',
}

// Polls GET /live. `connected` is false until the back end answers, and again if it stops answering.
export function useLaika(intervalMs = 1500) {
  const [live, setLive] = useState(null)
  const [connected, setConnected] = useState(false)
  const [days, setDays] = useState({})
  const wasConnected = useRef(false)

  const refreshDays = useCallback(async () => {
    try { setDays(await (await fetch(`${API}/diary/days`)).json()) } catch {}
  }, [])

  useEffect(() => {
    let stop = false
    let timer
    const poll = async () => {
      let ok = false
      try {
        const r = await fetch(`${API}/live`)
        if (!r.ok) throw new Error()
        const data = await r.json()
        if (stop) return
        ok = true
        setLive(data)
        setConnected(true)
        if (!wasConnected.current) { wasConnected.current = true; refreshDays() }
      } catch {
        if (!stop) { setConnected(false); wasConnected.current = false }
      }
      // Back off to every 5 s while the back end is off, so the console isn't flooded.
      if (!stop) timer = setTimeout(poll, ok ? intervalMs : 5000)
    }
    poll()
    return () => { stop = true; clearTimeout(timer) }
  }, [intervalMs, refreshDays])

  return { connected, live, days, refreshDays }
}

// "12:57 Dog completed a tug round…" -> { time: '12:57', text: 'Pablo completed a tug round…' }
export function parseNotification(n, name) {
  const m = /^(\d{1,2}:\d{2}) (.*)$/.exec(n)
  const text = (m ? m[2] : n).replace(/^Dog\b/, name).replace(/\bDog\b/g, name)
  return { time: m ? m[1] : '', text }
}

// A diary written by the back end, split into the pieces the diary page draws:
// drops the italic date line and the "Pablo 🐾" line (the page draws its own paw) and pulls out a
// short sign-off such as "Waggingly yours," so it can replace the page's default "Love,".
export function splitDiary(text) {
  const lines = text.trim().split('\n')
  if (lines[0]?.trim().startsWith('*')) lines.shift()
  let signoff = null
  if (lines.at(-1)?.trim().endsWith('🐾')) {
    lines.pop()
    while (lines.length && !lines.at(-1).trim()) lines.pop()
    const prev = lines.at(-1)?.trim() || ''
    if (prev.length < 50 && prev.endsWith(',')) { signoff = prev.slice(0, -1); lines.pop() }
  }
  const body = lines.join('\n').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
  return { body, signoff }
}
