// src/utils/harmonyEngine.js
import { ROOTS, QUALITIES } from '../constants/music'
import { DIATONIC_SCALE, getRootIdx } from '../core/index.js'

export const STRENGTH_COLORS = {
  strong:    '#2a7a3a',
  medium:    '#b07820',
  weak:      '#7a6050',
  dissonant: '#b03030',
  same:      '#3a6ea8',
}

export function analyzeInterval(prevRootIdx, prevQuality, hoverRootIdx, sectionKey = 'C', sectionMode = 'major') {
  if (prevRootIdx === null || hoverRootIdx === null) return null
  const interval    = ((hoverRootIdx - prevRootIdx) + 12) % 12
  const prevQ       = prevQuality ?? 0
  const prevIsMin   = [1, 3, 4].includes(prevQ)
  const prevIsMaj   = prevQ === 0

  const keyRootIdx     = getRootIdx(sectionKey)
  const scaleIntervals = DIATONIC_SCALE[sectionMode] ?? DIATONIC_SCALE.major
  const hoverFromKey   = ((hoverRootIdx - keyRootIdx) + 12) % 12
  const isDiatonic     = scaleIntervals.includes(hoverFromKey)

  const map = {
    0:  { name: 'Unison',           desc: 'Same root — recolour or reharmonise',                                    sugQ: null, sugExt: null, strength: 'same'      },
    1:  { name: '♭II — Neapolitan', desc: 'Half-step up — chromatic tension',                                       sugQ: 0,    sugExt: 1,   strength: 'dissonant' },
    2:  { name: 'II — Supertonic',  desc: `Whole step — ${isDiatonic ? 'diatonic ii, wants resolution' : 'non-diatonic passing'}`, sugQ: 1, sugExt: 1, strength: 'medium' },
    3:  prevIsMin
        ? { name: '♭III — Relative Major', desc: `Relative major of ${sectionKey}${sectionMode === 'minor' ? ' (same key)' : ''}`, sugQ: 0, sugExt: null, strength: 'strong' }
        : { name: '♭III — Minor Mediant',  desc: 'Borrowed from parallel minor — dark colour',                      sugQ: 1,    sugExt: null, strength: 'medium' },
    4:  { name: 'III — Mediant',    desc: `${isDiatonic ? 'Diatonic iii — colour chord' : 'Chromatic mediant — unexpected brightness'}`, sugQ: prevIsMin ? 0 : 1, sugExt: null, strength: 'medium' },
    5:  { name: 'IV — Subdominant', desc: `Perfect 4th — ${isDiatonic ? 'strong diatonic plagal motion' : 'borrowed subdominant'}`, sugQ: prevIsMin ? 1 : 0, sugExt: null, strength: 'strong' },
    6:  { name: '♭V — Tritone Sub', desc: 'Tritone — maximum tension, sub-dominant function',                       sugQ: 0,    sugExt: 1,   strength: 'dissonant' },
    7:  { name: 'V — Dominant',     desc: `Perfect 5th — ${isDiatonic ? 'strongest diatonic pull to tonic' : 'secondary dominant'}`, sugQ: 0, sugExt: 1, strength: 'strong' },
    8:  prevIsMaj
        ? { name: 'VI — Relative Minor',  desc: `Relative minor — ${sectionMode === 'major' ? 'shares key sig, darkens mood' : 'same key'}`, sugQ: 1, sugExt: null, strength: 'strong' }
        : { name: '♭VI — Submediant',     desc: 'Flat 6th — dramatic borrowed chord from parallel major',           sugQ: 0,    sugExt: null, strength: 'medium' },
    9:  prevIsMin
        ? { name: 'VI — Relative Major',  desc: `Relative major — ${sectionMode === 'minor' ? 'same key, lifts the mood' : 'borrowed brightness'}`, sugQ: 0, sugExt: null, strength: 'strong' }
        : { name: 'VI — Submediant',      desc: `${isDiatonic ? 'Diatonic vi — gentle deceptive cadence' : 'Chromatic submediant'}`, sugQ: 1, sugExt: null, strength: 'medium' },
    10: { name: '♭VII — Subtonic',  desc: `Whole step below tonic — ${isDiatonic ? 'diatonic in minor/mixolydian' : 'rock/blues borrowed'}`, sugQ: 0, sugExt: null, strength: 'medium' },
    11: { name: 'VII — Leading Tone', desc: 'Half-step below — strong tendency to resolve upward',                  sugQ: 2,    sugExt: null, strength: 'medium' },
  }

  const rel = map[interval] ?? { name: 'Unknown', desc: '', sugQ: null, sugExt: null, strength: 'weak' }
  return { ...rel, interval, isDiatonic, color: STRENGTH_COLORS[rel.strength] }
}

// ── Canvas data model helpers ─────────────────────────────────────────────────

export const BEAT_W   = 30
export const BEAT_GAP = 3
export const ROW_H    = 48

export function makeSection(id, name, bars = 2, timeSig = 4, key = 'C', mode = 'major', bpm = 120) {
  return { id, name, bars, timeSig, totalBeats: bars * timeSig, key, mode, bpm, events: [] }
}

export const INITIAL_SONG = [
  makeSection(1, 'Intro',   2, 4, 'C', 'major', 120),
  makeSection(2, 'Verse',   2, 4, 'C', 'major', 120),
  makeSection(3, 'Pre-Ch.', 1, 4, 'C', 'major', 120),
  makeSection(4, 'Chorus',  2, 4, 'C', 'major', 120),
  makeSection(5, 'Bridge',  1, 4, 'A', 'minor', 120),
  makeSection(6, 'Outro',   1, 4, 'C', 'major', 120),
]

export function beatMap(section) {
  const map = Array(section.totalBeats).fill(null)
  for (const ev of section.events)
    for (let b = ev.beat; b < ev.beat + ev.span && b < section.totalBeats; b++) map[b] = ev
  return map
}

export function freeRuns(section) {
  const map = beatMap(section), runs = []
  let i = 0
  while (i < section.totalBeats) {
    if (map[i] === null) {
      let j = i
      while (j < section.totalBeats && map[j] === null) j++
      runs.push({ beat: i, span: j - i })
      i = j
    } else i++
  }
  return runs
}
