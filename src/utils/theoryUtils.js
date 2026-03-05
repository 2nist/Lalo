import { ROOTS, QUALITIES, EXTENSIONS } from '../constants/music';
import { transposeProgression } from '../core/index.js';
import { parseLabelToContext } from './chordUtils';

export function numeralToChordLabel(token, sectionKey = 'C', sectionMode = 'major') {
  const raw = String(token ?? '').trim()
    .replace(/♭/g, 'b')
    .replace(/♯/g, '#');
  if (!raw) return null;
  return transposeProgression([raw], null, sectionKey, sectionMode)?.[0] ?? null;
}

export function buildTheoryEventsForSection(section, payload, options = {}) {
  if (!section || !payload || payload.kind !== 'theory-progression') return [];

  const createEventId = typeof options.createEventId === 'function'
    ? options.createEventId
    : (() => `${section.id}-theory-${Math.random().toString(36).slice(2, 9)}`);

  const labels = (payload.tokens ?? [])
    .map(token => numeralToChordLabel(token, section.key, section.mode))
    .filter(Boolean);

  if (!labels.length) return [];

  const step = Math.max(1, Math.floor(section.totalBeats / labels.length));

  return labels.map((label, idx) => {
    const beat = Math.min(section.totalBeats - 1, idx * step);
    const rawSpan = idx === labels.length - 1
      ? section.totalBeats - beat
      : step;
    const span = Math.max(1, rawSpan);
    const parsed = parseLabelToContext(label);

    return {
      id: createEventId(),
      sectionId: options.sectionId ?? section.id,
      beat,
      beatFloat: beat,
      span,
      durationBeats: span,
      label,
      root: parsed ? ROOTS[parsed.rootIdx] : 'C',
      quality: parsed ? (QUALITIES[parsed.qualityIdx]?.label ?? 'maj') : 'maj',
      extensions: parsed && parsed.extensionIdx > 0
        ? [EXTENSIONS[parsed.extensionIdx]?.symbol ?? '']
        : [],
      inversion: 0,
      bassNote: undefined,
      source: options.source ?? 'theory',
    };
  }).filter(ev => ev.beat < section.totalBeats);
}
