import { QUALITIES, EXTENSIONS } from '../constants/music.js'

let mcgillEventId = 1000

const ROOT_INDEX_BY_TOKEN = {
  C: 0,
  'C#': 1,
  Db: 1,
  D: 2,
  'D#': 3,
  Eb: 3,
  E: 4,
  F: 5,
  'F#': 6,
  Gb: 6,
  G: 7,
  'G#': 8,
  Ab: 8,
  A: 9,
  'A#': 10,
  Bb: 10,
  B: 11,
}

const SECTION_TYPE_MAP = {
  Bridge: 'Bridge',
  Chorus: 'Chorus',
  Intro: 'Intro',
  Other: 'Other',
  Outro: 'Outro',
  PreChorus: 'Pre-Ch.',
  Transition: 'Trans.',
  Verse: 'Verse',
}

function toDisplayRoot(rootToken) {
  if (!rootToken) return null
  if (rootToken.endsWith('b')) return `${rootToken[0]}♭`
  if (rootToken.endsWith('#')) return `${rootToken[0]}♯`
  return rootToken
}

function mapInversion(inversionToken) {
  switch (inversionToken) {
    case '3':
      return 1
    case '5':
      return 2
    default:
      return 0
  }
}

function extensionFromParenthetical(token) {
  if (!token) return 0
  if (token.includes('13')) return 7
  if (token.includes('11')) return 6
  if (token.includes('9')) return 5
  if (token.includes('b7') || token.includes('7')) return 1
  return 0
}

function makeChordLabel(root, qualityIdx, extensionIdx) {
  const q = QUALITIES[qualityIdx] ?? QUALITIES[0]
  const ext = EXTENSIONS[extensionIdx] ?? EXTENSIONS[0]
  const noExt = q.label === '°7' || q.label === '5'
  const extSymbol = noExt ? '' : ext.symbol
  return `${root}${q.symbol}${extSymbol}`
}

function mapQualityExtension(baseToken, parentheticalToken) {
  switch (baseToken) {
    case 'maj':
      return { qualityIdx: 0, extensionIdx: extensionFromParenthetical(parentheticalToken) }
    case 'min':
      return { qualityIdx: 1, extensionIdx: extensionFromParenthetical(parentheticalToken) }
    case 'dim7':
      return { qualityIdx: 3, extensionIdx: 0 }
    case '7':
      return { qualityIdx: 0, extensionIdx: 1 }
    case 'maj7':
      return { qualityIdx: 0, extensionIdx: 2 }
    case 'maj6':
      return { qualityIdx: 0, extensionIdx: 3 }
    case 'maj9':
    case 'maj9#11':
      return { qualityIdx: 0, extensionIdx: 5 }
    case 'min7':
      return { qualityIdx: 1, extensionIdx: 1 }
    case 'min11':
      return { qualityIdx: 1, extensionIdx: 6 }
    case 'sus2':
      return { qualityIdx: 6, extensionIdx: extensionFromParenthetical(parentheticalToken) }
    case 'sus4':
      return { qualityIdx: 7, extensionIdx: extensionFromParenthetical(parentheticalToken) }
    case '5':
      return { qualityIdx: 8, extensionIdx: 0 }
    case '9':
      return { qualityIdx: 0, extensionIdx: 5 }
    case '1/1':
      return { qualityIdx: 0, extensionIdx: 0 }
    default:
      throw new Error(`Unsupported Harte quality token "${baseToken}"`)
  }
}

export function parseHarteChord(harte) {
  if (harte === 'N' || harte === 'X') return null
  if (typeof harte !== 'string' || !harte.includes(':')) {
    throw new Error(`Invalid Harte chord "${String(harte)}"`)
  }

  const [rootTokenRaw, descriptorRaw] = harte.split(':')
  const rootIdx = ROOT_INDEX_BY_TOKEN[rootTokenRaw]
  if (rootIdx === undefined) {
    throw new Error(`Unsupported Harte root "${rootTokenRaw}" in "${harte}"`)
  }

  const root = toDisplayRoot(rootTokenRaw)
  let baseToken = descriptorRaw
  let parentheticalToken = ''
  let inversionToken = ''

  if (descriptorRaw.startsWith('1/1')) {
    baseToken = '1/1'
  } else {
    const parenMatch = descriptorRaw.match(/\(([^)]+)\)/)
    if (parenMatch) {
      parentheticalToken = parenMatch[1]
      baseToken = descriptorRaw.replace(/\([^)]+\)/, '')
    }

    const slashIdx = baseToken.indexOf('/')
    if (slashIdx >= 0) {
      inversionToken = baseToken.slice(slashIdx + 1)
      baseToken = baseToken.slice(0, slashIdx)
    } else {
      const slashWithParen = descriptorRaw.match(/\/([^/()]+)$/)
      if (slashWithParen) inversionToken = slashWithParen[1]
    }
  }

  const normBase = baseToken.replace(/\s+/g, '')
  const { qualityIdx, extensionIdx } = mapQualityExtension(normBase, parentheticalToken)
  const inversionIdx = mapInversion(inversionToken)

  return {
    label: makeChordLabel(root, qualityIdx, extensionIdx),
    root,
    rootIdx,
    qualityIdx,
    extensionIdx,
    inversionIdx,
    harte,
  }
}

export function normaliseSectionType(sectionType) {
  return SECTION_TYPE_MAP[sectionType] ?? 'Other'
}

