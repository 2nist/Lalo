import { useEffect, useMemo, useState } from 'react'
import { ROOTS, QUALITIES } from '../../constants/music.js'
import { parseLabelToContext } from '../../utils/chordUtils.js'
import {
  DIATONIC_SCALE,
  transposeProgression,
  chordToNumeral,
  fingerprintProgression,
  matchNamedProgression,
  matchVampPattern,
  getRootIdx,
  normalizeRoot,
} from '../../core/index.js'

let pbId = 3000

const NUMERAL_SUGGESTIONS = [
  'I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°',
  'i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII',
  'bII', 'bIII', 'bVI', 'bVII',
]

function tokenToNumeralFromChordToken(token, key, mode) {
  const parsed = parseLabelToContext(String(token ?? '').trim())
  if (!parsed) return null
  const root = ROOTS[parsed.rootIdx] ?? 'C'
  const quality = QUALITIES[parsed.qualityIdx]?.label ?? 'maj'
  return chordToNumeral(root, quality, key, mode)
}

function convertLetterTokensToNumerals(tokens, key, mode) {
  return tokens.map((token) => {
    const res = tokenToNumeralFromChordToken(token, key, mode)
    return res?.numeral ?? null
  })
}

function convertLetterTokensToNumeralsKeepShape(tokens, key, mode) {
  return tokens.map((token) => {
    const raw = String(token ?? '').trim()
    if (!raw) return ''
    const res = tokenToNumeralFromChordToken(raw, key, mode)
    return res?.numeral ?? raw
  })
}

function transposeNumeralTokensKeepShape(tokens, key, mode) {
  return tokens.map((token) => {
    const raw = String(token ?? '').trim()
    if (!raw) return ''
    return transposeProgression([raw], null, key, mode)?.[0] ?? raw
  })
}

function estimateKeyFromChordTokens(tokens) {
  const parsed = tokens
    .map((token) => parseLabelToContext(String(token ?? '').trim()))
    .filter(Boolean)

  if (!parsed.length) return null

  const roots = parsed.map((ctx) => ctx.rootIdx)
  const firstRootIdx = roots[0]
  let best = { key: 'C', mode: 'major', count: -1, tonicHit: 0 }

  for (const rootName of ROOTS) {
    const keyIdx = getRootIdx(rootName)
    for (const mode of ['major', 'minor']) {
      const scale = DIATONIC_SCALE[mode] ?? DIATONIC_SCALE.major
      const set = new Set(scale.map((v) => (keyIdx + v) % 12))
      const count = roots.filter((r) => set.has(r)).length
      const tonicHit = firstRootIdx === keyIdx ? 1 : 0
      if (
        count > best.count ||
        (count === best.count && tonicHit > best.tonicHit) ||
        (count === best.count && tonicHit === best.tonicHit && mode === 'major' && best.mode !== 'major')
      ) {
        best = { key: rootName, mode, count, tonicHit }
      }
    }
  }

  const confidence = best.count / roots.length
  if (confidence >= 0.6) return { ...best, confidence }
  return null
}

function cleanTokens(tokens) {
  return tokens.map((t) => String(t ?? '').trim()).filter(Boolean)
}

function Pill({ children, active = false, borrowed = false, onClick, onRemove }) {
  return (
    <span
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '3px 8px',
        borderRadius: 3,
        border: `1px solid ${active ? 'var(--accent)' : 'rgba(196,130,42,0.4)'}`,
        borderLeft: borrowed ? '3px solid var(--accent-warm)' : undefined,
        background: active ? 'rgba(196,130,42,0.22)' : 'rgba(196,130,42,0.12)',
        color: 'var(--ink-primary)',
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        fontWeight: 700,
        cursor: 'pointer',
        userSelect: 'none',
      }}
    >
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          style={{
            border: 'none',
            background: 'transparent',
            color: 'var(--ink-secondary)',
            fontSize: 11,
            cursor: 'pointer',
            lineHeight: 1,
          }}
        >
          ×
        </button>
      )}
    </span>
  )
}

