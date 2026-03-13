import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { BEAT_W, BEAT_GAP, ROW_H } from '../../utils/harmonyEngine'
import { getChordAccent, hexToRgba } from '../../utils/chordUtils'
import { compressHarmonyEvents, deriveProgressions, rebaseEvents } from '../../utils/progressionView'

const CHIP_H = Math.round(ROW_H * 0.7)

function InfoBadge({ children, tone = 'neutral' }) {
  const styles = tone === 'accent'
    ? {
        color: 'rgba(188,135,58,0.95)',
        border: '1px solid rgba(188,135,58,0.45)',
        background: 'rgba(188,135,58,0.1)',
      }
    : tone === 'variant'
      ? {
          color: 'rgba(176,120,32,0.95)',
          border: '1px solid rgba(176,120,32,0.45)',
          background: 'rgba(176,120,32,0.08)',
        }
      : {
          color: 'rgba(60,35,10,0.72)',
          border: '1px solid rgba(100,65,25,0.2)',
          background: 'rgba(100,65,25,0.06)',
        }

  return (
    <span style={{
      fontSize: 9,
      fontFamily: "'DM Mono', monospace",
      borderRadius: 999,
      padding: '2px 6px',
      letterSpacing: '0.04em',
      ...styles,
    }}>
      {children}
    </span>
  )
}

