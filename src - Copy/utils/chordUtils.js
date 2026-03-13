/**
 * LALO chord utilities — pure functions, no React, no state, no JSX.
 */
import { ROOTS, QUALITIES, EXTENSIONS, INVERSIONS } from '../constants/music';

export const polar = (cx, cy, r, deg) => {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
};

export const arcPath = (cx, cy, r1, r2, startDeg, endDeg, gap = 1.6) => {
  const s = startDeg + gap / 2, e = endDeg - gap / 2;
  const p1 = polar(cx, cy, r2, s), p2 = polar(cx, cy, r2, e);
  const p3 = polar(cx, cy, r1, e), p4 = polar(cx, cy, r1, s);
  const lg = e - s > 180 ? 1 : 0;
  return `M${p1.x} ${p1.y} A${r2} ${r2} 0 ${lg} 1 ${p2.x} ${p2.y} L${p3.x} ${p3.y} A${r1} ${r1} 0 ${lg} 0 ${p4.x} ${p4.y}Z`;
};

export const hexToRgba = (hex, a) => {
  if (!hex) return `rgba(26,26,26,${a})`;
  if (hex.startsWith('#')) {
    if (hex.length < 7) return `rgba(26,26,26,${a})`;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${a})`;
  }
  // Handle pre-formatted rgb/rgba strings — extract channels and re-apply the given alpha
  const m = hex.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (m) return `rgba(${m[1]},${m[2]},${m[3]},${a})`;
  return `rgba(26,26,26,${a})`;
};

export const getChordAccent = (label) => {
  if (!label) return '#5a3e1a';
  const QUALITY_ACCENTS = {
    'm': '#3a6ea8', '°': '#b54040', '°7': '#8b2020', 'ø': '#c05050',
    '+': '#c07030', 'sus2': '#3a8a5a', 'sus4': '#2a7a7a', '5': '#7a7a7a',
  };
  const ordered = ['°7', 'ø', 'sus2', 'sus4', 'm', '+', '°', '5'];
  for (const sym of ordered)
    if (label.includes(sym)) return QUALITY_ACCENTS[sym] ?? '#5a3e1a';
  return '#5a3e1a';
};

export function buildChordLabel(rootIdx, qualityIdx, extensionIdx, inversionIdx) {
  const root = ROOTS[rootIdx ?? 0];
  const q    = QUALITIES[qualityIdx ?? 0];
  const ext  = EXTENSIONS[extensionIdx ?? 0];
  const inv  = INVERSIONS[inversionIdx ?? 0];

  // Qualities that are fully self-contained — ignore extensions
  const noExt  = q.label === '°7' || q.label === '5';
  // Qualities where maj7 doesn't make sense
  const noMaj7 = ['dim', '°7', 'ø', '5'].includes(q.label);
  // 3rd inversion requires a 7th in the chord
  const has7th = ['7', 'maj7', '9', '11', '13'].includes(ext.label);
  const invSym = (inv.label === '3rd' && !has7th) ? '' : inv.symbol;

  let extSym = noExt ? '' : ext.symbol;
  if (noMaj7 && ext.label === 'maj7') extSym = '7'; // degrade gracefully

  // Special case: ø always shows as ø7 (the 7th is intrinsic)
  if (q.label === 'ø') extSym = ext.label === '—' ? '7' : ext.symbol;

  return `${root}${q.symbol}${extSym}${invSym}`;
}

export function parseLabelToContext(label) {
  if (!label) return null;
  // Find root (longest match first — C♯ before C)
  const rootsSorted = [...ROOTS].sort((a, b) => b.length - a.length);
  let rootIdx = null, rest = label;
  for (const r of rootsSorted) {
    if (label.startsWith(r)) { rootIdx = ROOTS.indexOf(r); rest = label.slice(r.length); break; }
  }
  if (rootIdx === null) return null;

  const qualsSorted = [...QUALITIES].sort((a, b) => b.symbol.length - a.symbol.length);
  let qualityIdx = 0;
  for (const q of qualsSorted) {
    if (q.symbol && rest.startsWith(q.symbol)) { qualityIdx = QUALITIES.indexOf(q); break; }
  }

  const extsSorted = [...EXTENSIONS].sort((a, b) => b.symbol.length - a.symbol.length);
  let extensionIdx = 0;
  const afterQ = rest.slice(QUALITIES[qualityIdx].symbol.length);
  for (const e of extsSorted) {
    if (e.symbol && afterQ.startsWith(e.symbol)) { extensionIdx = EXTENSIONS.indexOf(e); break; }
  }

  return { rootIdx, qualityIdx, extensionIdx };
}

export function suggestedLabel(rootIdx, sugQ, sugExt) {
  if (rootIdx === null) return null;
  const q   = QUALITIES[sugQ ?? 0];
  const ext = EXTENSIONS[sugExt ?? 0];
  return `${ROOTS[rootIdx]}${q.symbol}${ext.symbol}`;
}