export default function ProgressionInputBar({
  sectionId,
  sectionKey,
  sectionMode,
  beatStart,
  onPlace,
  onClose,
}) {
  const [mode, setMode] = useState('numeral')
  const [tokens, setTokens] = useState([])
  const [key, setKey] = useState(normalizeRoot(sectionKey) ?? 'C')
  const [keyMode, setKeyMode] = useState(sectionMode === 'minor' ? 'minor' : 'major')
  const [activeTokenIdx, setActiveTokenIdx] = useState(null)
  const [keyAutoDetected, setKeyAutoDetected] = useState(false)

  const [draft, setDraft] = useState('')
  const [invalidIdxSet, setInvalidIdxSet] = useState(new Set())
  const [flashInvalid, setFlashInvalid] = useState(false)

  const [bothNumerals, setBothNumerals] = useState([])
  const [bothLetters, setBothLetters] = useState([])
  const [bothEditRow, setBothEditRow] = useState('numeral')

  const numeralsForMatch = useMemo(() => {
    if (mode === 'numeral') return cleanTokens(tokens)
    if (mode === 'letter') return convertLetterTokensToNumerals(cleanTokens(tokens), key, keyMode).filter(Boolean)
    return cleanTokens(bothNumerals)
  }, [bothNumerals, key, keyMode, mode, tokens])

  const translatedChords = useMemo(() => {
    if (mode === 'letter') return cleanTokens(tokens)
    if (mode === 'both') return cleanTokens(bothLetters)
    return transposeProgression(cleanTokens(tokens), null, key, keyMode)
  }, [bothLetters, key, keyMode, mode, tokens])

  const translatedNumerals = useMemo(() => {
    if (mode === 'numeral') return cleanTokens(tokens)
    if (mode === 'both') return cleanTokens(bothNumerals)
    return convertLetterTokensToNumerals(cleanTokens(tokens), key, keyMode)
  }, [bothNumerals, key, keyMode, mode, tokens])

  const match = useMemo(() => {
    const named = matchNamedProgression(numeralsForMatch)
    const vamp = matchVampPattern(numeralsForMatch)
    return named ?? vamp
  }, [numeralsForMatch])

  useEffect(() => {
    if (mode !== 'letter') return
    const detected = estimateKeyFromChordTokens(cleanTokens(tokens))
    if (!detected) {
      setKeyAutoDetected(false)
      return
    }
    setKey(detected.key)
    setKeyMode(detected.mode)
    setKeyAutoDetected(true)
  }, [mode, tokens])

  useEffect(() => {
    if (activeTokenIdx == null) return
    const base = mode === 'both'
      ? (bothEditRow === 'numeral' ? bothNumerals : bothLetters)
      : tokens
    setDraft(String(base[activeTokenIdx] ?? ''))
  }, [activeTokenIdx, bothEditRow, bothLetters, bothNumerals, mode, tokens])

  function switchMode(nextMode) {
    if (nextMode === mode) return

    if (mode === 'numeral' && nextMode === 'letter') {
      setTokens(transposeProgression(cleanTokens(tokens), null, key, keyMode))
      setInvalidIdxSet(new Set())
    } else if (mode === 'letter' && nextMode === 'numeral') {
      const src = cleanTokens(tokens)
      const converted = convertLetterTokensToNumerals(src, key, keyMode)
      const invalid = new Set()
      const merged = src.map((token, idx) => {
        if (!converted[idx]) {
          invalid.add(idx)
          return token
        }
        return converted[idx]
      })
      setTokens(merged)
      setInvalidIdxSet(invalid)
    } else if (nextMode === 'both') {
      if (mode === 'numeral') {
        const n = cleanTokens(tokens)
        setBothNumerals(n)
        setBothLetters(transposeProgression(n, null, key, keyMode))
      } else if (mode === 'letter') {
        const l = cleanTokens(tokens)
        setBothLetters(l)
        setBothNumerals(convertLetterTokensToNumeralsKeepShape(l, key, keyMode))
      }
      setBothEditRow('numeral')
      setInvalidIdxSet(new Set())
    } else if (mode === 'both' && nextMode === 'numeral') {
      setTokens(cleanTokens(bothNumerals))
      setInvalidIdxSet(new Set())
    } else if (mode === 'both' && nextMode === 'letter') {
      setTokens(cleanTokens(bothLetters))
      setInvalidIdxSet(new Set())
    }

    setMode(nextMode)
    setActiveTokenIdx(null)
  }

  function updateTokenAt(idx, value, row = 'primary') {
    if (mode === 'both') {
      if (row === 'numeral') {
        const nextN = [...bothNumerals]
        nextN[idx] = value
        setBothNumerals(nextN)
        setBothLetters(transposeNumeralTokensKeepShape(nextN, key, keyMode))
      } else {
        const nextL = [...bothLetters]
        nextL[idx] = value
        setBothLetters(nextL)
        setBothNumerals(convertLetterTokensToNumeralsKeepShape(nextL, key, keyMode))
      }
      return
    }

    const next = [...tokens]
    next[idx] = value
    setTokens(next)
  }

  function removeTokenAt(idx, row = 'primary') {
    if (mode === 'both') {
      if (row === 'numeral') {
        const nextN = bothNumerals.filter((_, i) => i !== idx)
        setBothNumerals(nextN)
        setBothLetters(transposeNumeralTokensKeepShape(nextN, key, keyMode))
      } else {
        const nextL = bothLetters.filter((_, i) => i !== idx)
        setBothLetters(nextL)
        setBothNumerals(convertLetterTokensToNumeralsKeepShape(nextL, key, keyMode))
      }
      return
    }

    setTokens(tokens.filter((_, i) => i !== idx))
  }

  function addToken(row = 'primary') {
    if (mode === 'both') {
      if (row === 'numeral') {
        setBothNumerals([...bothNumerals, ''])
        setBothLetters([...bothLetters, ''])
        setBothEditRow('numeral')
        setActiveTokenIdx(bothNumerals.length)
      } else {
        setBothLetters([...bothLetters, ''])
        setBothNumerals([...bothNumerals, ''])
        setBothEditRow('letter')
        setActiveTokenIdx(bothLetters.length)
      }
      return
    }

    setTokens([...tokens, ''])
    setActiveTokenIdx(tokens.length)
  }

  function applyDraft() {
    if (activeTokenIdx == null) return
    updateTokenAt(activeTokenIdx, draft.trim(), mode === 'both' ? bothEditRow : 'primary')
    setActiveTokenIdx(null)
  }

  function resolveNumeralsForConfirm() {
    if (mode === 'numeral') return cleanTokens(tokens)
    if (mode === 'both') return cleanTokens(bothNumerals)

    const src = cleanTokens(tokens)
    const converted = convertLetterTokensToNumerals(src, key, keyMode)
    const invalid = new Set()
    const numerals = src.map((_, idx) => {
      if (!converted[idx]) invalid.add(idx)
      return converted[idx]
    }).filter(Boolean)
    setInvalidIdxSet(invalid)
    return invalid.size ? null : numerals
  }

  function confirmPlacement() {
    const numerals = resolveNumeralsForConfirm()
    if (!numerals || !numerals.length || !key) {
      setFlashInvalid(true)
      setTimeout(() => setFlashInvalid(false), 180)
      return
    }

    const { fingerprint } = fingerprintProgression(numerals)
    const chordLabels = transposeProgression(numerals, null, key, keyMode)
    const instance = {
      id: pbId++,
      typeId: fingerprint,
      sectionId,
      beatStart,
      beatEnd: beatStart + numerals.length,
      key,
      mode: keyMode,
      chordLabels,
      keyConfidence: true,
      vampRunBars: null,
      vampBreakBeat: null,
      source: 'manual',
    }

    onPlace?.(instance)
    setTokens([])
    setBothNumerals([])
    setBothLetters([])
    setActiveTokenIdx(null)
    setInvalidIdxSet(new Set())
  }

  function onEditorKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose?.()
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      applyDraft()
      return
    }
    if (e.key === 'Tab') {
      e.preventDefault()
      applyDraft()

      const baseLen = mode === 'both'
        ? (bothEditRow === 'numeral' ? bothNumerals.length : bothLetters.length)
        : tokens.length

      const dir = e.shiftKey ? -1 : 1
      let next = (activeTokenIdx ?? 0) + dir
      if (!e.shiftKey && next >= baseLen) {
        addToken(mode === 'both' ? bothEditRow : 'primary')
        return
      }
      next = Math.max(0, Math.min(baseLen - 1, next))
      setActiveTokenIdx(next)
      return
    }
    if (e.key === 'Backspace' && !draft) {
      const base = mode === 'both'
        ? (bothEditRow === 'numeral' ? bothNumerals : bothLetters)
        : tokens
      if (base.length > 0) {
        e.preventDefault()
        removeTokenAt(base.length - 1, mode === 'both' ? bothEditRow : 'primary')
      }
    }
  }

  function onContainerKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose?.()
      return
    }
    if (e.key === 'Enter' && activeTokenIdx == null) {
      e.preventDefault()
      confirmPlacement()
    }
  }

  const letterBorrowedFlags = useMemo(() => {
    const source = mode === 'both' ? bothLetters : tokens
    return source.map((token) => {
      const res = tokenToNumeralFromChordToken(token, key, keyMode)
      return !!(res && (res.borrowed || !res.diatonic))
    })
  }, [bothLetters, key, keyMode, mode, tokens])

  const renderTokenRow = (rowMode, rowTokens, borrowedFlags = []) => (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
      {mode === 'both' && (
        <button
          type="button"
          onClick={() => setBothEditRow(rowMode)}
          style={{
            border: '1px solid rgba(196,130,42,0.25)',
            background: bothEditRow === rowMode ? 'rgba(196,130,42,0.16)' : 'transparent',
            borderRadius: 2,
            padding: '1px 5px',
            fontSize: 9,
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
            color: 'var(--ink-primary)',
          }}
        >
          {rowMode === 'numeral' ? 'ℝ' : 'A'}
        </button>
      )}
      {rowTokens.map((token, idx) => {
        const isActive = activeTokenIdx === idx && (mode !== 'both' || bothEditRow === rowMode)
        const borrowed = rowMode === 'letter' ? borrowedFlags[idx] : false
        const invalid = invalidIdxSet.has(idx) && rowMode === 'letter'
        return isActive ? (
          <input
            key={`${rowMode}-edit-${idx}`}
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={applyDraft}
            onKeyDown={onEditorKeyDown}
            style={{
              minWidth: 32,
              width: Math.max(32, draft.length * 9),
              padding: '3px 8px',
              borderRadius: 3,
              outline: 'none',
              border: `1px solid ${invalid ? 'var(--dissonant)' : 'var(--accent)'}`,
              background: 'rgba(196,130,42,0.22)',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              fontWeight: 700,
              color: 'var(--ink-primary)',
            }}
          />
        ) : (
          <Pill
            key={`${rowMode}-${token}-${idx}`}
            active={isActive}
            borrowed={borrowed}
            onClick={() => {
              if (mode === 'both') setBothEditRow(rowMode)
              setActiveTokenIdx(idx)
            }}
            onRemove={() => removeTokenAt(idx, mode === 'both' ? rowMode : 'primary')}
          >
            <span style={{ textDecoration: invalid ? 'underline' : 'none', textDecorationColor: 'var(--dissonant)' }}>
              {token || '·'}
            </span>
          </Pill>
        )
      })}
      <button
        type="button"
        onClick={() => addToken(mode === 'both' ? rowMode : 'primary')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
          padding: '3px 8px',
          borderRadius: 3,
          border: '1px dashed rgba(196,130,42,0.45)',
          background: 'rgba(196,130,42,0.08)',
          color: 'var(--ink-primary)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          fontWeight: 700,
          cursor: 'pointer',
        }}
      >
        +
      </button>
    </div>
  )

  return (
    <div
      tabIndex={0}
      onKeyDown={onContainerKeyDown}
      style={{
        marginTop: 6,
        borderLeft: '4px solid var(--accent)',
        border: '1px solid rgba(196,130,42,0.25)',
        background: 'rgba(223,201,154,0.42)',
        borderRadius: 4,
        padding: '6px 8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ display: 'inline-flex', border: '1px solid rgba(196,130,42,0.25)', borderRadius: 3 }}>
          {[
            { id: 'numeral', label: 'ℝ' },
            { id: 'letter', label: 'A' },
            { id: 'both', label: 'B' },
          ].map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => switchMode(m.id)}
              style={{
                border: 'none',
                borderRight: m.id !== 'both' ? '1px solid rgba(196,130,42,0.18)' : 'none',
                background: mode === m.id ? 'var(--accent)' : 'transparent',
                color: mode === m.id ? '#1c1610' : 'var(--ink-secondary)',
                padding: '3px 7px',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {(mode === 'numeral' || mode === 'letter') && renderTokenRow(mode, tokens, letterBorrowedFlags)}
          {mode === 'both' && renderTokenRow('numeral', bothNumerals)}
          {mode === 'both' && renderTokenRow('letter', bothLetters, letterBorrowedFlags)}
        </div>

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginLeft: 'auto' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-secondary)' }}>key:</span>
          <select value={key} onChange={(e) => { setKey(e.target.value); setKeyAutoDetected(false) }} style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            {ROOTS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={keyMode} onChange={(e) => { setKeyMode(e.target.value); setKeyAutoDetected(false) }} style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            <option value="major">major</option>
            <option value="minor">minor</option>
          </select>
          {keyAutoDetected && mode === 'letter' && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent)' }}>auto</span>
          )}

          <button
            type="button"
            onClick={confirmPlacement}
            style={{
              border: `1px solid ${flashInvalid ? 'var(--dissonant)' : 'rgba(196,130,42,0.35)'}`,
              background: flashInvalid ? 'rgba(184,72,48,0.2)' : 'rgba(196,130,42,0.12)',
              color: 'var(--ink-primary)',
              borderRadius: 3,
              padding: '2px 6px',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
            }}
          >
            ✓
          </button>
          <button
            type="button"
            onClick={onClose}
            style={{
              border: '1px solid rgba(196,130,42,0.35)',
              background: 'transparent',
              color: 'var(--ink-secondary)',
              borderRadius: 3,
              padding: '2px 6px',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {(mode === 'numeral' || mode === 'both') && (
        <div style={{ marginTop: 6, display: 'flex', gap: 10, flexWrap: 'wrap', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-primary)' }}>
          {translatedChords.map((chord, idx) => (
            <span key={`chord-preview-${idx}`}>{chord}</span>
          ))}
        </div>
      )}

      {(mode === 'letter' || mode === 'both') && (
        <div style={{ marginTop: 4, display: 'flex', gap: 10, flexWrap: 'wrap', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-secondary)' }}>
          {translatedNumerals.map((n, idx) => (
            <span key={`num-preview-${idx}`}>{n ?? '?'}</span>
          ))}
        </div>
      )}

      {match && (
        <div
          style={{
            marginTop: 6,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 9,
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            letterSpacing: '0.08em',
            color: 'var(--accent)',
            padding: '1px 6px',
            background: 'rgba(196,130,42,0.1)',
            border: '1px solid rgba(196,130,42,0.25)',
            borderRadius: 2,
          }}
        >
          <span>{String(match.id).startsWith('vamp-') ? '🔁' : '■'}</span>
          <span>{match.name}</span>
        </div>
      )}

      {activeTokenIdx != null && (mode === 'numeral' || (mode === 'both' && bothEditRow === 'numeral')) && (
        <div style={{ marginTop: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {NUMERAL_SUGGESTIONS.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => {
                setDraft(n)
                updateTokenAt(activeTokenIdx, n, mode === 'both' ? bothEditRow : 'primary')
                setActiveTokenIdx(null)
              }}
              style={{
                border: '1px solid rgba(196,130,42,0.25)',
                background: 'rgba(196,130,42,0.08)',
                borderRadius: 2,
                padding: '2px 5px',
                fontSize: 10,
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              {n}
            </button>
          ))}
        </div>
      )}

      {activeTokenIdx != null && (mode === 'letter' || (mode === 'both' && bothEditRow === 'letter')) && (
        <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <select
            defaultValue=""
            onChange={(e) => {
              const root = e.target.value
              if (!root) return
              const current = parseLabelToContext(draft)
              const quality = QUALITIES[current?.qualityIdx ?? 0]?.label ?? 'maj'
              const symbol = QUALITIES.find((q) => q.label === quality)?.symbol ?? ''
              setDraft(`${root}${symbol}`)
            }}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}
          >
            <option value="">root</option>
            {ROOTS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select
            defaultValue=""
            onChange={(e) => {
              const q = e.target.value
              if (!q) return
              const root = parseLabelToContext(draft)?.rootIdx
              const rootLabel = ROOTS[root ?? getRootIdx(key)]
              const symbol = QUALITIES.find((qq) => qq.label === q)?.symbol ?? ''
              setDraft(`${rootLabel}${symbol}`)
            }}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}
          >
            <option value="">quality</option>
            {['maj', 'min', 'dim', 'aug', 'sus2', 'sus4'].map((q) => <option key={q} value={q}>{q}</option>)}
          </select>
        </div>
      )}

      {mode === 'both' && null}
    </div>
  )
}