function makeBaseSection(id, name, bars = 2, timeSig = 4, key = 'C', mode = 'major', bpm = 120) {
  return { id, name, bars, timeSig, totalBeats: bars * timeSig, key, mode, bpm, events: [] }
}

function buildSectionFromSource(srcSection, i, bpm, name) {
  const chords = Array.isArray(srcSection.chords) ? srcSection.chords : []
  const timeSig = 4
  const durationMs = Number.isFinite(srcSection.duration_ms) ? srcSection.duration_ms : 0
  const estimatedBeats = durationMs > 0
    ? Math.round((durationMs / 60000) * bpm)
    : chords.length
  const derivedBeats = Math.max(chords.length, estimatedBeats, 1)
  const bars = Math.max(1, Math.ceil(derivedBeats / timeSig))
  const sectionId = srcSection.id ?? `mcgill_${i + 1}`
  const section = makeBaseSection(sectionId, name, bars, timeSig, 'C', 'major', bpm)
  section.keyDetected = false
  section.sourceStartMs = Number.isFinite(srcSection.start_ms) ? srcSection.start_ms : 0
  section.sourceDurationMs = durationMs

  const slotCount = Math.max(chords.length, 1)
  const beatsPerSlot = section.totalBeats / slotCount

  chords.forEach((harte, iChord) => {
    const beat = Math.min(section.totalBeats - 1, Math.round(iChord * beatsPerSlot))
    const nextBeat = Math.min(section.totalBeats, Math.round((iChord + 1) * beatsPerSlot))
    const span = Math.max(1, nextBeat - beat)
    const parsed = parseHarteChord(harte)
    if (!parsed) return
    const extensionSymbol = EXTENSIONS[parsed.extensionIdx]?.symbol ?? ''
    section.events.push({
      id: mcgillEventId++,
      beat,
      beatFloat: beat,
      span,
      durationBeats: span,
      label: parsed.label,
      root: parsed.root,
      quality: QUALITIES[parsed.qualityIdx]?.label ?? 'maj',
      extensions: extensionSymbol ? [extensionSymbol] : [],
      inversion: parsed.inversionIdx,
      bassNote: undefined,
      source: 'mcgill',
      harte: parsed.harte,
    })
  })

  section.events.sort((a, b) => a.beat - b.beat || a.id - b.id)
  return section
}

function getSectionSignature(section) {
  if (!Array.isArray(section.events) || section.events.length === 0) return 'EMPTY'
  const parts = []
  let prev = null
  let count = 0
  for (const ev of section.events) {
    const label = ev.label ?? 'N'
    if (label === prev) count += 1
    else {
      if (prev !== null) parts.push(`${prev}x${count}`)
      prev = label
      count = 1
    }
  }
  if (prev !== null) parts.push(`${prev}x${count}`)
  return parts.join('|')
}

function letterForIndex(i) {
  return String.fromCharCode(65 + (i % 26))
}

function sortSectionsByTime(sections) {
  return [...sections].sort((a, b) => {
    const aStart = Number.isFinite(a.start_ms) ? a.start_ms : Number.POSITIVE_INFINITY
    const bStart = Number.isFinite(b.start_ms) ? b.start_ms : Number.POSITIVE_INFINITY
    if (aStart !== bStart) return aStart - bStart
    return String(a.id ?? '').localeCompare(String(b.id ?? ''))
  })
}

export function importMcGillJson(json, options = {}) {
  if (!json || !Array.isArray(json.sections) || json.sections.length === 0) {
    throw new Error('Invalid McGill JSON: expected non-empty "sections" array.')
  }

  const title = typeof json.title === 'string' && json.title.trim() ? json.title : 'Untitled'
  const artist = typeof json.artist === 'string' && json.artist.trim() ? json.artist : 'Unknown Artist'
  const bpm = Number.isFinite(json.bpm) && json.bpm > 0 ? json.bpm : 120
  const strategy = options.sectionStrategy === 'dataset' ? 'dataset' : 'auto-json'
  const ordered = sortSectionsByTime(json.sections)

  let song = []
  if (strategy === 'dataset') {
    const sectionCounters = {}
    song = ordered.map((srcSection, i) => {
      const baseName = normaliseSectionType(srcSection.sectionType)
      sectionCounters[baseName] = (sectionCounters[baseName] ?? 0) + 1
      const count = sectionCounters[baseName]
      const name = count > 1 ? `${baseName} ${count}` : baseName
      return buildSectionFromSource(srcSection, i, bpm, name)
    })
  } else {
    const raw = ordered.map((srcSection, i) =>
      buildSectionFromSource(srcSection, i, bpm, `Part ${i + 1}`))
    const signatureToLetter = new Map()
    const perLetterCount = {}
    let nextLetterIdx = 0

    song = raw.map((section) => {
      const signature = getSectionSignature(section)
      if (!signatureToLetter.has(signature)) {
        signatureToLetter.set(signature, letterForIndex(nextLetterIdx))
        nextLetterIdx += 1
      }
      const letter = signatureToLetter.get(signature)
      perLetterCount[letter] = (perLetterCount[letter] ?? 0) + 1
      const name = perLetterCount[letter] > 1
        ? `Part ${letter} ${perLetterCount[letter]}`
        : `Part ${letter}`
      return {
        ...section,
        name,
        sectionSignature: signature,
      }
    })
  }

  song[0].meta = { title, artist, bpm, source: 'mcgill', sectionStrategy: strategy }
  return song
}