function ProgChordChip({ ev, instanceEv, onContextMenu, disabled, titleStr: propTitle }) {
  const accent = getChordAccent(ev.label)
  const [hov, setHov] = useState(false)
  const spanRaw = Number(ev.durationBeats ?? ev.span ?? 1)
  const span = Number.isFinite(spanRaw) ? Math.max(1, Math.round(spanRaw)) : 1
  const width = span * BEAT_W + Math.max(0, span - 1) * BEAT_GAP
  const titleStr = ev._computedTitle ?? propTitle ?? `${ev.label}${span > 1 ? ` (${Number(span)} beats)` : ''}`
  // debug
  // console.debug('ProgChordChip titleStr (final) =', titleStr)
  return (
    <div
      onContextMenu={e => !disabled && onContextMenu(e, instanceEv)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        position: 'relative',
        width,
        height: CHIP_H,
        borderRadius: 5,
        border: `2px solid ${hexToRgba(accent, hov ? 0.95 : 0.7)}`,
        background: hov
          ? hexToRgba(accent, 0.28)
          : `linear-gradient(160deg,${hexToRgba(accent,0.22)} 0%,${hexToRgba(accent,0.14)} 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 10,
        fontFamily: "'DM Mono',monospace",
        fontWeight: 700,
        color: accent,
        cursor: disabled ? 'default' : 'context-menu',
        opacity: disabled ? 0.35 : 1,
        transition: 'border 0.12s, background 0.12s, opacity 0.12s',
        marginRight: BEAT_GAP,
        userSelect: 'none',
      }}
      title={titleStr}
    >
      {ev.label}
    </div>
  )
}

function ProgAddTarget({ sectionId, beat, onAddChord, disabled }) {
  const [hov, setHov] = useState(false)
  return (
    <div
      onContextMenu={e => !disabled && onAddChord(e, sectionId, beat)}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        width: BEAT_W,
        height: CHIP_H,
        borderRadius: 4,
        border: `1px dashed rgba(100,65,25,0.3)`,
        background: hov ? 'rgba(100,65,25,0.08)' : 'transparent',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'rgba(100,65,25,0.55)',
        fontSize: 14,
        fontWeight: 500,
        cursor: disabled ? 'default' : 'context-menu',
        opacity: disabled ? 0.35 : 1,
        userSelect: 'none',
        marginRight: BEAT_GAP,
        transition: 'background 0.1s, opacity 0.1s',
      }}
    >
      {hov && '+'}
    </div>
  )
}

function DotRow({ occurrences, selectedIdx, onSelect, isVariant, disabled }) {
  const color = isVariant ? 'rgba(176,120,32,0.9)' : 'rgba(60,35,10,0.85)'
  const dotsToShow = occurrences.slice(0, 16)
  const overflow = occurrences.length - dotsToShow.length
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8, flexWrap: 'wrap' }}>
      {dotsToShow.map((barIdx, i) => {
        const active = i === selectedIdx
        return (
          <button
            key={`${barIdx}-${i}`}
            title={`Instance ${i + 1} (bar ${barIdx + 1})`}
            onClick={() => !disabled && onSelect(i)}
            style={{
              width: 8, height: 8, borderRadius: '50%',
              border: `1px solid ${color}`,
              background: active ? color : 'transparent',
              padding: 0,
              cursor: disabled ? 'default' : 'pointer',
              opacity: disabled ? 0.4 : 1,
            }}
          />
        )
      })}
      {overflow > 0 && (
        <span style={{ fontSize: 9, color: color, opacity: disabled ? 0.4 : 0.8 }}>
          +{overflow}
        </span>
      )}
    </div>
  )
}

function formatBars(occurrences) {
  if (!occurrences?.length) return 'bar ?'
  return occurrences.map(barIdx => barIdx + 1).join(', ')
}

function patternContainsBeat(pattern, beat, timeSig) {
  const spanBars = Math.max(1, pattern.spanBars ?? 1)
  return pattern.occurrences.some(barIdx => {
    const startBeat = barIdx * timeSig
    const endBeat = startBeat + spanBars * timeSig
    return beat >= startBeat && beat < endBeat
  })
}

function ApplyToAllPrompt({ patternName, count, selectedBar, onApplyAll, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 8000)
    return () => clearTimeout(t)
  }, [onDismiss])

  return (
    <div style={{
      marginTop: 8,
      padding: '8px 10px',
      borderRadius: 6,
      border: '1px solid rgba(188,135,58,0.45)',
      background: 'rgba(188,135,58,0.08)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      fontFamily: "'DM Mono', monospace",
      fontSize: 10,
      color: 'rgba(60,35,10,0.9)',
    }}>
      <span>Changed {patternName} at bar {selectedBar}. Apply that edit to all {count} matching instances?</span>
      <div style={{ display: 'flex', gap: 6 }}>
        <button onClick={onApplyAll} style={{
          padding: '6px 10px',
          border: 'none',
          borderRadius: 5,
          background: 'rgba(188,135,58,0.9)',
          color: '#120d07',
          fontWeight: 700,
          letterSpacing: '0.04em',
          cursor: 'pointer',
        }}>APPLY ALL</button>
        <button onClick={onDismiss} style={{
          padding: '6px 10px',
          border: '1px solid rgba(188,135,58,0.45)',
          borderRadius: 5,
          background: 'transparent',
          color: 'rgba(100,65,25,0.85)',
          cursor: 'pointer',
        }}>THIS ONLY</button>
      </div>
    </div>
  )
}

function PatternRow({
  pattern,
  section,
  selectedIdx,
  onSelectInstance,
  onEditChord,
  onAddChord,
  pendingEdit,
  onApplyAll,
  sectionEditMode,
  patternIndex,
}) {
  
  const activeOccurrence = pattern.occurrences[selectedIdx] ?? pattern.occurrences[0] ?? 0
  const activeInstance = pattern.instances?.[selectedIdx] ?? null
  const badge = patternIndex === 0 ? '①' : patternIndex === 1 ? '②' : patternIndex === 2 ? '③' : `${patternIndex + 1}`
  const timeSigLocal = section?.timeSig ?? 4
  const rebased = useMemo(
    () => rebaseEvents(pattern, selectedIdx, timeSigLocal),
    [pattern, selectedIdx, timeSigLocal]
  )
  const displayEvents = useMemo(
    () => compressHarmonyEvents(rebased),
    [rebased]
  )

  

  const handleContext = (e, instanceEv) => {
    onEditChord(e, section.id, instanceEv)
  }

  const beatOffset = (pattern.occurrences[selectedIdx] ?? 0) * section.timeSig
  const patternTotalBeats = Math.max(
    section.timeSig * Math.max(1, pattern.spanBars ?? 1),
    ...displayEvents.map(ev => (ev.beat ?? 0) + (ev.durationBeats ?? ev.span ?? 1))
  )
  const nextBeat = beatOffset + Math.min(
    patternTotalBeats - 1,
    Math.max(0, ...displayEvents.map(ev => (ev.beat ?? 0) + (ev.durationBeats ?? ev.span ?? 1)))
  )

  // Compute a robust title for each display event in case duration/span fields are missing or malformed.
  const computedDisplayEvents = displayEvents.map((ev, idx, arr) => {
    const spanRaw = ev.durationBeats ?? ev.span
    let span = Number.isFinite(spanRaw) ? Math.max(1, Math.round(spanRaw)) : null
    if (!span || span < 1) {
      const next = arr[idx + 1]
      const nextBeat = next ? (next.beat ?? 0) : patternTotalBeats
      span = Math.max(1, Math.round((nextBeat ?? (ev.beat + 1)) - (ev.beat ?? 0)))
    }
    return { ...ev, _computedTitle: `${ev.label}${span > 1 ? ` (${span} beats)` : ''}` }
  })

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      padding: '8px 10px',
      borderRadius: 8,
      border: selectedIdx > 0 || pendingEdit?.patternId === pattern.id
        ? '1px solid rgba(188,135,58,0.28)'
        : '1px solid rgba(100,65,25,0.12)',
      background: pendingEdit?.patternId === pattern.id
        ? 'rgba(188,135,58,0.08)'
        : 'rgba(255,255,255,0.03)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{
          fontSize: 10, fontWeight: 700, color: 'rgba(60,35,10,0.9)',
          background: 'rgba(100,65,25,0.1)', border: '1px solid rgba(100,65,25,0.25)',
          borderRadius: 5, padding: '2px 6px', minWidth: 20, textAlign: 'center',
          fontFamily: "'DM Mono', monospace",
        }}>{badge}</span>
        {pattern.name && (
          <span style={{ fontSize: 10, color: 'rgba(60,35,10,0.75)', fontFamily: "'DM Mono', monospace" }}>
            {pattern.name}
          </span>
        )}
        <InfoBadge>{pattern.occurrences.length}x</InfoBadge>
        <InfoBadge tone="accent">bar {activeOccurrence + 1}</InfoBadge>
        {(pattern.spanBars ?? 1) > 1 && <InfoBadge>{pattern.spanBars} bars</InfoBadge>}
        {(pattern.analysis?.variantOccurrenceCount ?? 0) > 0 && (
          <InfoBadge tone="variant">{pattern.analysis.variantOccurrenceCount} slight variation{pattern.analysis.variantOccurrenceCount === 1 ? '' : 's'}</InfoBadge>
        )}
        {pattern.isVariant && (
          <InfoBadge tone="variant">1-chord variant</InfoBadge>
        )}
        {pattern.analysis?.canonical && <InfoBadge>{pattern.analysis.canonical}</InfoBadge>}
        {pattern.analysis?.cadence && <InfoBadge>{pattern.analysis.cadence} cadence</InfoBadge>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 9, color: 'rgba(60,35,10,0.62)', fontFamily: "'DM Mono', monospace" }}>
          Bars: {formatBars(pattern.occurrences)}
        </span>
        <span style={{ fontSize: 9, color: 'rgba(60,35,10,0.52)', fontFamily: "'DM Mono', monospace" }}>
          Dots switch instances. Right-click a chord to edit. Right-click + to add.
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {computedDisplayEvents.map((ev, idx) => (
            <ProgChordChip
              key={ev.id ?? idx}
              ev={ev}
              instanceEv={ev}
              onContextMenu={handleContext}
              disabled={sectionEditMode}
              titleStr={ev._computedTitle}
            />
          ))}
          <ProgAddTarget
            sectionId={section.id}
            beat={nextBeat}
            onAddChord={onAddChord}
            disabled={sectionEditMode}
          />
        </div>
        <DotRow
          occurrences={pattern.occurrences}
          selectedIdx={selectedIdx}
          onSelect={onSelectInstance}
          isVariant={pattern.isVariant}
          disabled={sectionEditMode}
        />
      </div>

      {pendingEdit && pendingEdit.patternId === pattern.id && pattern.occurrences.length > 1 && (
        <ApplyToAllPrompt
          patternName={pattern.name ?? `Pattern ${patternIndex + 1}`}
          count={pattern.occurrences.length}
          selectedBar={activeOccurrence + 1}
          onApplyAll={() => onApplyAll(pattern, pendingEdit.editedEv)}
          onDismiss={() => onApplyAll(null, null)}
        />
      )}
    </div>
  )
}

export default function ProgressionView({
  section,
  onEditChord,
  onAddChord,
  onApplyAll,
  sectionEditMode,
}) {
  const patterns = useMemo(
    () => section.progressions ?? deriveProgressions(section),
    [section]
  )
  const [selectedInstance, setSelectedInstance] = useState({})
  const [pendingEdit, setPendingEdit] = useState(null)
  const prevEventsRef = useRef(section.events)
  const lastClickedEvRef = useRef(null)

  useEffect(() => {
    if (!lastClickedEvRef.current) {
      prevEventsRef.current = section.events
      return
    }
    const prev = prevEventsRef.current
    const curr = section.events
    const changedEv = curr.find(ev => {
      const old = prev.find(p => p.id === ev.id)
      return old && old.label !== ev.label
    })
    if (changedEv) {
      const pat = patterns.find(p => patternContainsBeat(p, changedEv.beat, section.timeSig))
      if (pat && pat.occurrences.length > 1) {
        setPendingEdit({ patternId: pat.id, editedEv: changedEv })
      }
      lastClickedEvRef.current = null
    }
    prevEventsRef.current = curr
  }, [section.events, patterns, section.timeSig])

  const handleSelect = useCallback((patternId, idx) => {
    setSelectedInstance(prev => ({ ...prev, [patternId]: idx }))
  }, [])

  const handleContextMenu = (e, instanceEv) => {
    lastClickedEvRef.current = instanceEv
    onEditChord(e, section.id, instanceEv)
  }

  const handleApplyAll = (pattern, editedEv) => {
    if (pattern && editedEv) {
      onApplyAll(section.id, pattern, editedEv)
    }
    setPendingEdit(null)
  }

  const dominantCount = patterns.filter(pattern => !pattern.isVariant).length

  if (!patterns.length) {
    return (
      <div style={{
        height: ROW_H,
        display: 'flex',
        alignItems: 'center',
        color: 'rgba(100,65,25,0.45)',
        fontSize: 10,
        fontFamily: "'DM Mono', monospace",
      }}>
        No patterns detected.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
        flexWrap: 'wrap',
        padding: '0 2px 2px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <InfoBadge tone="accent">{patterns.length} pattern{patterns.length === 1 ? '' : 's'}</InfoBadge>
          <InfoBadge>{dominantCount} core phrase{dominantCount === 1 ? '' : 's'}</InfoBadge>
          {pendingEdit && <InfoBadge tone="variant">Apply-all pending</InfoBadge>}
        </div>
        <div style={{ fontSize: 9, color: 'rgba(60,35,10,0.55)', fontFamily: "'DM Mono', monospace" }}>
          Edit one bar, then decide whether the change should stay local or propagate.
        </div>
      </div>
      {patterns.map((p, idx) => (
        <PatternRow
          key={p.id}
          pattern={p}
          section={section}
          selectedIdx={selectedInstance[p.id] ?? 0}
          onSelectInstance={(i) => handleSelect(p.id, i)}
          onEditChord={handleContextMenu}
          onAddChord={onAddChord}
          pendingEdit={pendingEdit}
          onApplyAll={handleApplyAll}
          sectionEditMode={sectionEditMode}
          patternIndex={idx}
        />
      ))}
    </div>
  )
}
